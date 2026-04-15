// static/js/cloud/upload.js - Version compatible Babel

(function() {
    if (window.cloudUpload) return;

    // Fonction de traduction (fallback)
    const t = (window.i18n && window.i18n.t) || function(key, params = {}) {
        // Fallback en français - CES CHAÎNES SERONT REMPLACÉES PAR LE BACKEND
        const fallbacks = {
            'how_to_use': 'Comment utiliser {service}',
            'download_file': 'Téléchargez votre fichier',
            'download_file_desc': 'Depuis {service} vers votre ordinateur',
            'come_back': 'Revenez sur cette page',
            'come_back_desc': "L'onglet de {service} s'est ouvert",
            'use_browse': 'Utilisez le bouton "Parcourir"',
            'use_browse_desc': 'Pour sélectionner le fichier téléchargé',
            'understood': "J'ai compris",
            'cloud_upload_ready': '☁️ Upload cloud prêt - Ouvre les services cloud'
        };
        let text = fallbacks[key] || key;
        Object.keys(params).forEach(p => {
            text = text.replace(`{${p}}`, params[p]);
        });
        return text;
    };

    // Pour l'extraction Babel - Ces lignes sont ignorées à l'exécution mais lues par Babel
    const _extract = [
        t('how_to_use', { service: '' }),
        t('download_file'),
        t('download_file_desc', { service: '' }),
        t('come_back'),
        t('come_back_desc', { service: '' }),
        t('use_browse'),
        t('use_browse_desc'),
        t('understood'),
        t('cloud_upload_ready')
    ];

    const CLOUD_SERVICES = [
        { id: 'google', name: 'Google Drive', url: 'https://drive.google.com', icon: 'fab fa-google-drive', color: '#4285F4' },
        { id: 'onedrive', name: 'OneDrive', url: 'https://onedrive.live.com', icon: 'fab fa-microsoft', color: '#0078D4' },
        { id: 'dropbox', name: 'Dropbox', url: 'https://www.dropbox.com', icon: 'fab fa-dropbox', color: '#0061FF' },
        { id: 'icloud', name: 'iCloud', url: 'https://www.icloud.com', icon: 'fab fa-apple', color: '#555555' },
        { id: 'box', name: 'Box', url: 'https://www.box.com', icon: 'fas fa-box', color: '#0061D5' },
        { id: 'pcloud', name: 'pCloud', url: 'https://www.pcloud.com', icon: 'fas fa-cloud', color: '#FF6B00' }
    ];

    window.cloudUpload = {
        open: function(providerId) {
            const service = CLOUD_SERVICES.find(s => s.id === providerId);
            if (service) {
                window.open(service.url, '_blank');
                this.showInstructions(service.name);
            }
        },
        
        showInstructions: function(serviceName) {
            const oldModal = document.getElementById('cloudInstructionsModal');
            if (oldModal) oldModal.remove();
            
            const modal = document.createElement('div');
            modal.id = 'cloudInstructionsModal';
            modal.style.cssText = `
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10001;
                animation: fadeIn 0.2s ease;
            `;
            
            modal.innerHTML = `
                <div style="
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    max-width: 450px;
                    width: 90%;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    animation: slideUp 0.3s ease;
                ">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <i class="fas fa-cloud-download-alt" style="font-size: 48px; color: #4285F4;"></i>
                    </div>
                    <h4 style="margin-bottom: 15px; text-align: center;">
                        <i class="fas fa-info-circle text-primary me-2"></i>
                        ${t('how_to_use', { service: serviceName })}
                    </h4>
                    <div style="background: #f0f7ff; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                        <ol style="margin: 0; padding-left: 20px; color: #2c3e50;">
                            <li style="margin-bottom: 12px;">
                                <strong>${t('download_file')}</strong><br>
                                <span style="font-size: 14px; color: #6c757d;">${t('download_file_desc', { service: serviceName })}</span>
                            </li>
                            <li style="margin-bottom: 12px;">
                                <strong>${t('come_back')}</strong><br>
                                <span style="font-size: 14px; color: #6c757d;">${t('come_back_desc', { service: serviceName })}</span>
                            </li>
                            <li>
                                <strong>${t('use_browse')}</strong><br>
                                <span style="font-size: 14px; color: #6c757d;">${t('use_browse_desc')}</span>
                            </li>
                        </ol>
                    </div>
                    <div style="display: flex; gap: 10px; justify-content: center;">
                        <button onclick="this.closest('#cloudInstructionsModal').remove()" style="
                            background: #4285F4;
                            color: white;
                            border: none;
                            padding: 12px 30px;
                            border-radius: 50px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.3s;
                        " onmouseover="this.style.background='#3367d6'" onmouseout="this.style.background='#4285F4'">
                            ${t('understood')}
                        </button>
                    </div>
                </div>
            `;
            
            // Animations...
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
            `;
            document.head.appendChild(style);
            document.body.appendChild(modal);
            
            modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
            
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    modal.remove();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
        },
        
        getServices: function() {
            return CLOUD_SERVICES;
        }
    };

    console.log(t('cloud_upload_ready'));
})();