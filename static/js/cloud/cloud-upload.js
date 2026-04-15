// static/js/cloud/upload.js - Version avec message clair

(function() {
    if (window.cloudUpload) return;

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
                // Ouvrir dans un nouvel onglet
                window.open(service.url, '_blank');
                
                // Afficher un message explicatif
                this.showInstructions(service.name);
            }
        },
        
        showInstructions: function(serviceName) {
            // Supprimer l'ancien modal s'il existe
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
                        Comment utiliser ${serviceName}
                    </h4>
                    <div style="background: #f0f7ff; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                        <ol style="margin: 0; padding-left: 20px; color: #2c3e50;">
                            <li style="margin-bottom: 12px;">
                                <strong>Téléchargez votre fichier</strong><br>
                                <span style="font-size: 14px; color: #6c757d;">Depuis ${serviceName} vers votre ordinateur</span>
                            </li>
                            <li style="margin-bottom: 12px;">
                                <strong>Revenez sur cette page</strong><br>
                                <span style="font-size: 14px; color: #6c757d;">L'onglet de ${serviceName} s'est ouvert</span>
                            </li>
                            <li>
                                <strong>Utilisez le bouton "Parcourir"</strong><br>
                                <span style="font-size: 14px; color: #6c757d;">Pour sélectionner le fichier téléchargé</span>
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
                            J'ai compris
                        </button>
                    </div>
                </div>
            `;
            
            // Ajouter les animations
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(modal);
            
            // Fermer en cliquant à l'extérieur
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.remove();
            });
            
            // Fermer avec Escape
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

    // En bas du fichier, après window.cloudUpload = { ... }
    console.log('✅ cloudUpload initialisé', Object.keys(window.cloudUpload));
    
    console.log('☁️ Cloud upload ready - Ouvre les services cloud');
})();