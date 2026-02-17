#!/bin/bash

echo "Extraction des textes à traduire..."
pybabel extract -F babel.cfg -o messages.pot .

echo "Mise à jour des traductions existantes..."
pybabel update -i messages.pot -d translations

echo "Compilation des traductions..."
pybabel compile -d translations

echo "Terminé !"