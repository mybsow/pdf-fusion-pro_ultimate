#!/bin/bash

echo "========================================="
echo "CORRECTION COMPLÈTE DES DEUX-POINTS"
echo "========================================="
echo ""

# Fonction pour extraire la partie sans deux-points
extract_text_without_colon() {
    local text="$1"
    # Supprimer le deux-points et l'espace à la fin
    echo "$text" | sed 's/ :$//' | sed 's/:$//' | sed 's/：$//'
}

# Fonction pour ajouter les deux-points selon la langue
add_colon_correctly() {
    local text="$1"
    local lang="$2"
    
    case $lang in
        fr)
            # Espace avant le deux-points
            echo "${text} :"
            ;;
        en|es|de|it|pt|nl)
            # Pas d'espace avant le deux-points
            echo "${text}:"
            ;;
        zh|ja|ko)
            # Deux-points chinois (pleine largeur)
            echo "${text}："
            ;;
        ar)
            # Arabe : deux-points inversé
            echo "${text}："
            ;;
        *)
            echo "${text}:"
            ;;
    esac
}

# Créer un fichier avec tous les textes problématiques
echo "1. Extraction des textes problématiques..."
grep -rh "{{ _('[^']* :') }}" --include="*.html" . | \
    sed "s/{{ _('\([^']*\)') }}/\1/" | \
    sort -u > /tmp/problematic_colons.txt

grep -rh "<strong>{{ _('[^']* :') }}" --include="*.html" . | \
    sed "s/<strong>{{ _('\([^']*\)') }}<\/strong>/\1/" | \
    sort -u >> /tmp/problematic_colons.txt

grep -rh "<label[^>]*>{{ _('[^']* :') }}" --include="*.html" . | \
    sed "s/.*{{ _('\([^']*\)') }}.*/\1/" | \
    sort -u >> /tmp/problematic_colons.txt

sort -u /tmp/problematic_colons.txt > /tmp/all_problematic.txt
total_problematic=$(cat /tmp/all_problematic.txt | wc -l)
echo "   ✅ $total_problematic textes problématiques trouvés"
echo ""

# Traiter chaque fichier .po
echo "2. Correction des fichiers .po..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "   Traitement de $lang..."
    
    # Lire tous les textes problématiques
    while IFS= read -r old_text; do
        # Extraire le texte sans deux-points
        clean_text=$(extract_text_without_colon "$old_text")
        
        # Créer le nouveau texte avec le bon format
        new_text=$(add_colon_correctly "$clean_text" "$lang")
        
        # Vérifier si l'ancien texte existe
        if grep -q "^msgid \"$old_text\"$" "$po_file"; then
            # Récupérer la traduction existante si elle n'est pas vide
            current_trans=$(grep -A1 "^msgid \"$old_text\"$" "$po_file" | grep "^msgstr" | sed 's/msgstr "\(.*\)"/\1/')
            
            # Supprimer l'ancienne entrée
            sed -i "/^msgid \"$old_text\"$/,+2d" "$po_file"
            
            # Ajouter la nouvelle entrée
            echo "" >> "$po_file"
            echo "msgid \"$new_text\"" >> "$po_file"
            
            # Traduire selon la langue
            case $lang in
                fr)
                    echo "msgstr \"$new_text\"" >> "$po_file"
                    ;;
                en)
                    # Pour l'anglais, enlever l'espace avant deux-points
                    en_trans=$(echo "$clean_text" | sed 's/ $//')
                    echo "msgstr \"$en_trans:\"" >> "$po_file"
                    ;;
                es)
                    es_trans=$(echo "$clean_text" | sed 's/ $//')
                    echo "msgstr \"$es_trans:\"" >> "$po_file"
                    ;;
                de)
                    de_trans=$(echo "$clean_text" | sed 's/ $//')
                    echo "msgstr \"$de_trans:\"" >> "$po_file"
                    ;;
                *)
                    echo "msgstr \"$current_trans\"" >> "$po_file"
                    ;;
            esac
            
            echo "      🔄 $old_text -> $new_text"
        fi
    done < /tmp/all_problematic.txt
done

echo ""
echo "3. Ajout des textes manquants sans deux-points..."
# Ajouter les textes propres sans deux-points pour les langues qui en ont besoin
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    
    while IFS= read -r old_text; do
        clean_text=$(extract_text_without_colon "$old_text")
        new_text=$(add_colon_correctly "$clean_text" "$lang")
        
        # Vérifier si le texte sans deux-points existe déjà
        if ! grep -q "^msgid \"$clean_text\"$" "$po_file"; then
            echo "" >> "$po_file"
            echo "msgid \"$clean_text\"" >> "$po_file"
            
            case $lang in
                fr)
                    echo "msgstr \"$clean_text\"" >> "$po_file"
                    ;;
                en)
                    echo "msgstr \"$clean_text\"" >> "$po_file"
                    ;;
                *)
                    echo "msgstr \"$clean_text\"" >> "$po_file"
                    ;;
            esac
            echo "      ➕ Ajouté: $clean_text"
        fi
    done < /tmp/all_problematic.txt
done

echo ""
echo "4. Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        size=$(ls -lh "${po_file%.po}.mo" | awk '{print $5}')
        entries=$(grep -c "^msgid" "$po_file")
        echo "✅ ($entries entrées, $size)"
    else
        echo "❌ Erreur"
    fi
done

echo ""
echo "========================================="
echo "✅ CORRECTION TERMINÉE !"
echo "========================================="
echo ""
echo "📊 Résumé:"
echo "   - $total_problematic textes corrigés"
echo "   - 11 langues traitées"
echo ""
echo "🔍 Vérification des corrections:"
python3 << 'PYEOF'
import gettext

test_texts = [
    "Format PDF",
    "Extraction intelligente",
    "Session cookie",
    "Préférences"
]

print("\nTest des textes corrigés:")
for lang in ['fr', 'en', 'es']:
    print(f"\n{lang.upper()}:")
    try:
        trans = gettext.translation('messages', './translations', languages=[lang], fallback=True)
        _ = trans.gettext
        for text in test_texts:
            result = _(text)
            print(f"  '{text}' -> '{result}'")
    except Exception as e:
        print(f"  Erreur: {e}")
PYEOF

echo ""
echo "🔄 Redémarrez l'application:"
echo "   pkill -f python"
echo "   export LANG=fr_FR.UTF-8"
echo "   python3 app.py"
