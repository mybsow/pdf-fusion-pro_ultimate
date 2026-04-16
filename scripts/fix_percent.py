#!/usr/bin/env python3
# scripts/add_all_missing_translations.py

import re
import os
import subprocess

# Tous les textes manquants
MISSING_TEXTS = [
    # Général
    "Sélectionnez votre fichier",
    "Sélectionner des images",
    "Sélectionner des fichiers",
    
    # Format/Plages
    "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"",
    
    # Image to Excel
    "Convertissez votre image en Excel",
    "Extrayez les tableaux de vos images ou PDF en feuilles Excel",
    
    # CSV to Excel
    "Convertissez vos fichiers CSV en Excel",
    "Transformez vos fichiers CSV en feuilles Excel",
    "Sélectionnez vos fichiers CSV",
    "Séparateur",
    
    # Prepare Form
    "Créez votre formulaire PDF",
    "Sélectionnez votre document",
    "Type de formulaire",
    "Langue du formulaire",
    "Couleur des champs",
    "Style des champs",
    "Ajouter des textes indicatifs",
    "Ex: \"Nom\", \"Prénom\"...",
    "Marquer les champs obligatoires",
    "Ajoute un astérisque (*) aux champs requis",
    
    # Sign PDF
    "Signez votre PDF",
    "Dessinez votre signature",
    
    # Edit PDF
    "Éditez votre PDF",
    
    # Redact PDF
    "Caviardez votre PDF",
    "Texte à caviarder",
    "Pages à traiter",
    "Plage de pages",
    
    # PDF to HTML
    "Convertissez votre PDF en HTML",
    "Transformez votre document PDF en page web HTML",
    
    # PDF to TXT
    "Convertissez votre PDF en texte",
    "Extrayez le texte de votre document PDF",
    
    # TXT to PDF
    "Convertissez votre texte en PDF",
    "Téléchargez un fichier texte ou collez votre contenu directement",
    "Sélectionnez votre fichier texte",
    "Police",
    
    # HTML to PDF
    "Convertissez votre code HTML en PDF",
    "Téléchargez un fichier HTML ou collez votre code directement",
    "Sélectionnez votre fichier HTML",
    
    # Image to PDF
    "Convertissez vos images en PDF",
    "Transformez vos images en document PDF",
    "Sélectionnez vos images",
    "Qualité",
    
    # PowerPoint to PDF
    "Sélectionnez vos fichiers PowerPoint",
    
    # Excel to PDF
    "Convertissez vos fichiers Excel en PDF",
    "Transformez vos feuilles Excel en documents PDF",
    "Sélectionnez vos fichiers Excel",
]

