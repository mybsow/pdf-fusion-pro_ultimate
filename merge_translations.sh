#!/bin/bash

echo "========================================="
echo "FUSION DES TRADUCTIONS"
echo "========================================="
echo ""

# Langue modèle complète
MODEL="it"

# Langues cibles
TARGET_LANGS=("pt" "de" "es" "ja" "ru" "ar")

echo "1. Analyse de la langue modèle ($MODEL)..."
MODEL_PO="translations/$MODEL/LC_MESSAGES/messages.po"
MODEL_ENTRIES=$(grep -c "^msgid" "$MODEL_PO")
echo "   $MODEL: $MODEL_ENTRIES entrées"
echo ""

echo "2. Fusion des traductions..."
for target in "${TARGET_LANGS[@]}"; do
    echo "   $target..."
    
    TARGET_PO="translations/$target/LC_MESSAGES/messages.po"
    
    if [ -f "$TARGET_PO" ]; then
        # Sauvegarder
        cp "$TARGET_PO" "$TARGET_PO.specific"
        
        # Extraire les traductions spécifiques déjà présentes
        echo "      📝 Extraction des traductions spécifiques..."
        grep "^msgid" "$TARGET_PO.specific" | while read line; do
            msgid=$(echo "$line" | sed 's/msgid "\(.*\)"/\1/')
            if grep -q "^msgid \"$msgid\"$" "$MODEL_PO"; then
                # Remplacer dans le modèle
                specific_trans=$(grep -A1 "^msgid \"$msgid\"$" "$TARGET_PO.specific" | grep "^msgstr" | sed 's/msgstr "\(.*\)"/\1/')
                if [ -n "$specific_trans" ] && [ "$specific_trans" != "$msgid" ]; then
                    echo "         🟢 Garde: $msgid -> $specific_trans"
                fi
            fi
        done
        
        # Copier le fichier modèle
        cp "$MODEL_PO" "$TARGET_PO"
        
        # Réappliquer les traductions spécifiques
        echo "      🔄 Réapplication des traductions spécifiques..."
        grep "^msgid" "$TARGET_PO.specific" | while read line; do
            msgid=$(echo "$line" | sed 's/msgid "\(.*\)"/\1/')
            specific_trans=$(grep -A1 "^msgid \"$msgid\"$" "$TARGET_PO.specific" | grep "^msgstr" | sed 's/msgstr "\(.*\)"/\1/')
            
            if [ -n "$specific_trans" ] && [ "$specific_trans" != "$msgid" ]; then
                # Mettre à jour la traduction dans le fichier copié
                sed -i "/^msgid \"$msgid\"$/{n;s/^msgstr \".*\"/msgstr \"$specific_trans\"/}" "$TARGET_PO"
                echo "         ✅ Restauré: $msgid"
            fi
        done
        
        # Compiler
        msgfmt -o "translations/$target/LC_MESSAGES/messages.mo" "$TARGET_PO" 2>/dev/null
        if [ $? -eq 0 ]; then
            size=$(stat -c%s "translations/$target/LC_MESSAGES/messages.mo")
            entries=$(grep -c "^msgid" "$TARGET_PO")
            echo "      ✅ Compilé: $entries entrées, ${size} octets"
        else
            echo "      ❌ Erreur de compilation"
        fi
        
        # Nettoyer
        rm -f "$TARGET_PO.specific"
    else
        echo "      ❌ Fichier non trouvé"
    fi
done

echo ""
echo "3. Vérification finale..."
for target in "${TARGET_LANGS[@]}"; do
    mo_file="translations/$target/LC_MESSAGES/messages.mo"
    if [ -f "$mo_file" ]; then
        size=$(stat -c%s "$mo_file")
        entries=$(grep -c "^msgid" "translations/$target/LC_MESSAGES/messages.po")
        if [ $size -gt 10000 ]; then
            echo "   ✅ $target: $entries entrées, ${size} octets"
        else
            echo "   ⚠️  $target: $entries entrées, ${size} octets"
        fi
    fi
done

echo ""
echo "========================================="
echo "✅ FUSION TERMINÉE"
echo "========================================="
