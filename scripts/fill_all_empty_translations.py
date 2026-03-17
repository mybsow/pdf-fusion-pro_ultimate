#!/usr/bin/env python3
"""
Remplit automatiquement les msgstr vides dans tous les fichiers .po
via Google Translate (deep-translator, gratuit, sans clé API).

Usage:
    python fill_translations_google.py --lang en
    python fill_translations_google.py --all
    python fill_translations_google.py --lang en --dry-run
"""

import re
import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# ============================================================================
# CONFIG
# ============================================================================

TRANSLATIONS_DIR = Path("translations")

LANG_NAMES = {
    "en": "English",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ar": "Arabic",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ru": "Russian",
}

# Codes Google Translate (parfois différents des codes Babel)
GOOGLE_LANG_CODES = {
    "en": "en",
    "es": "es",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "nl": "nl",
    "ar": "ar",
    "zh": "zh-CN",
    "ja": "ja",
    "ru": "ru",
}

# Taille des lots — Google Translate accepte jusqu'à ~5000 chars par requête
# On envoie plusieurs chaînes séparées par un séparateur rare
BATCH_SIZE = 30

# Séparateur improbable dans les vraies chaînes
SEP = " |||SEP||| "

# Pause entre les lots (évite le rate limiting de Google)
PAUSE_BETWEEN_BATCHES = 1.0   # secondes
PAUSE_ON_ERROR = 5.0

# ============================================================================
# LECTURE / ÉCRITURE .po
# ============================================================================

def parse_po_file(po_path: Path):
    """Retourne (content_str, liste_de_blocs)."""
    content = po_path.read_text(encoding="utf-8")
    blocks = []

    pattern = re.compile(
        r'(msgid\s+"((?:[^"\\]|\\.)*)"\n)'
        r'(msgstr\s+"((?:[^"\\]|\\.)*)")',
        re.MULTILINE
    )

    for m in pattern.finditer(content):
        msgid  = m.group(2)
        msgstr = m.group(4)

        if msgid == "":   # header
            continue

        blocks.append({
            "msgid":  msgid,
            "msgstr": msgstr,
            "empty":  msgstr.strip() == "",
        })

    return content, blocks


def write_translations(po_path: Path, content: str, updates: dict) -> str:
    """Remplace les msgstr vides par les traductions."""

    def replacer(m):
        msgid  = m.group(2)
        msgstr = m.group(4)
        if msgstr.strip() == "" and msgid in updates:
            new_trans = updates[msgid].replace("\\", "\\\\").replace('"', '\\"')
            return m.group(0).replace('msgstr ""', f'msgstr "{new_trans}"', 1)
        return m.group(0)

    pattern = re.compile(
        r'(msgid\s+"((?:[^"\\]|\\.)*)"\n)'
        r'(msgstr\s+"((?:[^"\\]|\\.)*)")',
        re.MULTILINE
    )
    new_content = pattern.sub(replacer, content)
    po_path.write_text(new_content, encoding="utf-8")
    return new_content


# ============================================================================
# TRADUCTION VIA GOOGLE TRANSLATE
# ============================================================================

def unescape_msgid(s: str) -> str:
    """Convertit les séquences d'échappement .po en texte réel."""
    return s.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")