# Traductions pour toutes les langues
TRANSLATIONS = {
    'fr': {t: t for t in MISSING_TEXTS},
    
    'en': {
        "Sélectionnez votre fichier": "Select your file",
        "Sélectionner des images": "Select images",
        "Sélectionner des fichiers": "Select files",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Format: numbers separated by commas, ranges with dash. Ex: \"1,3-5\"",
        "Convertissez votre image en Excel": "Convert your image to Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Extract tables from your images or PDF to Excel sheets",
        "Convertissez vos fichiers CSV en Excel": "Convert your CSV files to Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Transform your CSV files into Excel sheets",
        "Sélectionnez vos fichiers CSV": "Select your CSV files",
        "Séparateur": "Separator",
        "Créez votre formulaire PDF": "Create your PDF form",
        "Sélectionnez votre document": "Select your document",
        "Type de formulaire": "Form type",
        "Langue du formulaire": "Form language",
        "Couleur des champs": "Field color",
        "Style des champs": "Field style",
        "Ajouter des textes indicatifs": "Add placeholder texts",
        "Ex: \"Nom\", \"Prénom\"...": "Ex: \"Name\", \"First name\"...",
        "Marquer les champs obligatoires": "Mark required fields",
        "Ajoute un astérisque (*) aux champs requis": "Adds an asterisk (*) to required fields",
        "Signez votre PDF": "Sign your PDF",
        "Dessinez votre signature": "Draw your signature",
        "Éditez votre PDF": "Edit your PDF",
        "Caviardez votre PDF": "Redact your PDF",
        "Texte à caviarder": "Text to redact",
        "Pages à traiter": "Pages to process",
        "Plage de pages": "Page range",
        "Convertissez votre PDF en HTML": "Convert your PDF to HTML",
        "Transformez votre document PDF en page web HTML": "Transform your PDF document into an HTML web page",
        "Convertissez votre PDF en texte": "Convert your PDF to text",
        "Extrayez le texte de votre document PDF": "Extract text from your PDF document",
        "Convertissez votre texte en PDF": "Convert your text to PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Upload a text file or paste your content directly",
        "Sélectionnez votre fichier texte": "Select your text file",
        "Police": "Font",
        "Convertissez votre code HTML en PDF": "Convert your HTML code to PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Upload an HTML file or paste your code directly",
        "Sélectionnez votre fichier HTML": "Select your HTML file",
        "Convertissez vos images en PDF": "Convert your images to PDF",
        "Transformez vos images en document PDF": "Transform your images into a PDF document",
        "Sélectionnez vos images": "Select your images",
        "Qualité": "Quality",
        "Sélectionnez vos fichiers PowerPoint": "Select your PowerPoint files",
        "Convertissez vos fichiers Excel en PDF": "Convert your Excel files to PDF",
        "Transformez vos feuilles Excel en documents PDF": "Transform your Excel sheets into PDF documents",
        "Sélectionnez vos fichiers Excel": "Select your Excel files",
    },
    
    'es': {
        "Sélectionnez votre fichier": "Seleccione su archivo",
        "Sélectionner des images": "Seleccionar imágenes",
        "Sélectionner des fichiers": "Seleccionar archivos",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Formato: números separados por comas, rangos con guión. Ej: \"1,3-5\"",
        "Convertissez votre image en Excel": "Convierta su imagen a Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Extraiga tablas de sus imágenes o PDF a hojas de Excel",
        "Convertissez vos fichiers CSV en Excel": "Convierta sus archivos CSV a Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Transforme sus archivos CSV en hojas de Excel",
        "Sélectionnez vos fichiers CSV": "Seleccione sus archivos CSV",
        "Séparateur": "Separador",
        "Créez votre formulaire PDF": "Cree su formulario PDF",
        "Sélectionnez votre document": "Seleccione su documento",
        "Type de formulaire": "Tipo de formulario",
        "Langue du formulaire": "Idioma del formulario",
        "Couleur des champs": "Color de los campos",
        "Style des champs": "Estilo de los campos",
        "Ajouter des textes indicatifs": "Agregar textos indicativos",
        "Ex: \"Nom\", \"Prénom\"...": "Ej: \"Nombre\", \"Apellido\"...",
        "Marquer les champs obligatoires": "Marcar campos obligatorios",
        "Ajoute un astérisque (*) aux champs requis": "Agrega un asterisco (*) a los campos requeridos",
        "Signez votre PDF": "Firme su PDF",
        "Dessinez votre signature": "Dibuje su firma",
        "Éditez votre PDF": "Edite su PDF",
        "Caviardez votre PDF": "Censure su PDF",
        "Texte à caviarder": "Texto a censurar",
        "Pages à traiter": "Páginas a procesar",
        "Plage de pages": "Rango de páginas",
        "Convertissez votre PDF en HTML": "Convierta su PDF a HTML",
        "Transformez votre document PDF en page web HTML": "Transforme su documento PDF en página web HTML",
        "Convertissez votre PDF en texte": "Convierta su PDF a texto",
        "Extrayez le texte de votre document PDF": "Extraiga el texto de su documento PDF",
        "Convertissez votre texte en PDF": "Convierta su texto a PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Suba un archivo de texto o pegue su contenido directamente",
        "Sélectionnez votre fichier texte": "Seleccione su archivo de texto",
        "Police": "Fuente",
        "Convertissez votre code HTML en PDF": "Convierta su código HTML a PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Suba un archivo HTML o pegue su código directamente",
        "Sélectionnez votre fichier HTML": "Seleccione su archivo HTML",
        "Convertissez vos images en PDF": "Convierta sus imágenes a PDF",
        "Transformez vos images en document PDF": "Transforme sus imágenes en documento PDF",
        "Sélectionnez vos images": "Seleccione sus imágenes",
        "Qualité": "Calidad",
        "Sélectionnez vos fichiers PowerPoint": "Seleccione sus archivos PowerPoint",
        "Convertissez vos fichiers Excel en PDF": "Convierta sus archivos Excel a PDF",
        "Transformez vos feuilles Excel en documents PDF": "Transforme sus hojas Excel en documentos PDF",
        "Sélectionnez vos fichiers Excel": "Seleccione sus archivos Excel",
    },
    
    'de': {
        "Sélectionnez votre fichier": "Wählen Sie Ihre Datei aus",
        "Sélectionner des images": "Bilder auswählen",
        "Sélectionner des fichiers": "Dateien auswählen",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Format: Zahlen durch Kommas getrennt, Bereiche mit Bindestrich. Bsp: \"1,3-5\"",
        "Convertissez votre image en Excel": "Konvertieren Sie Ihr Bild in Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Extrahieren Sie Tabellen aus Ihren Bildern oder PDF in Excel-Tabellen",
        "Convertissez vos fichiers CSV en Excel": "Konvertieren Sie Ihre CSV-Dateien in Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Wandeln Sie Ihre CSV-Dateien in Excel-Tabellen um",
        "Sélectionnez vos fichiers CSV": "Wählen Sie Ihre CSV-Dateien aus",
        "Séparateur": "Trennzeichen",
        "Créez votre formulaire PDF": "Erstellen Sie Ihr PDF-Formular",
        "Sélectionnez votre document": "Wählen Sie Ihr Dokument aus",
        "Type de formulaire": "Formulartyp",
        "Langue du formulaire": "Formularsprache",
        "Couleur des champs": "Feldfarbe",
        "Style des champs": "Feldstil",
        "Ajouter des textes indicatifs": "Platzhaltertexte hinzufügen",
        "Ex: \"Nom\", \"Prénom\"...": "Bsp: \"Name\", \"Vorname\"...",
        "Marquer les champs obligatoires": "Pflichtfelder markieren",
        "Ajoute un astérisque (*) aux champs requis": "Fügt ein Sternchen (*) zu Pflichtfeldern hinzu",
        "Signez votre PDF": "Unterschreiben Sie Ihr PDF",
        "Dessinez votre signature": "Zeichnen Sie Ihre Unterschrift",
        "Éditez votre PDF": "Bearbeiten Sie Ihr PDF",
        "Caviardez votre PDF": "Schwärzen Sie Ihr PDF",
        "Texte à caviarder": "Zu schwärzender Text",
        "Pages à traiter": "Zu verarbeitende Seiten",
        "Plage de pages": "Seitenbereich",
        "Convertissez votre PDF en HTML": "Konvertieren Sie Ihr PDF in HTML",
        "Transformez votre document PDF en page web HTML": "Wandeln Sie Ihr PDF-Dokument in eine HTML-Webseite um",
        "Convertissez votre PDF en texte": "Konvertieren Sie Ihr PDF in Text",
        "Extrayez le texte de votre document PDF": "Extrahieren Sie Text aus Ihrem PDF-Dokument",
        "Convertissez votre texte en PDF": "Konvertieren Sie Ihren Text in PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Laden Sie eine Textdatei hoch oder fügen Sie Ihren Inhalt direkt ein",
        "Sélectionnez votre fichier texte": "Wählen Sie Ihre Textdatei aus",
        "Police": "Schriftart",
        "Convertissez votre code HTML en PDF": "Konvertieren Sie Ihren HTML-Code in PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Laden Sie eine HTML-Datei hoch oder fügen Sie Ihren Code direkt ein",
        "Sélectionnez votre fichier HTML": "Wählen Sie Ihre HTML-Datei aus",
        "Convertissez vos images en PDF": "Konvertieren Sie Ihre Bilder in PDF",
        "Transformez vos images en document PDF": "Wandeln Sie Ihre Bilder in ein PDF-Dokument um",
        "Sélectionnez vos images": "Wählen Sie Ihre Bilder aus",
        "Qualité": "Qualität",
        "Sélectionnez vos fichiers PowerPoint": "Wählen Sie Ihre PowerPoint-Dateien aus",
        "Convertissez vos fichiers Excel en PDF": "Konvertieren Sie Ihre Excel-Dateien in PDF",
        "Transformez vos feuilles Excel en documents PDF": "Wandeln Sie Ihre Excel-Tabellen in PDF-Dokumente um",
        "Sélectionnez vos fichiers Excel": "Wählen Sie Ihre Excel-Dateien aus",
    },
    
    'it': {
        "Sélectionnez votre fichier": "Seleziona il tuo file",
        "Sélectionner des images": "Seleziona immagini",
        "Sélectionner des fichiers": "Seleziona file",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Formato: numeri separati da virgole, intervalli con trattino. Es: \"1,3-5\"",
        "Convertissez votre image en Excel": "Converti la tua immagine in Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Estrai tabelle dalle tue immagini o PDF in fogli Excel",
        "Convertissez vos fichiers CSV en Excel": "Converti i tuoi file CSV in Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Trasforma i tuoi file CSV in fogli Excel",
        "Sélectionnez vos fichiers CSV": "Seleziona i tuoi file CSV",
        "Séparateur": "Separatore",
        "Créez votre formulaire PDF": "Crea il tuo modulo PDF",
        "Sélectionnez votre document": "Seleziona il tuo documento",
        "Type de formulaire": "Tipo di modulo",
        "Langue du formulaire": "Lingua del modulo",
        "Couleur des champs": "Colore dei campi",
        "Style des champs": "Stile dei campi",
        "Ajouter des textes indicatifs": "Aggiungi testi segnaposto",
        "Ex: \"Nom\", \"Prénom\"...": "Es: \"Nome\", \"Cognome\"...",
        "Marquer les champs obligatoires": "Contrassegna campi obbligatori",
        "Ajoute un astérisque (*) aux champs requis": "Aggiunge un asterisco (*) ai campi obbligatori",
        "Signez votre PDF": "Firma il tuo PDF",
        "Dessinez votre signature": "Disegna la tua firma",
        "Éditez votre PDF": "Modifica il tuo PDF",
        "Caviardez votre PDF": "Oscura il tuo PDF",
        "Texte à caviarder": "Testo da oscurare",
        "Pages à traiter": "Pagine da elaborare",
        "Plage de pages": "Intervallo di pagine",
        "Convertissez votre PDF en HTML": "Converti il tuo PDF in HTML",
        "Transformez votre document PDF en page web HTML": "Trasforma il tuo documento PDF in una pagina web HTML",
        "Convertissez votre PDF en texte": "Converti il tuo PDF in testo",
        "Extrayez le texte de votre document PDF": "Estrai il testo dal tuo documento PDF",
        "Convertissez votre texte en PDF": "Converti il tuo testo in PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Carica un file di testo o incolla direttamente il contenuto",
        "Sélectionnez votre fichier texte": "Seleziona il tuo file di testo",
        "Police": "Carattere",
        "Convertissez votre code HTML en PDF": "Converti il tuo codice HTML in PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Carica un file HTML o incolla direttamente il codice",
        "Sélectionnez votre fichier HTML": "Seleziona il tuo file HTML",
        "Convertissez vos images en PDF": "Converti le tue immagini in PDF",
        "Transformez vos images en document PDF": "Trasforma le tue immagini in un documento PDF",
        "Sélectionnez vos images": "Seleziona le tue immagini",
        "Qualité": "Qualità",
        "Sélectionnez vos fichiers PowerPoint": "Seleziona i tuoi file PowerPoint",
        "Convertissez vos fichiers Excel en PDF": "Converti i tuoi file Excel in PDF",
        "Transformez vos feuilles Excel en documents PDF": "Trasforma i tuoi fogli Excel in documenti PDF",
        "Sélectionnez vos fichiers Excel": "Seleziona i tuoi file Excel",
    },
    
    'pt': {
        "Sélectionnez votre fichier": "Selecione seu arquivo",
        "Sélectionner des images": "Selecionar imagens",
        "Sélectionner des fichiers": "Selecionar arquivos",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Formato: números separados por vírgulas, intervalos com hífen. Ex: \"1,3-5\"",
        "Convertissez votre image en Excel": "Converta sua imagem em Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Extraia tabelas de suas imagens ou PDF para planilhas Excel",
        "Convertissez vos fichiers CSV en Excel": "Converta seus arquivos CSV em Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Transforme seus arquivos CSV em planilhas Excel",
        "Sélectionnez vos fichiers CSV": "Selecione seus arquivos CSV",
        "Séparateur": "Separador",
        "Créez votre formulaire PDF": "Crie seu formulário PDF",
        "Sélectionnez votre document": "Selecione seu documento",
        "Type de formulaire": "Tipo de formulário",
        "Langue du formulaire": "Idioma do formulário",
        "Couleur des champs": "Cor dos campos",
        "Style des champs": "Estilo dos campos",
        "Ajouter des textes indicatifs": "Adicionar textos indicativos",
        "Ex: \"Nom\", \"Prénom\"...": "Ex: \"Nome\", \"Sobrenome\"...",
        "Marquer les champs obligatoires": "Marcar campos obrigatórios",
        "Ajoute un astérisque (*) aux champs requis": "Adiciona um asterisco (*) aos campos obrigatórios",
        "Signez votre PDF": "Assine seu PDF",
        "Dessinez votre signature": "Desenhe sua assinatura",
        "Éditez votre PDF": "Edite seu PDF",
        "Caviardez votre PDF": "Tarje seu PDF",
        "Texte à caviarder": "Texto a tarjar",
        "Pages à traiter": "Páginas a processar",
        "Plage de pages": "Intervalo de páginas",
        "Convertissez votre PDF en HTML": "Converta seu PDF em HTML",
        "Transformez votre document PDF en page web HTML": "Transforme seu documento PDF em página web HTML",
        "Convertissez votre PDF en texte": "Converta seu PDF em texto",
        "Extrayez le texte de votre document PDF": "Extraia texto do seu documento PDF",
        "Convertissez votre texte en PDF": "Converta seu texto em PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Carregue um arquivo de texto ou cole seu conteúdo diretamente",
        "Sélectionnez votre fichier texte": "Selecione seu arquivo de texto",
        "Police": "Fonte",
        "Convertissez votre code HTML en PDF": "Converta seu código HTML em PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Carregue um arquivo HTML ou cole seu código diretamente",
        "Sélectionnez votre fichier HTML": "Selecione seu arquivo HTML",
        "Convertissez vos images en PDF": "Converta suas imagens em PDF",
        "Transformez vos images en document PDF": "Transforme suas imagens em documento PDF",
        "Sélectionnez vos images": "Selecione suas imagens",
        "Qualité": "Qualidade",
        "Sélectionnez vos fichiers PowerPoint": "Selecione seus arquivos PowerPoint",
        "Convertissez vos fichiers Excel en PDF": "Converta seus arquivos Excel em PDF",
        "Transformez vos feuilles Excel en documents PDF": "Transforme suas planilhas Excel em documentos PDF",
        "Sélectionnez vos fichiers Excel": "Selecione seus arquivos Excel",
    },
    
    'nl': {
        "Sélectionnez votre fichier": "Selecteer uw bestand",
        "Sélectionner des images": "Afbeeldingen selecteren",
        "Sélectionner des fichiers": "Bestanden selecteren",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Formaat: nummers gescheiden door komma's, bereiken met streepje. Bv: \"1,3-5\"",
        "Convertissez votre image en Excel": "Converteer uw afbeelding naar Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Extraheer tabellen uit uw afbeeldingen of PDF naar Excel-werkbladen",
        "Convertissez vos fichiers CSV en Excel": "Converteer uw CSV-bestanden naar Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Transformeer uw CSV-bestanden in Excel-werkbladen",
        "Sélectionnez vos fichiers CSV": "Selecteer uw CSV-bestanden",
        "Séparateur": "Scheidingsteken",
        "Créez votre formulaire PDF": "Maak uw PDF-formulier",
        "Sélectionnez votre document": "Selecteer uw document",
        "Type de formulaire": "Formuliertype",
        "Langue du formulaire": "Formuliertaal",
        "Couleur des champs": "Veldkleur",
        "Style des champs": "Veldstijl",
        "Ajouter des textes indicatifs": "Plaatsvervangende teksten toevoegen",
        "Ex: \"Nom\", \"Prénom\"...": "Bv: \"Naam\", \"Voornaam\"...",
        "Marquer les champs obligatoires": "Verplichte velden markeren",
        "Ajoute un astérisque (*) aux champs requis": "Voegt een asterisk (*) toe aan verplichte velden",
        "Signez votre PDF": "Onderteken uw PDF",
        "Dessinez votre signature": "Teken uw handtekening",
        "Éditez votre PDF": "Bewerk uw PDF",
        "Caviardez votre PDF": "Redigeer uw PDF",
        "Texte à caviarder": "Tekst om te redigeren",
        "Pages à traiter": "Te verwerken pagina's",
        "Plage de pages": "Paginabereik",
        "Convertissez votre PDF en HTML": "Converteer uw PDF naar HTML",
        "Transformez votre document PDF en page web HTML": "Transformeer uw PDF-document in een HTML-webpagina",
        "Convertissez votre PDF en texte": "Converteer uw PDF naar tekst",
        "Extrayez le texte de votre document PDF": "Extraheer tekst uit uw PDF-document",
        "Convertissez votre texte en PDF": "Converteer uw tekst naar PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Upload een tekstbestand of plak uw inhoud direct",
        "Sélectionnez votre fichier texte": "Selecteer uw tekstbestand",
        "Police": "Lettertype",
        "Convertissez votre code HTML en PDF": "Converteer uw HTML-code naar PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Upload een HTML-bestand of plak uw code direct",
        "Sélectionnez votre fichier HTML": "Selecteer uw HTML-bestand",
        "Convertissez vos images en PDF": "Converteer uw afbeeldingen naar PDF",
        "Transformez vos images en document PDF": "Transformeer uw afbeeldingen in een PDF-document",
        "Sélectionnez vos images": "Selecteer uw afbeeldingen",
        "Qualité": "Kwaliteit",
        "Sélectionnez vos fichiers PowerPoint": "Selecteer uw PowerPoint-bestanden",
        "Convertissez vos fichiers Excel en PDF": "Converteer uw Excel-bestanden naar PDF",
        "Transformez vos feuilles Excel en documents PDF": "Transformeer uw Excel-werkbladen in PDF-documenten",
        "Sélectionnez vos fichiers Excel": "Selecteer uw Excel-bestanden",
    },
    
    'ar': {
        "Sélectionnez votre fichier": "اختر ملفك",
        "Sélectionner des images": "اختر الصور",
        "Sélectionner des fichiers": "اختر الملفات",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "التنسيق: أرقام مفصولة بفواصل، نطاقات بشرطة. مثال: \"1,3-5\"",
        "Convertissez votre image en Excel": "حول صورتك إلى إكسل",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "استخرج الجداول من صورك أو PDF إلى أوراق إكسل",
        "Convertissez vos fichiers CSV en Excel": "حول ملفات CSV إلى إكسل",
        "Transformez vos fichiers CSV en feuilles Excel": "حول ملفات CSV إلى أوراق إكسل",
        "Sélectionnez vos fichiers CSV": "اختر ملفات CSV",
        "Séparateur": "فاصل",
        "Créez votre formulaire PDF": "أنشئ نموذج PDF الخاص بك",
        "Sélectionnez votre document": "اختر مستندك",
        "Type de formulaire": "نوع النموذج",
        "Langue du formulaire": "لغة النموذج",
        "Couleur des champs": "لون الحقول",
        "Style des champs": "نمط الحقول",
        "Ajouter des textes indicatifs": "أضف نصوصًا إرشادية",
        "Ex: \"Nom\", \"Prénom\"...": "مثال: \"الاسم\"، \"الاسم الأول\"...",
        "Marquer les champs obligatoires": "حدد الحقول الإلزامية",
        "Ajoute un astérisque (*) aux champs requis": "يضيف علامة النجمة (*) إلى الحقول المطلوبة",
        "Signez votre PDF": "وقع PDF الخاص بك",
        "Dessinez votre signature": "ارسم توقيعك",
        "Éditez votre PDF": "حرر PDF الخاص بك",
        "Caviardez votre PDF": "احجب محتوى PDF الخاص بك",
        "Texte à caviarder": "النص المراد حجبه",
        "Pages à traiter": "الصفحات المراد معالجتها",
        "Plage de pages": "نطاق الصفحات",
        "Convertissez votre PDF en HTML": "حول PDF إلى HTML",
        "Transformez votre document PDF en page web HTML": "حول مستند PDF إلى صفحة ويب HTML",
        "Convertissez votre PDF en texte": "حول PDF إلى نص",
        "Extrayez le texte de votre document PDF": "استخرج النص من مستند PDF",
        "Convertissez votre texte en PDF": "حول النص إلى PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "حمّل ملفًا نصيًا أو الصق المحتوى مباشرة",
        "Sélectionnez votre fichier texte": "اختر ملفك النصي",
        "Police": "الخط",
        "Convertissez votre code HTML en PDF": "حول كود HTML إلى PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "حمّل ملف HTML أو الصق الكود مباشرة",
        "Sélectionnez votre fichier HTML": "اختر ملف HTML",
        "Convertissez vos images en PDF": "حول صورك إلى PDF",
        "Transformez vos images en document PDF": "حول صورك إلى مستند PDF",
        "Sélectionnez vos images": "اختر صورك",
        "Qualité": "الجودة",
        "Sélectionnez vos fichiers PowerPoint": "اختر ملفات PowerPoint",
        "Convertissez vos fichiers Excel en PDF": "حول ملفات Excel إلى PDF",
        "Transformez vos feuilles Excel en documents PDF": "حول أوراق Excel إلى مستندات PDF",
        "Sélectionnez vos fichiers Excel": "اختر ملفات Excel",
    },
    
    'zh': {
        "Sélectionnez votre fichier": "选择您的文件",
        "Sélectionner des images": "选择图像",
        "Sélectionner des fichiers": "选择文件",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "格式：数字用逗号分隔，范围用连字符。例如：\"1,3-5\"",
        "Convertissez votre image en Excel": "将您的图像转换为 Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "从图像或 PDF 中提取表格到 Excel 工作表",
        "Convertissez vos fichiers CSV en Excel": "将 CSV 文件转换为 Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "将 CSV 文件转换为 Excel 工作表",
        "Sélectionnez vos fichiers CSV": "选择您的 CSV 文件",
        "Séparateur": "分隔符",
        "Créez votre formulaire PDF": "创建您的 PDF 表单",
        "Sélectionnez votre document": "选择您的文档",
        "Type de formulaire": "表单类型",
        "Langue du formulaire": "表单语言",
        "Couleur des champs": "字段颜色",
        "Style des champs": "字段样式",
        "Ajouter des textes indicatifs": "添加占位文本",
        "Ex: \"Nom\", \"Prénom\"...": "例如：\"姓名\"、\"名字\"...",
        "Marquer les champs obligatoires": "标记必填字段",
        "Ajoute un astérisque (*) aux champs requis": "在必填字段旁添加星号 (*)",
        "Signez votre PDF": "签署您的 PDF",
        "Dessinez votre signature": "绘制您的签名",
        "Éditez votre PDF": "编辑您的 PDF",
        "Caviardez votre PDF": "遮盖您的 PDF",
        "Texte à caviarder": "要遮盖的文本",
        "Pages à traiter": "要处理的页面",
        "Plage de pages": "页面范围",
        "Convertissez votre PDF en HTML": "将 PDF 转换为 HTML",
        "Transformez votre document PDF en page web HTML": "将 PDF 文档转换为 HTML 网页",
        "Convertissez votre PDF en texte": "将 PDF 转换为文本",
        "Extrayez le texte de votre document PDF": "从 PDF 文档中提取文本",
        "Convertissez votre texte en PDF": "将文本转换为 PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "上传文本文件或直接粘贴内容",
        "Sélectionnez votre fichier texte": "选择您的文本文件",
        "Police": "字体",
        "Convertissez votre code HTML en PDF": "将 HTML 代码转换为 PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "上传 HTML 文件或直接粘贴代码",
        "Sélectionnez votre fichier HTML": "选择您的 HTML 文件",
        "Convertissez vos images en PDF": "将图像转换为 PDF",
        "Transformez vos images en document PDF": "将图像转换为 PDF 文档",
        "Sélectionnez vos images": "选择您的图像",
        "Qualité": "质量",
        "Sélectionnez vos fichiers PowerPoint": "选择您的 PowerPoint 文件",
        "Convertissez vos fichiers Excel en PDF": "将 Excel 文件转换为 PDF",
        "Transformez vos feuilles Excel en documents PDF": "将 Excel 工作表转换为 PDF 文档",
        "Sélectionnez vos fichiers Excel": "选择您的 Excel 文件",
    },
    
    'ja': {
        "Sélectionnez votre fichier": "ファイルを選択",
        "Sélectionner des images": "画像を選択",
        "Sélectionner des fichiers": "ファイルを選択",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "形式：数字はカンマ区切り、範囲はハイフン。例：\"1,3-5\"",
        "Convertissez votre image en Excel": "画像を Excel に変換",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "画像や PDF から表を Excel シートに抽出",
        "Convertissez vos fichiers CSV en Excel": "CSV ファイルを Excel に変換",
        "Transformez vos fichiers CSV en feuilles Excel": "CSV ファイルを Excel シートに変換",
        "Sélectionnez vos fichiers CSV": "CSV ファイルを選択",
        "Séparateur": "区切り文字",
        "Créez votre formulaire PDF": "PDF フォームを作成",
        "Sélectionnez votre document": "ドキュメントを選択",
        "Type de formulaire": "フォームタイプ",
        "Langue du formulaire": "フォーム言語",
        "Couleur des champs": "フィールドの色",
        "Style des champs": "フィールドのスタイル",
        "Ajouter des textes indicatifs": "プレースホルダーテキストを追加",
        "Ex: \"Nom\", \"Prénom\"...": "例：\"名前\"、\"姓\"...",
        "Marquer les champs obligatoires": "必須フィールドをマーク",
        "Ajoute un astérisque (*) aux champs requis": "必須フィールドにアスタリスク (*) を追加",
        "Signez votre PDF": "PDF に署名",
        "Dessinez votre signature": "署名を描く",
        "Éditez votre PDF": "PDF を編集",
        "Caviardez votre PDF": "PDF を墨消し",
        "Texte à caviarder": "墨消しするテキスト",
        "Pages à traiter": "処理するページ",
        "Plage de pages": "ページ範囲",
        "Convertissez votre PDF en HTML": "PDF を HTML に変換",
        "Transformez votre document PDF en page web HTML": "PDF ドキュメントを HTML ウェブページに変換",
        "Convertissez votre PDF en texte": "PDF をテキストに変換",
        "Extrayez le texte de votre document PDF": "PDF ドキュメントからテキストを抽出",
        "Convertissez votre texte en PDF": "テキストを PDF に変換",
        "Téléchargez un fichier texte ou collez votre contenu directement": "テキストファイルをアップロードするか、内容を直接貼り付け",
        "Sélectionnez votre fichier texte": "テキストファイルを選択",
        "Police": "フォント",
        "Convertissez votre code HTML en PDF": "HTML コードを PDF に変換",
        "Téléchargez un fichier HTML ou collez votre code directement": "HTML ファイルをアップロードするか、コードを直接貼り付け",
        "Sélectionnez votre fichier HTML": "HTML ファイルを選択",
        "Convertissez vos images en PDF": "画像を PDF に変換",
        "Transformez vos images en document PDF": "画像を PDF ドキュメントに変換",
        "Sélectionnez vos images": "画像を選択",
        "Qualité": "品質",
        "Sélectionnez vos fichiers PowerPoint": "PowerPoint ファイルを選択",
        "Convertissez vos fichiers Excel en PDF": "Excel ファイルを PDF に変換",
        "Transformez vos feuilles Excel en documents PDF": "Excel シートを PDF ドキュメントに変換",
        "Sélectionnez vos fichiers Excel": "Excel ファイルを選択",
    },
    
    'ru': {
        "Sélectionnez votre fichier": "Выберите файл",
        "Sélectionner des images": "Выбрать изображения",
        "Sélectionner des fichiers": "Выбрать файлы",
        "Format: numéros séparés par des virgules, plages avec tiret. Ex: \"1,3-5\"": "Формат: номера через запятую, диапазоны через дефис. Пример: \"1,3-5\"",
        "Convertissez votre image en Excel": "Конвертируйте изображение в Excel",
        "Extrayez les tableaux de vos images ou PDF en feuilles Excel": "Извлеките таблицы из изображений или PDF в листы Excel",
        "Convertissez vos fichiers CSV en Excel": "Конвертируйте файлы CSV в Excel",
        "Transformez vos fichiers CSV en feuilles Excel": "Преобразуйте файлы CSV в листы Excel",
        "Sélectionnez vos fichiers CSV": "Выберите файлы CSV",
        "Séparateur": "Разделитель",
        "Créez votre formulaire PDF": "Создайте форму PDF",
        "Sélectionnez votre document": "Выберите документ",
        "Type de formulaire": "Тип формы",
        "Langue du formulaire": "Язык формы",
        "Couleur des champs": "Цвет полей",
        "Style des champs": "Стиль полей",
        "Ajouter des textes indicatifs": "Добавить замещающий текст",
        "Ex: \"Nom\", \"Prénom\"...": "Пример: \"Имя\", \"Фамилия\"...",
        "Marquer les champs obligatoires": "Отметить обязательные поля",
        "Ajoute un astérisque (*) aux champs requis": "Добавляет звездочку (*) к обязательным полям",
        "Signez votre PDF": "Подпишите PDF",
        "Dessinez votre signature": "Нарисуйте подпись",
        "Éditez votre PDF": "Редактируйте PDF",
        "Caviardez votre PDF": "Заретушируйте PDF",
        "Texte à caviarder": "Текст для ретуширования",
        "Pages à traiter": "Страницы для обработки",
        "Plage de pages": "Диапазон страниц",
        "Convertissez votre PDF en HTML": "Конвертируйте PDF в HTML",
        "Transformez votre document PDF en page web HTML": "Преобразуйте документ PDF в веб-страницу HTML",
        "Convertissez votre PDF en texte": "Конвертируйте PDF в текст",
        "Extrayez le texte de votre document PDF": "Извлеките текст из документа PDF",
        "Convertissez votre texte en PDF": "Конвертируйте текст в PDF",
        "Téléchargez un fichier texte ou collez votre contenu directement": "Загрузите текстовый файл или вставьте содержимое напрямую",
        "Sélectionnez votre fichier texte": "Выберите текстовый файл",
        "Police": "Шрифт",
        "Convertissez votre code HTML en PDF": "Конвертируйте HTML-код в PDF",
        "Téléchargez un fichier HTML ou collez votre code directement": "Загрузите HTML-файл или вставьте код напрямую",
        "Sélectionnez votre fichier HTML": "Выберите HTML-файл",
        "Convertissez vos images en PDF": "Конвертируйте изображения в PDF",
        "Transformez vos images en document PDF": "Преобразуйте изображения в документ PDF",
        "Sélectionnez vos images": "Выберите изображения",
        "Qualité": "Качество",
        "Sélectionnez vos fichiers PowerPoint": "Выберите файлы PowerPoint",
        "Convertissez vos fichiers Excel en PDF": "Конвертируйте файлы Excel в PDF",
        "Transformez vos feuilles Excel en documents PDF": "Преобразуйте листы Excel в документы PDF",
        "Sélectionnez vos fichiers Excel": "Выберите файлы Excel",
    }
}

