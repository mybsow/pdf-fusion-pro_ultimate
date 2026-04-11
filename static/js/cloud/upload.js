// static/js/cloud/upload.js - Version moderne et pro

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
                window.open(service.url, '_blank');
                this.showToast(service.name);
            }
        },
        
        showToast: function(serviceName) {
            let toast = document.getElementById('cloudToast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'cloudToast';
                toast.className = 'cloud-toast';
                toast.innerHTML = `
                    <div class="cloud-toast-content">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <div>
                            <strong>${serviceName}</strong>
                            <p>Téléchargez votre fichier puis utilisez "Parcourir"</p>
                        </div>
                    </div>
                `;
                document.body.appendChild(toast);
                
                // Style du toast
                const style = document.createElement('style');
                style.textContent = `
                    .cloud-toast {
                        position: fixed;
                        bottom: 30px;
                        right: 30px;
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                        padding: 16px 24px;
                        z-index: 10000;
                        transform: translateX(400px);
                        transition: transform 0.3s ease;
                        border-left: 4px solid #4285F4;
                        max-width: 350px;
                    }
                    .cloud-toast.show {
                        transform: translateX(0);
                    }
                    .cloud-toast-content {
                        display: flex;
                        align-items: center;
                        gap: 15px;
                    }
                    .cloud-toast-content i {
                        font-size: 28px;
                        color: #4285F4;
                    }
                    .cloud-toast-content strong {
                        display: block;
                        margin-bottom: 4px;
                        color: #2c3e50;
                    }
                    .cloud-toast-content p {
                        margin: 0;
                        font-size: 13px;
                        color: #6c757d;
                    }
                `;
                document.head.appendChild(style);
            }
            
            toast.querySelector('strong').textContent = serviceName;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 4000);
        },
        
        getServices: function() {
            return CLOUD_SERVICES;
        }
    };
    
    console.log('☁️ Cloud upload ready');
})();