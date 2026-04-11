// static/js/cloud/upload.js

(function() {
    // Éviter le double chargement
    if (window.cloudUpload) {
        console.log('☁️ Cloud upload already loaded');
        return;
    }
    
    // Configuration des URLs des services cloud
    const CLOUD_SERVICES = {
        google: {
            name: 'Google Drive',
            url: 'https://drive.google.com',
            icon: 'fab fa-google-drive'
        },
        onedrive: {
            name: 'OneDrive',
            url: 'https://onedrive.live.com',
            icon: 'fab fa-microsoft'
        },
        dropbox: {
            name: 'Dropbox',
            url: 'https://www.dropbox.com',
            icon: 'fab fa-dropbox'
        },
        icloud: {
            name: 'iCloud',
            url: 'https://www.icloud.com',
            icon: 'fab fa-apple'
        },
        box: {
            name: 'Box',
            url: 'https://www.box.com',
            icon: 'fas fa-box'
        },
        pcloud: {
            name: 'pCloud',
            url: 'https://www.pcloud.com',
            icon: 'fas fa-cloud'
        }
    };
    
    window.cloudUpload = {
        open: function(provider) {
            console.log('Cloud upload clicked:', provider);
            const service = CLOUD_SERVICES[provider];
            if (service) {
                window.open(service.url, '_blank');
                alert(`📁 ${service.name}\n\n1. Connectez-vous à votre compte\n2. Téléchargez le fichier souhaité\n3. Revenez ici et cliquez sur "Parcourir" pour le sélectionner`);
            } else {
                console.error('Service non trouvé:', provider);
            }
        }
    };
    
    console.log('☁️ Cloud upload ready - ' + Object.keys(CLOUD_SERVICES).length + ' services');
})();