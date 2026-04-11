// static/js/cloud/upload.js
// Version simplifiée - Ouvre simplement les URLs des clouds

(function() {
    // Configuration des providers cloud
    const CLOUD_URLS = {
        google: 'https://drive.google.com',
        onedrive: 'https://onedrive.live.com',
        dropbox: 'https://www.dropbox.com/login',
        icloud: 'https://www.icloud.com'
    };

    // Créer l'objet global cloudUpload
    window.cloudUpload = {
        /**
         * Ouvre le service cloud dans un nouvel onglet
         * @param {string} provider - Nom du provider ('google', 'onedrive', 'dropbox', 'icloud')
         */
        open: function(provider) {
            const url = CLOUD_URLS[provider];
            if (url) {
                window.open(url, '_blank');
                this.showHelperMessage(provider);
            } else {
                console.warn('Provider non supporté:', provider);
            }
        },

        /**
         * Affiche un message d'aide dans la modal
         * @param {string} provider - Nom du provider
         */
        showHelperMessage: function(provider) {
            // Vérifier si la modal existe déjà
            let modal = document.getElementById('cloudHelperModal');
            
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'cloudHelperModal';
                modal.className = 'modal fade';
                modal.tabIndex = -1;
                modal.innerHTML = `
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-cloud-upload-alt me-2"></i>
                                    ${this.getProviderName(provider)}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="text-center">
                                    <i class="fas fa-download fa-3x text-primary mb-3"></i>
                                    <p><strong>Comment importer votre fichier :</strong></p>
                                    <ol class="text-start">
                                        <li>Connectez-vous à votre compte ${this.getProviderName(provider)}</li>
                                        <li>Téléchargez le fichier que vous souhaitez convertir</li>
                                        <li>Revenez sur cette page</li>
                                        <li>Cliquez sur "Parcourir" pour sélectionner le fichier téléchargé</li>
                                    </ol>
                                    <div class="alert alert-info mt-3">
                                        <i class="fas fa-info-circle me-2"></i>
                                        <small>Le fichier sera traité localement et supprimé automatiquement après conversion.</small>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                                <button type="button" class="btn btn-primary" onclick="document.querySelector('input[type=\\\\'file\\\\']')?.click(); bootstrap.Modal.getInstance(document.getElementById('cloudHelperModal')).hide();">
                                    <i class="fas fa-folder-open me-1"></i>Parcourir
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            
            // Mettre à jour le titre du modal
            const titleEl = modal.querySelector('.modal-title');
            if (titleEl) {
                titleEl.innerHTML = `<i class="fas fa-cloud-upload-alt me-2"></i>${this.getProviderName(provider)}`;
            }
            
            // Afficher le modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        },

        /**
         * Retourne le nom du provider
         */
        getProviderName: function(provider) {
            const names = {
                google: 'Google Drive',
                onedrive: 'OneDrive',
                dropbox: 'Dropbox',
                icloud: 'iCloud'
            };
            return names[provider] || provider;
        }
    };
    
    console.log('☁️ Cloud upload ready - URLs only mode');
})();