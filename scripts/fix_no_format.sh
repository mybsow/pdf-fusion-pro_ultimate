#!/bin/bash
# fix_no_format.sh

for lang in pt it de ja ru ar nl zh es en; do
    echo "🔧 Correction de translations/$lang/LC_MESSAGES/messages.po"
    
    # Créer un fichier temporaire
    cp translations/$lang/LC_MESSAGES/messages.po /tmp/messages.po.$lang
    
    # Ajouter #, no-python-format après la ligne #: templates/pdf/index.html:12
    awk '
    {
        print $0
        if ($0 ~ /^#: templates\/pdf\/index.html:12/) {
            getline
            if ($0 !~ /^#, no-python-format/) {
                print "#, no-python-format"
            }
            print $0
        }
    }
    ' /tmp/messages.po.$lang > translations/$lang/LC_MESSAGES/messages.po.new
    
    mv translations/$lang/LC_MESSAGES/messages.po.new translations/$lang/LC_MESSAGES/messages.po
    rm -f /tmp/messages.po.$lang
done

echo "✅ Correction terminée"