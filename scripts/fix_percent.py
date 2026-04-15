#!/usr/bin/env python3
# scripts/add_cloud_upload_translations.py

import re
import os
from pathlib import Path

# Textes à extraire (clés et valeurs françaises)
CLOUD_TEXTS_FR = {
    'how_to_use': 'Comment utiliser {service}',
    'download_file': 'Téléchargez votre fichier',
    'download_file_desc': 'Depuis {service} vers votre ordinateur',
    'come_back': 'Revenez sur cette page',
    'come_back_desc': "L'onglet de {service} s'est ouvert",
    'use_browse': 'Utilisez le bouton "Parcourir"',
    'use_browse_desc': 'Pour sélectionner le fichier téléchargé',
    'understood': "J'ai compris",
    'cloud_upload_ready': '☁️ Upload cloud prêt - Ouvre les services cloud'
}

# Traductions pour toutes les langues (basées sur les valeurs françaises)
TRANSLATIONS = {
    'fr': {
        'Comment utiliser {service}': 'Comment utiliser {service}',
        'Téléchargez votre fichier': 'Téléchargez votre fichier',
        'Depuis {service} vers votre ordinateur': 'Depuis {service} vers votre ordinateur',
        'Revenez sur cette page': 'Revenez sur cette page',
        "L'onglet de {service} s'est ouvert": "L'onglet de {service} s'est ouvert",
        'Utilisez le bouton "Parcourir"': 'Utilisez le bouton "Parcourir"',
        'Pour sélectionner le fichier téléchargé': 'Pour sélectionner le fichier téléchargé',
        "J'ai compris": "J'ai compris",
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Upload cloud prêt - Ouvre les services cloud'
    },
    'en': {
        'Comment utiliser {service}': 'How to use {service}',
        'Téléchargez votre fichier': 'Download your file',
        'Depuis {service} vers votre ordinateur': 'From {service} to your computer',
        'Revenez sur cette page': 'Come back to this page',
        "L'onglet de {service} s'est ouvert": 'The {service} tab has opened',
        'Utilisez le bouton "Parcourir"': 'Use the "Browse" button',
        'Pour sélectionner le fichier téléchargé': 'To select the downloaded file',
        "J'ai compris": 'I understand',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Cloud upload ready - Opens cloud services'
    },
    'es': {
        'Comment utiliser {service}': 'Cómo usar {service}',
        'Téléchargez votre fichier': 'Descargue su archivo',
        'Depuis {service} vers votre ordinateur': 'Desde {service} a su computadora',
        'Revenez sur cette page': 'Vuelva a esta página',
        "L'onglet de {service} s'est ouvert": 'La pestaña de {service} se ha abierto',
        'Utilisez le bouton "Parcourir"': 'Use el botón "Examinar"',
        'Pour sélectionner le fichier téléchargé': 'Para seleccionar el archivo descargado',
        "J'ai compris": 'He entendido',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Carga en la nube lista - Abre servicios en la nube'
    },
    'de': {
        'Comment utiliser {service}': 'Wie man {service} benutzt',
        'Téléchargez votre fichier': 'Laden Sie Ihre Datei herunter',
        'Depuis {service} vers votre ordinateur': 'Von {service} auf Ihren Computer',
        'Revenez sur cette page': 'Kehren Sie zu dieser Seite zurück',
        "L'onglet de {service} s'est ouvert": 'Der Tab von {service} wurde geöffnet',
        'Utilisez le bouton "Parcourir"': 'Verwenden Sie die Schaltfläche "Durchsuchen"',
        'Pour sélectionner le fichier téléchargé': 'Um die heruntergeladene Datei auszuwählen',
        "J'ai compris": 'Ich habe verstanden',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Cloud-Upload bereit - Öffnet Cloud-Dienste'
    },
    'it': {
        'Comment utiliser {service}': 'Come usare {service}',
        'Téléchargez votre fichier': 'Scarica il tuo file',
        'Depuis {service} vers votre ordinateur': 'Da {service} al tuo computer',
        'Revenez sur cette page': 'Torna a questa pagina',
        "L'onglet de {service} s'est ouvert": 'La scheda di {service} è stata aperta',
        'Utilisez le bouton "Parcourir"': 'Usa il pulsante "Sfoglia"',
        'Pour sélectionner le fichier téléchargé': 'Per selezionare il file scaricato',
        "J'ai compris": 'Ho capito',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Upload cloud pronto - Apre i servizi cloud'
    },
    'pt': {
        'Comment utiliser {service}': 'Como usar {service}',
        'Téléchargez votre fichier': 'Baixe seu arquivo',
        'Depuis {service} vers votre ordinateur': 'De {service} para o seu computador',
        'Revenez sur cette page': 'Volte para esta página',
        "L'onglet de {service} s'est ouvert": 'A aba do {service} foi aberta',
        'Utilisez le bouton "Parcourir"': 'Use o botão "Procurar"',
        'Pour sélectionner le fichier téléchargé': 'Para selecionar o arquivo baixado',
        "J'ai compris": 'Eu entendi',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Upload na nuvem pronto - Abre serviços em nuvem'
    },
    'nl': {
        'Comment utiliser {service}': 'Hoe {service} te gebruiken',
        'Téléchargez votre fichier': 'Download uw bestand',
        'Depuis {service} vers votre ordinateur': 'Van {service} naar uw computer',
        'Revenez sur cette page': 'Kom terug naar deze pagina',
        "L'onglet de {service} s'est ouvert": 'Het tabblad van {service} is geopend',
        'Utilisez le bouton "Parcourir"': 'Gebruik de knop "Bladeren"',
        'Pour sélectionner le fichier téléchargé': 'Om het gedownloade bestand te selecteren',
        "J'ai compris": 'Ik begrijp het',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Cloud-upload klaar - Opent cloudservices'
    },
    'ar': {
        'Comment utiliser {service}': 'كيفية استخدام {service}',
        'Téléchargez votre fichier': 'قم بتنزيل ملفك',
        'Depuis {service} vers votre ordinateur': 'من {service} إلى جهاز الكمبيوتر الخاص بك',
        'Revenez sur cette page': 'عد إلى هذه الصفحة',
        "L'onglet de {service} s'est ouvert": 'تم فتح علامة تبويب {service}',
        'Utilisez le bouton "Parcourir"': 'استخدم زر "تصفح"',
        'Pour sélectionner le fichier téléchargé': 'لتحديد الملف الذي تم تنزيله',
        "J'ai compris": 'فهمت',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ التحميل السحابي جاهز - يفتح الخدمات السحابية'
    },
    'zh': {
        'Comment utiliser {service}': '如何使用{service}',
        'Téléchargez votre fichier': '下载您的文件',
        'Depuis {service} vers votre ordinateur': '从{service}到您的计算机',
        'Revenez sur cette page': '返回此页面',
        "L'onglet de {service} s'est ouvert": '{service}标签页已打开',
        'Utilisez le bouton "Parcourir"': '使用"浏览"按钮',
        'Pour sélectionner le fichier téléchargé': '选择下载的文件',
        "J'ai compris": '我明白了',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ 云上传就绪 - 打开云服务'
    },
    'ja': {
        'Comment utiliser {service}': '{service}の使い方',
        'Téléchargez votre fichier': 'ファイルをダウンロード',
        'Depuis {service} vers votre ordinateur': '{service}からコンピュータへ',
        'Revenez sur cette page': 'このページに戻る',
        "L'onglet de {service} s'est ouvert": '{service}のタブが開きました',
        'Utilisez le bouton "Parcourir"': '「参照」ボタンを使用',
        'Pour sélectionner le fichier téléchargé': 'ダウンロードしたファイルを選択',
        "J'ai compris": '理解しました',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ クラウドアップロード準備完了 - クラウドサービスを開く'
    },
    'ru': {
        'Comment utiliser {service}': 'Как использовать {service}',
        'Téléchargez votre fichier': 'Скачайте ваш файл',
        'Depuis {service} vers votre ordinateur': 'С {service} на ваш компьютер',
        'Revenez sur cette page': 'Вернитесь на эту страницу',
        "L'onglet de {service} s'est ouvert": 'Вкладка {service} открыта',
        'Utilisez le bouton "Parcourir"': 'Используйте кнопку "Обзор"',
        'Pour sélectionner le fichier téléchargé': 'Чтобы выбрать загруженный файл',
        "J'ai compris": 'Я понял',
        '☁️ Upload cloud prêt - Ouvre les services cloud': '☁️ Загрузка в облако готова - Открывает облачные сервисы'
    }
}