def parse_existing_msgids(po_file):
    """Retourne l'ensemble des msgid existants"""
    existing = set()
    
    if not os.path.exists(po_file):
        return existing
    
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'msgid "(.+?)"\nmsgstr'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for m in matches:
            clean = m.replace('"\n"', '').replace('\\"', '"')
            existing.add(clean)
    except:
        pass
    
    return existing

def add_translations(po_file, lang):
    """Ajoute les traductions manquantes sans doublons"""
    
    if not os.path.exists(po_file):
        print(f"  ❌ {lang}: fichier non trouvé")
        return 0
    
    existing = parse_existing_msgids(po_file)
    
    # Trouver les textes manquants
    missing = {}
    if lang in TRANSLATIONS:
        for text in MISSING_TEXTS:
            if text not in existing:
                missing[text] = TRANSLATIONS[lang].get(text, text)
    
    if not missing:
        return 0
    
    # Ajouter au fichier
    with open(po_file, 'a', encoding='utf-8') as f:
        f.write('\n# ===== TRADUCTIONS MANQUANTES (TOUS TEMPLATES) =====\n\n')
        
        for text, trans in missing.items():
            text_esc = text.replace('"', '\\"')
            trans_esc = trans.replace('"', '\\"')
            f.write(f'msgid "{text_esc}"\n')
            f.write(f'msgstr "{trans_esc}"\n\n')
    
    return len(missing)

