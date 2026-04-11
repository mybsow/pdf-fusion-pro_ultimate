// static/js/cloud/upload.js

class CloudUpload {
    constructor() {
        this.currentProvider = null;
        this.currentPath = '/';
        this.selectedFile = null;
        this.files = [];
        this.init();
    }
    
    init() {
        // Créer le modal s'il n'existe pas
        if (!document.getElementById('cloudFileModal')) {
            this.createModal();
        }
    }
    
    createModal() {
        const modalHtml = `
        <div class="modal fade" id="cloudFileModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-cloud-upload-alt me-2"></i>
                            Importer depuis le cloud
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div id="cloudFileBrowser">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <div id="cloudPath" class="text-muted small">
                                    <i class="fas fa-folder-open me-1"></i>
                                    <span>/</span>
                                </div>
                                <button class="btn btn-sm btn-outline-secondary" id="cloudBackBtn" style="display: none;">
                                    <i class="fas fa-arrow-left me-1"></i>Retour
                                </button>
                            </div>
                            <div id="cloudFileList" class="list-group">
                                <div class="text-center p-4">
                                    <i class="fas fa-spinner fa-spin me-2"></i>
                                    Chargement...
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" id="cloudSelectBtn" disabled>Sélectionner</button>
                    </div>
                </div>
            </div>
        </div>`;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Réattacher les événements
        document.getElementById('cloudBackBtn')?.addEventListener('click', () => this.goBack());
        document.getElementById('cloudSelectBtn')?.addEventListener('click', () => this.selectFile());
    }
    
    async open(provider) {
        this.currentProvider = provider;
        this.currentPath = '/';
        this.selectedFile = null;
        this.files = [];
        
        const modal = new bootstrap.Modal(document.getElementById('cloudFileModal'));
        modal.show();
        
        // Réinitialiser l'interface
        document.getElementById('cloudBackBtn').style.display = 'none';
        document.getElementById('cloudSelectBtn').disabled = true;
        
        await this.loadFiles();
    }
    
    async loadFiles() {
        const container = document.getElementById('cloudFileList');
        container.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin me-2"></i>Chargement...</div>';
        
        try {
            const response = await fetch(`/cloud/files/${this.currentProvider}?path=${encodeURIComponent(this.currentPath)}`);
            
            if (response.status === 401) {
                // Rediriger vers l'authentification
                const authResponse = await fetch(`/cloud/auth/${this.currentProvider}`);
                const data = await authResponse.json();
                window.location.href = data.auth_url;
                return;
            }
            
            if (!response.ok) {
                throw new Error('Erreur de chargement');
            }
            
            const data = await response.json();
            this.files = data.files || [];
            this.displayFiles();
            
        } catch (error) {
            console.error(error);
            container.innerHTML = '<div class="alert alert-danger">Erreur de chargement des fichiers</div>';
        }
    }
    
    displayFiles() {
        const container = document.getElementById('cloudFileList');
        container.innerHTML = '';
        
        // Mettre à jour le chemin
        const pathSpan = document.querySelector('#cloudPath span');
        if (pathSpan) pathSpan.textContent = this.currentPath;
        
        // Afficher/masquer le bouton retour
        document.getElementById('cloudBackBtn').style.display = this.currentPath !== '/' ? 'inline-flex' : 'none';
        
        // Séparer dossiers et fichiers
        const folders = this.files.filter(f => f.type === 'folder');
        const documents = this.files.filter(f => f.type === 'file');
        
        if (this.files.length === 0) {
            container.innerHTML = '<div class="text-center p-4 text-muted">Aucun fichier trouvé</div>';
            return;
        }
        
        // Afficher les dossiers
        folders.forEach(folder => {
            container.appendChild(this.createFileItem(folder, true));
        });
        
        // Afficher les fichiers
        documents.forEach(doc => {
            container.appendChild(this.createFileItem(doc, false));
        });
    }
    
