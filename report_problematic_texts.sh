#!/bin/bash

echo "========================================="
echo "RAPPORT DES TEXTES PROBLÉMATIQUES"
echo "========================================="
echo ""

# 1. Textes qui se terminent par " :"
echo "1. Textes avec deux-points dans la clé:"
grep -rh "{{ _('[^']* :') }}" --include="*.html" . | sed "s/{{ _('\([^']*\)') }}/\1/" | sort -u | while read text; do
    echo "   ❌ $text"
done

echo ""
echo "2. Textes avec structure fragmentée:"
grep -rn "{{ _('.*') }}.*{{ _('.*') }}" --include="*.html" . | head -20

echo ""
echo "3. Recommandations par langue:"
echo ""
echo "   🇫🇷 FRANÇAIS:"
echo "      - Garder l'espace avant le deux-points"
echo "      - Exemple: 'Extraction intelligente :'"
echo ""
echo "   🇬🇧 ANGLAIS:"
echo "      - Supprimer l'espace avant le deux-points"
echo "      - Exemple: 'Intelligent Extraction:'"
echo ""
echo "   🇪🇸 ESPAGNOL:"
echo "      - Pas d'espace avant le deux-points"
echo "      - Exemple: 'Extracción inteligente:'"
echo ""
echo "   🇩🇪 ALLEMAND:"
echo "      - Pas d'espace avant le deux-points"
echo "      - Exemple: 'Intelligente Extraktion:'"
echo ""
echo "   🇨🇳 CHINOIS/JAPONAIS:"
echo "      - Utiliser le deux-points chinois '：' (pleine largeur)"
echo "      - Exemple: '智能提取：'"
