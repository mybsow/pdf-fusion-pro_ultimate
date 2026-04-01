#!/bin/bash

echo "========================================="
echo "AJOUT DE TOUS LES TEXTES À TRADUIRE"
echo "========================================="
echo ""

# Extraire tous les textes des templates et Python
echo "1. Extraction des textes..."
grep -roh "{{ _('[^']*') }}" --include="*.html" . | sed "s/{{ _('\([^']*\)') }}/\1/" | sort -u > /tmp/all_texts.txt
grep -roh "gettext('[^']*')" --include="*.py" . | sed "s/gettext('\([^']*\)')/\1/" | sort -u >> /tmp/all_texts.txt

# Nettoyer et trier
sort -u /tmp/all_texts.txt > /tmp/texts_final.txt
total_texts=$(cat /tmp/texts_final.txt | wc -l)
echo "   ✅ $total_texts textes uniques trouvés"
echo ""

# Fonction pour ajouter un texte au fichier .po
add_text_to_po() {
    local po_file=$1
    local msgid=$2
    local msgstr=$3
    
    # Échapper les caractères spéciaux
    local escaped_msgid=$(printf '%s\n' "$msgid" | sed 's/["\\]/\\&/g')
    local escaped_msgstr=$(printf '%s\n' "$msgstr" | sed 's/["\\]/\\&/g')
    
    # Vérifier si le texte existe déjà
    if grep -q "^msgid \"$escaped_msgid\"$" "$po_file"; then
        # Vérifier si la traduction est vide
        if grep -A1 "^msgid \"$escaped_msgid\"$" "$po_file" | grep -q "msgstr \"\"$"; then
            # Remplacer la traduction vide
            sed -i "/^msgid \"$escaped_msgid\"$/{n;s/^msgstr \"\"/msgstr \"$escaped_msgstr\"/}" "$po_file"
            echo "      🔄 Mis à jour: $(echo "$msgid" | cut -c1-50)..."
        fi
    else
        # Ajouter le nouveau texte
        echo "" >> "$po_file"
        echo "msgid \"$msgid\"" >> "$po_file"
        echo "msgstr \"$msgstr\"" >> "$po_file"
        echo "      ➕ Ajouté: $(echo "$msgid" | cut -c1-50)..."
    fi
}

# Traitement pour chaque langue
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "2. Traitement de $lang..."
    
    case $lang in
        fr)
            # Français : garder identique
            echo "   Ajout des textes français..."
            while IFS= read -r text; do
                [ -z "$text" ] && continue
                add_text_to_po "$po_file" "$text" "$text"
            done < /tmp/texts_final.txt
            ;;
        
        en)
            # Anglais : traduction de base (pour l'instant garder identique)
            echo "   Ajout des textes anglais..."
            while IFS= read -r text; do
                [ -z "$text" ] && continue
                # Pour l'anglais, on garde identique en attendant les vraies traductions
                add_text_to_po "$po_file" "$text" "$text"
            done < /tmp/texts_final.txt
            ;;
        
        es)
            # Espagnol : garder identique pour l'instant
            echo "   Ajout des textes espagnols..."
            while IFS= read -r text; do
                [ -z "$text" ] && continue
                add_text_to_po "$po_file" "$text" "$text"
            done < /tmp/texts_final.txt
            ;;
        
        *)
            # Autres langues : garder identique
            echo "   Ajout des textes pour $lang..."
            while IFS= read -r text; do
                [ -z "$text" ] && continue
                add_text_to_po "$po_file" "$text" "$text"
            done < /tmp/texts_final.txt
            ;;
    esac
    
    echo ""
done

echo "3. Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   Compilation $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        size=$(ls -lh "${po_file%.po}.mo" | awk '{print $5}')
        echo "✅ ($size)"
    else
        echo "❌ Erreur"
    fi
done

echo ""
echo "========================================="
echo "✅ TERMINÉ !"
echo "========================================="
echo ""
echo "📊 Statistiques:"
echo "   - $total_texts textes ajoutés"
echo "   - 11 langues traitées"
echo ""
echo "🔄 Redémarrez l'application pour voir les changements:"
echo "   pkill -f python"
echo "   python app.py"
