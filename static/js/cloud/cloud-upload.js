// static/js/cloud/upload.js - Version avec fallback par langue

(function() {
    if (window.cloudUpload) return;

    // Détecter la langue de la page
    const htmlLang = document.documentElement.lang || 'fr';
    
    // Traductions par langue (fallback)
    const TRANSLATIONS_BY_LANG = {
        'fr': {
            'how_to_use': 'Comment utiliser {service}',
            'download_file': 'Téléchargez votre fichier',
            'download_file_desc': 'Depuis {service} vers votre ordinateur',
            'come_back': 'Revenez sur cette page',
            'come_back_desc': "L'onglet de {service} s'est ouvert",
            'use_browse': 'Utilisez le bouton "Parcourir"',
            'use_browse_desc': 'Pour sélectionner le fichier téléchargé',
            'understood': "J'ai compris",
            'cloud_upload_ready': '☁️ Upload cloud prêt - Ouvre les services cloud'
        },
        'en': {
            'how_to_use': 'How to use {service}',
            'download_file': 'Download your file',
            'download_file_desc': 'From {service} to your computer',
            'come_back': 'Come back to this page',
            'come_back_desc': 'The {service} tab has opened',
            'use_browse': 'Use the "Browse" button',
            'use_browse_desc': 'To select the downloaded file',
            'understood': 'I understand',
            'cloud_upload_ready': '☁️ Cloud upload ready - Opens cloud services'
        },
        'es': {
            'how_to_use': 'Cómo usar {service}',
            'download_file': 'Descargue su archivo',
            'download_file_desc': 'Desde {service} a su computadora',
            'come_back': 'Vuelva a esta página',
            'come_back_desc': 'La pestaña de {service} se ha abierto',
            'use_browse': 'Use el botón "Examinar"',
            'use_browse_desc': 'Para seleccionar el archivo descargado',
            'understood': 'He entendido',
            'cloud_upload_ready': '☁️ Carga en la nube lista - Abre servicios en la nube'
        },
        'de': {
            'how_to_use': 'Wie man {service} benutzt',
            'download_file': 'Laden Sie Ihre Datei herunter',
            'download_file_desc': 'Von {service} auf Ihren Computer',
            'come_back': 'Kehren Sie zu dieser Seite zurück',
            'come_back_desc': 'Der Tab von {service} wurde geöffnet',
            'use_browse': 'Verwenden Sie die Schaltfläche "Durchsuchen"',
            'use_browse_desc': 'Um die heruntergeladene Datei auszuwählen',
            'understood': 'Ich habe verstanden',
            'cloud_upload_ready': '☁️ Cloud-Upload bereit - Öffnet Cloud-Dienste'
        },
        'it': {
            'how_to_use': 'Come usare {service}',
            'download_file': 'Scarica il tuo file',
            'download_file_desc': 'Da {service} al tuo computer',
            'come_back': 'Torna a questa pagina',
            'come_back_desc': 'La scheda di {service} è stata aperta',
            'use_browse': 'Usa il pulsante "Sfoglia"',
            'use_browse_desc': 'Per selezionare il file scaricato',
            'understood': 'Ho capito',
            'cloud_upload_ready': '☁️ Upload cloud pronto - Apre i servizi cloud'
        },
        'pt': {
            'how_to_use': 'Como usar {service}',
            'download_file': 'Baixe seu arquivo',
            'download_file_desc': 'De {service} para o seu computador',
            'come_back': 'Volte para esta página',
            'come_back_desc': 'A aba do {service} foi aberta',
            'use_browse': 'Use o botão "Procurar"',
            'use_browse_desc': 'Para selecionar o arquivo baixado',
            'understood': 'Eu entendi',
            'cloud_upload_ready': '☁️ Upload na nuvem pronto - Abre serviços em nuvem'
        },
        'nl': {
            'how_to_use': 'Hoe {service} te gebruiken',
            'download_file': 'Download uw bestand',
            'download_file_desc': 'Van {service} naar uw computer',
            'come_back': 'Kom terug naar deze pagina',
            'come_back_desc': 'Het tabblad van {service} is geopend',
            'use_browse': 'Gebruik de knop "Bladeren"',
            'use_browse_desc': 'Om het gedownloade bestand te selecteren',
            'understood': 'Ik begrijp het',
            'cloud_upload_ready': '☁️ Cloud-upload klaar - Opent cloudservices'
        },
        'ar': {
            'how_to_use': 'كيفية استخدام {service}',
            'download_file': 'قم بتنزيل ملفك',
            'download_file_desc': 'من {service} إلى جهاز الكمبيوتر الخاص بك',
            'come_back': 'عد إلى هذه الصفحة',
            'come_back_desc': 'تم فتح علامة تبويب {service}',
            'use_browse': 'استخدم زر "تصفح"',
            'use_browse_desc': 'لتحديد الملف الذي تم تنزيله',
            'understood': 'فهمت',
            'cloud_upload_ready': '☁️ التحميل السحابي جاهز - يفتح الخدمات السحابية'
        },
        'zh': {
            'how_to_use': '如何使用{service}',
            'download_file': '下载您的文件',
            'download_file_desc': '从{service}到您的计算机',
            'come_back': '返回此页面',
            'come_back_desc': '{service}标签页已打开',
            'use_browse': '使用"浏览"按钮',
            'use_browse_desc': '选择下载的文件',
            'understood': '我明白了',
            'cloud_upload_ready': '☁️ 云上传就绪 - 打开云服务'
        },
        'ja': {
            'how_to_use': '{service}の使い方',
            'download_file': 'ファイルをダウンロード',
            'download_file_desc': '{service}からコンピュータへ',
            'come_back': 'このページに戻る',
            'come_back_desc': '{service}のタブが開きました',
            'use_browse': '「参照」ボタンを使用',
            'use_browse_desc': 'ダウンロードしたファイルを選択',
            'understood': '理解しました',
            'cloud_upload_ready': '☁️ クラウドアップロード準備完了 - クラウドサービスを開く'
        },
        'ru': {
            'how_to_use': 'Как использовать {service}',
            'download_file': 'Скачайте ваш файл',
            'download_file_desc': 'С {service} на ваш компьютер',
            'come_back': 'Вернитесь на эту страницу',
            'come_back_desc': 'Вкладка {service} открыта',
            'use_browse': 'Используйте кнопку "Обзор"',
            'use_browse_desc': 'Чтобы выбрать загруженный файл',
            'understood': 'Я понял',
            'cloud_upload_ready': '☁️ Загрузка в облако готова - Открывает облачные сервисы'
        }
    };

    // Essayer de récupérer les traductions depuis l'élément caché
    const i18nEl = document.getElementById('js-i18n-cloud');
    let translations = TRANSLATIONS_BY_LANG[htmlLang] || TRANSLATIONS_BY_LANG['fr'];
    
    // Si l'élément existe, utiliser ses données (prioritaires)
    if (i18nEl) {
        translations = {
            'how_to_use': i18nEl.dataset.howToUse || translations.how_to_use,
            'download_file': i18nEl.dataset.downloadFile || translations.download_file,
            'download_file_desc': i18nEl.dataset.downloadFileDesc || translations.download_file_desc,
            'come_back': i18nEl.dataset.comeBack || translations.come_back,
            'come_back_desc': i18nEl.dataset.comeBackDesc || translations.come_back_desc,
            'use_browse': i18nEl.dataset.useBrowse || translations.use_browse,
            'use_browse_desc': i18nEl.dataset.useBrowseDesc || translations.use_browse_desc,
            'understood': i18nEl.dataset.understood || translations.understood,
            'cloud_upload_ready': i18nEl.dataset.cloudReady || translations.cloud_upload_ready
        };
    }

    // Fonction de traduction
    const t = function(key, params = {}) {
        let text = translations[key] || key;
        Object.keys(params).forEach(p => {
            text = text.replace(`{${p}}`, params[p]);
        });
        return text;
    };

    // ... reste du code (CLOUD_SERVICES, window.cloudUpload, etc.) ...
})();