    createFileItem(file, isFolder) {
        const div = document.createElement('div');
        div.className = `list-group-item list-group-item-action ${isFolder ? 'folder-item' : ''}`;
        div.style.cursor = 'pointer';
        
        const icon = isFolder ? 
            '<i class="fas fa-folder text-warning me-3 fa-lg"></i>' : 
            this.getFileIcon(file.name);
        
        const size = isFolder ? '' : `<small class="text-muted ms-2">${this.formatSize(file.size)}</small>`;
        
        div.innerHTML = `
            <div class="d-flex align-items-center">
                ${icon}
                <div class="flex-grow-1">
                    <span class="fw-medium">${this.escapeHtml(file.name)}</span>
                    ${size}
                </div>
                ${isFolder ? '<i class="fas fa-chevron-right text-muted"></i>' : ''}
            </div>
        `;
        
        if (isFolder) {
            div.addEventListener('click', (e) => {
                e.stopPropagation();
                this.currentPath = file.path;
                this.loadFiles();
            });
        } else {
            div.addEventListener('click', (e) => {
                e.stopPropagation();
                // Désélectionner précédent
                document.querySelectorAll('#cloudFileList .list-group-item').forEach(item => {
                    item.classList.remove('active');
                });
                div.classList.add('active');
                this.selectedFile = file;
                document.getElementById('cloudSelectBtn').disabled = false;
            });
        }
        
        return div;
    }
    
    async selectFile() {
        if (!this.selectedFile) return;
        
        const btn = document.getElementById('cloudSelectBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Téléchargement...';
        
        try {
            const response = await fetch(`/cloud/download/${this.currentProvider}?path=${encodeURIComponent(this.selectedFile.path)}`);
            
            if (!response.ok) {
                throw new Error('Erreur de téléchargement');
            }
            
            const blob = await response.blob();
            
            // Créer un fichier à partir du blob
            const file = new File([blob], this.selectedFile.name, { type: blob.type });
            
            // Ajouter au formulaire d'upload
            this.addToUploadForm(file);
            
            // Fermer le modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('cloudFileModal'));
            modal.hide();
            
        } catch (error) {
            console.error(error);
            alert('Erreur lors du téléchargement du fichier');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check me-1"></i>Sélectionner';
        }
    }
    
    addToUploadForm(file) {
        // Ajouter le fichier au formulaire d'upload existant
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {
            const dataTransfer = new DataTransfer();
            
            // Garder les fichiers existants
            if (fileInput.files) {
                for (let f of fileInput.files) {
                    dataTransfer.items.add(f);
                }
            }
            
            // Ajouter le nouveau fichier
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Déclencher l'événement change
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Mettre à jour l'affichage du nom du fichier si présent
            const fileNameSpan = document.querySelector('.file-name span');
            if (fileNameSpan) {
                fileNameSpan.textContent = file.name;
            }
        }
    }
    
    goBack() {
        const parentPath = this.currentPath.split('/').slice(0, -1).join('/') || '/';
        this.currentPath = parentPath;
        this.loadFiles();
    }
    
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            pdf: '<i class="fas fa-file-pdf text-danger me-3 fa-lg"></i>',
            doc: '<i class="fas fa-file-word text-primary me-3 fa-lg"></i>',
            docx: '<i class="fas fa-file-word text-primary me-3 fa-lg"></i>',
            xls: '<i class="fas fa-file-excel text-success me-3 fa-lg"></i>',
            xlsx: '<i class="fas fa-file-excel text-success me-3 fa-lg"></i>',
            ppt: '<i class="fas fa-file-powerpoint text-warning me-3 fa-lg"></i>',
            pptx: '<i class="fas fa-file-powerpoint text-warning me-3 fa-lg"></i>',
            jpg: '<i class="fas fa-file-image text-info me-3 fa-lg"></i>',
            jpeg: '<i class="fas fa-file-image text-info me-3 fa-lg"></i>',
            png: '<i class="fas fa-file-image text-info me-3 fa-lg"></i>',
            gif: '<i class="fas fa-file-image text-info me-3 fa-lg"></i>',
            txt: '<i class="fas fa-file-alt text-secondary me-3 fa-lg"></i>'
        };
        return icons[ext] || '<i class="fas fa-file me-3 fa-lg"></i>';
    }
    
    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialiser l'instance globale
window.cloudUpload = new CloudUpload();