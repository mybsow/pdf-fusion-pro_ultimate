import os
import polib
import re
from deep_translator import GoogleTranslator

LANG_MAP = {
    "fr": "fr",
    "en": "en",
    "es": "es",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "nl": "nl",
    "ru": "ru",
    "ar": "ar",
    "ja": "ja",
    "zh": "zh-CN",
}

def is_same_text(a, b):
    return (a or "").strip().lower() == (b or "").strip().lower()

def should_skip(text):
    text = text.strip()

    if not text:
        return True

    if len(text) <= 2:
        return True

    if text in [":", ".", "-", "|"]:
        return True

    if "%(" in text:  # variables Flask
        return True

    if "<" in text and ">" in text:  # HTML
        return True

    if "lorem ipsum" in text.lower():
        return True

    return False


PLACEHOLDER_PATTERN = re.compile(r"%\([^)]+\)[sd]")

def protect_placeholders(text):
    """Remplace %(xxx)s par tokens temporaires"""
    placeholders = PLACEHOLDER_PATTERN.findall(text)
    mapping = {}

    for i, ph in enumerate(placeholders):
        token = f"__VAR_{i}__"
        text = text.replace(ph, token)
        mapping[token] = ph

    return text, mapping


def restore_placeholders(text, mapping):
    """Remet les placeholders d'origine"""
    for token, ph in mapping.items():
        text = text.replace(token, ph)
    return text


def translate_text(text, target_lang):
    try:
        if not text.strip():
            return text

        # 🔒 protéger variables
        protected_text, mapping = protect_placeholders(text)

        translated = GoogleTranslator(
            source="fr",
            target=target_lang
        ).translate(protected_text)

        # 🔁 fallback via anglais
        if not translated or translated.strip() == protected_text.strip():
            print(f"⚠️ Fallback EN [{target_lang}] : {text}")

            en_text = GoogleTranslator(source="fr", target="en").translate(protected_text)
            translated = GoogleTranslator(source="en", target=target_lang).translate(en_text)

        # 🔒 restaurer variables
        translated = restore_placeholders(translated, mapping)

        return translated

    except Exception as e:
        print(f"❌ Erreur [{target_lang}] : {text} -> {e}")
        return text


def process_po_file(po_path, target_lang):
    print(f"📄 Traitement: {po_path}")

    po = polib.pofile(po_path)
    updated = 0

    for entry in po:
        text = (entry.msgid or "").strip()

        if not text:
            continue

        if should_skip(text):
            continue

        current = (entry.msgstr or "").strip()

        needs_translation = (
            not current
            or is_same_text(current, text)
            or looks_french(current)
        )

        if not needs_translation:
            continue

        translated = translate_text(text, target_lang)

        if translated and not is_same_text(translated, text):
            entry.msgstr = translated
            updated += 1

    po.save()
    print(f"✅ {updated} traductions ajoutées\n")


def process_directory(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".po"):
                po_path = os.path.join(root, file)

                parts = po_path.split(os.sep)
                if len(parts) < 3:
                    continue

                lang = parts[-3]

                if lang in LANG_MAP:
                    process_po_file(po_path, LANG_MAP[lang])
                else:
                    print(f"⚠️ Langue ignorée: {lang}")

def looks_french(text):
    french_markers = [
        " le ", " la ", " les ", " des ", " du ",
        " une ", " un ", " et ", " ou ",
        " avec ", " pour ", " vos ", " votre ",
        " fichier", " fichiers", " convert", " outil"
    ]

    t = " " + text.lower() + " "

    return any(word in t for word in french_markers)

def is_probably_french(text):
    return looks_french(text) and not any(ord(c) > 127 for c in text)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python translate_po.py translations")
        sys.exit(1)

    process_directory(sys.argv[1])
    print("🎯 Traduction terminée.")