#!/bin/bash

echo "========================================="
echo "VÉRIFICATION FINALE"
echo "========================================="
echo ""

# Vérifier qu'il n'y a plus de textes avec deux-points dans les clés
echo "1. Vérification des templates (textes avec deux-points dans _()):"
remaining=$(grep -rh "{{ _('[^']* :') }}" --include="*.html" . | wc -l)
if [ $remaining -eq 0 ]; then
    echo "   ✅ Aucun texte problématique trouvé !"
else
    echo "   ⚠️  $remaining textes problématiques restants:"
    grep -rh "{{ _('[^']* :') }}" --include="*.html" . | head -10
fi

echo ""
echo "2. Vérification des fichiers .po (deux-points dans msgid):"
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    count=$(grep -c "^msgid \".*:\"$" "$po_file")
    if [ $count -gt 0 ]; then
        echo "   $lang: $count entrées avec deux-points"
    fi
done

echo ""
echo "3. Test des traductions pour les langues principales:"
python3 << 'EOF'
import gettext

# Tester les textes clés
test_cases = [
    ("Format PDF", "PDF Format", "Formato PDF"),
    ("Extraction intelligente", "Intelligent Extraction", "Extracción inteligente"),
    ("Session cookie", "Session cookie", "Cookie de sesión"),
]

print("\nTest des traductions:")
for fr_text, en_expected, es_expected in test_cases:
    print(f"\nTexte source: '{fr_text}'")
    
    # Français
    trans_fr = gettext.translation('messages', './translations', languages=['fr'], fallback=True)
    _fr = trans_fr.gettext
    result_fr = _fr(fr_text)
    print(f"  🇫🇷 FR: '{result_fr}'")
    
    # Anglais
    trans_en = gettext.translation('messages', './translations', languages=['en'], fallback=True)
    _en = trans_en.gettext
    result_en = _en(fr_text)
    print(f"  🇬🇧 EN: '{result_en}'")
    
    # Espagnol
    trans_es = gettext.translation('messages', './translations', languages=['es'], fallback=True)
    _es = trans_es.gettext
    result_es = _es(fr_text)
    print(f"  🇪🇸 ES: '{result_es}'")