def escape_for_po(s: str) -> str:
    """Échappe le texte pour l'écriture dans un .po."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def protect_placeholders(text: str):
    """
    Remplace les placeholders Python %(name)s par des tokens neutres
    pour éviter que Google Translate ne les casse.
    Retourne (texte_protégé, mapping_token→placeholder)
    """
    mapping = {}
    counter = [0]

    def replace_ph(m):
        token = f"XPLACEHOLDERX{counter[0]}X"
        mapping[token] = m.group(0)
        counter[0] += 1
        return token

    # %(name)s  %(name)d  %s  %d
    protected = re.sub(r'%\([^)]+\)[sd]|%[sd]', replace_ph, text)
    return protected, mapping


def restore_placeholders(text: str, mapping: dict) -> str:
    """Restaure les placeholders originaux."""
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


def translate_batch(translator, msgids: list) -> dict:
    """
    Traduit un lot de chaînes en une seule requête Google.
    Retourne {msgid_original: traduction}.
    """
    # Préparer les textes (déséchapper, protéger placeholders)
    real_texts = []
    ph_maps = []
    for msgid in msgids:
        real = unescape_msgid(msgid)
        protected, ph_map = protect_placeholders(real)
        real_texts.append(protected)
        ph_maps.append(ph_map)

    # Joindre avec séparateur rare
    combined = SEP.join(real_texts)

    try:
        translated_combined = translator.translate(combined)
    except Exception as e:
        return {"_error": str(e)}

    if not translated_combined:
        return {}

    # Séparer les traductions
    # Google peut légèrement modifier le séparateur (espaces, casse)
    # On essaie plusieurs variantes
    parts = None
    for sep_variant in [SEP, " |||SEP||| ", "|||SEP|||", " ||| SEP ||| "]:
        split = translated_combined.split(sep_variant)
        if len(split) == len(msgids):
            parts = split
            break

    if parts is None:
        # Fallback : traduction chaîne par chaîne
        parts = []
        for text in real_texts:
            try:
                t = translator.translate(text) or text
                parts.append(t)
                time.sleep(0.2)
            except Exception:
                parts.append(text)

    result = {}
    for i, (msgid, translation) in enumerate(zip(msgids, parts)):
        # Restaurer placeholders
        translation = restore_placeholders(translation.strip(), ph_maps[i])
        result[msgid] = translation

    return result


# ============================================================================
# TRAITEMENT D'UN FICHIER .po
# ============================================================================

def fill_po_file(po_path: Path, target_lang: str, dry_run=False) -> int:
    lang_name   = LANG_NAMES.get(target_lang, target_lang)
    google_code = GOOGLE_LANG_CODES.get(target_lang, target_lang)

    print(f"\n{'='*60}")
    print(f"  Langue : {lang_name} ({target_lang})")
    print(f"  Fichier: {po_path}")

    content, blocks = parse_po_file(po_path)
    empty_blocks = [b for b in blocks if b["empty"]]
    total_empty  = len(empty_blocks)

    if total_empty == 0:
        print(f"  ✅ Déjà complet — aucune chaîne vide")
        return 0

    print(f"  📊 {total_empty} chaînes vides à traduire")

    if dry_run:
        print(f"  🔍 Mode dry-run — aucune modification")
        for b in empty_blocks[:5]:
            print(f"    → \"{b['msgid'][:70]}\"")
        if total_empty > 5:
            print(f"    ... et {total_empty - 5} autres")
        return total_empty

    # Créer le traducteur
    try:
        translator = GoogleTranslator(source="fr", target=google_code)
    except Exception as e:
        print(f"  ❌ Impossible de créer le traducteur: {e}")
        return 0

    all_translations = {}
    msgids = [b["msgid"] for b in empty_blocks]
    total_batches = (len(msgids) + BATCH_SIZE - 1) // BATCH_SIZE
    errors = 0

    for i in range(0, len(msgids), BATCH_SIZE):
        batch      = msgids[i:i + BATCH_SIZE]
        batch_num  = i // BATCH_SIZE + 1

        print(f"  🔄 Lot {batch_num}/{total_batches} ({len(batch)} chaînes)...", end="", flush=True)

        result = translate_batch(translator, batch)

        if "_error" in result:
            print(f" ⚠️  Erreur: {result['_error']}")
            errors += 1
            if errors >= 3:
                print(f"  ❌ Trop d'erreurs consécutives, arrêt")
                break
            time.sleep(PAUSE_ON_ERROR)
            continue

        errors = 0  # reset si succès
        all_translations.update(result)
        ok = len([v for v in result.values() if v])
        print(f" ✓ {ok}/{len(batch)} traduits")

        if i + BATCH_SIZE < len(msgids):
            time.sleep(PAUSE_BETWEEN_BATCHES)

    if not all_translations:
        print(f"  ❌ Aucune traduction obtenue")
        return 0

    # Écriture dans le fichier
    write_translations(po_path, content, all_translations)

    filled  = len(all_translations)
    missing = total_empty - filled
    print(f"  ✅ {filled}/{total_empty} traductions écrites")
    if missing > 0:
        print(f"  ⚠️  {missing} chaînes non traduites")

    return filled


# ============================================================================
# COMPILATION .po → .mo
# ============================================================================

def compile_po(lang: str):
    result = subprocess.run(
        ["pybabel", "compile", "-d", "translations", "-l", lang],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  ✅ .mo compilé pour {lang}")
    else:
        print(f"  ⚠️  Erreur compilation {lang}: {result.stderr[:200]}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Remplit les traductions vides via Google Translate (gratuit)"
    )
    parser.add_argument("--lang", "-l", help="Code langue (ex: en, es, de...)")
    parser.add_argument("--all",  "-a", action="store_true", help="Toutes les langues")
    parser.add_argument("--dry-run", action="store_true", help="Afficher sans modifier")
    parser.add_argument("--no-compile", action="store_true", help="Ne pas compiler les .mo")
    args = parser.parse_args()

    if not args.lang and not args.all:
        parser.print_help()
        sys.exit(1)

    if not HAS_TRANSLATOR:
        print("❌ Module 'deep-translator' non installé")
        print("   pip install deep-translator")
        sys.exit(1)

    langs = list(LANG_NAMES.keys()) if args.all else [args.lang]

    # Vérifier que les langues demandées existent
    for lang in langs:
        po_path = TRANSLATIONS_DIR / lang / "LC_MESSAGES" / "messages.po"
        if not po_path.exists():
            print(f"⚠️  Fichier introuvable: {po_path}")
            langs = [l for l in langs if l != lang]

    if not langs:
        print("❌ Aucune langue valide trouvée")
        sys.exit(1)

    print(f"🌍 Langues à traiter: {', '.join(langs)}")
    if args.dry_run:
        print("🔍 Mode dry-run activé\n")

    total_filled = 0

    for lang in langs:
        po_path = TRANSLATIONS_DIR / lang / "LC_MESSAGES" / "messages.po"
        filled  = fill_po_file(po_path, lang, dry_run=args.dry_run)
        total_filled += filled

        if filled > 0 and not args.dry_run and not args.no_compile:
            compile_po(lang)

        # Pause entre les langues pour éviter le rate limiting
        if not args.dry_run and lang != langs[-1]:
            print(f"  ⏳ Pause 3s avant la langue suivante...")
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"🎉 Total : {total_filled} traductions ajoutées")
    if not args.dry_run and total_filled > 0:
        print("   Les fichiers .mo ont été recompilés automatiquement")
        print("\n   Pour vérifier le résultat:")
        print("   python3 -c \"import gettext; t=gettext.translation('messages','translations',languages=['en']); print(t.gettext('Word vers PDF'))\"")


if __name__ == "__main__":
    main()