def parse_existing_msgids(po_file):
    """Récupère tous les msgid existants"""
    existing = set()
    if not os.path.exists(po_file):
        return existing
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = r'msgid "(.+?)"\nmsgstr'
        matches = re.findall(pattern, content, re.DOTALL)
        for m in matches:
            clean = m.replace('"\n"', '')
            existing.add(clean)
    except:
        pass
    return existing

def add_translations_to_po(po_file, translations, lang):
    """Ajoute les traductions sans doublons"""
    existing = parse_existing_msgids(po_file)
    new_entries = {k: v for k, v in translations.items() if k not in existing}
    
    if not new_entries:
        return 0
    
    with open(po_file, 'a', encoding='utf-8') as f:
        f.write('\n# ===== CLOUD UPLOAD JAVASCRIPT =====\n')
        f.write('#: static/js/cloud/cloud-upload.js\n\n')
        for msgid, msgstr in new_entries.items():
            msgid_esc = msgid.replace('"', '\\"')
            msgstr_esc = msgstr.replace('"', '\\"')
            f.write(f'msgid "{msgid_esc}"\n')
            f.write(f'msgstr "{msgstr_esc}"\n\n')
    return len(new_entries)

def main():
    print("🌍 Ajout des traductions cloud-upload.js à toutes les langues")
    print("=" * 60)
    
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
        
        if lang in TRANSLATIONS:
            added = add_translations_to_po(po_file, TRANSLATIONS[lang], lang)
            if added > 0:
                print(f"  ✅ {lang_names[lang]} ({lang}): {added} traductions ajoutées")
                total_added += added
            else:
                print(f"  ✓ {lang_names[lang]} ({lang}): déjà à jour")
    
    print("=" * 60)
    print(f"✨ Total: {total_added} traductions ajoutées")
    
    if total_added > 0:
        print("\n🔨 Recompilation...")
        import subprocess
        result = subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Compilation réussie !")
        else:
            print("❌ Erreur de compilation")
    
    # Vérification
    print("\n📊 Vérification :")
    for lang in languages[:5]:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_file):
            existing = parse_existing_msgids(po_file)
            cloud_texts = [t for t in TRANSLATIONS['fr'].keys() if t in existing]
            print(f"  {lang}: {len(cloud_texts)}/9 textes cloud présents")

if __name__ == "__main__":
    main()