def main():
    print("=" * 70)
    print("📝 AJOUT DE TOUTES LES TRADUCTIONS MANQUANTES")
    print("=" * 70)
    
    languages = ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl', 'ar', 'zh', 'ja', 'ru']
    lang_names = {
        'fr': 'Français', 'en': 'Anglais', 'es': 'Espagnol', 'de': 'Allemand',
        'it': 'Italien', 'pt': 'Portugais', 'nl': 'Néerlandais', 'ar': 'Arabe',
        'zh': 'Chinois', 'ja': 'Japonais', 'ru': 'Russe'
    }
    
    total_added = 0
    
    for lang in languages:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if not os.path.exists(po_file):
            print(f"  ❌ {lang}: fichier non trouvé")
            continue
        
        added = add_translations(po_file, lang)
        
        if added > 0:
            print(f"  ✅ {lang_names[lang]} ({lang}): {added} textes ajoutés")
            total_added += added
        else:
            print(f"  ✓ {lang_names[lang]} ({lang}): déjà à jour")
    
    print("=" * 70)
    print(f"✨ Total: {total_added} traductions ajoutées")
    
    if total_added > 0:
        print("\n🔨 Compilation...")
        result = subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Compilation réussie !")
        else:
            print(f"❌ Erreur de compilation")
    
    print(f"\n📊 {len(MISSING_TEXTS)} textes traités pour 11 langues")
    print("\n✨ Terminé !")

if __name__ == "__main__":
    main()