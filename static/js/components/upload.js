// static/js/components/upload.js

class UploadManager {
    constructor(uploadZoneId, fileInputId, fileListId, actionButtonId, maxFiles = 10) {
        this.uploadZone = document.getElementById(uploadZoneId);
        this.fileInput = document.getElementById(fileInputId);
        this.fileListContainer = document.getElementById(fileListId);
        this.actionButton = document.getElementById(actionButtonId);
        this.maxFiles = maxFiles;
        this.files = [];

        this.init();
    }

    init() {
        if (!this.uploadZone || !this.fileInput) return;

        // Click pour ouvrir le file picker
        this.uploadZone.addEventListener('click', () => this.fileInput.click());

        // Drag & Drop events
        ['dragenter', 'dragover'].forEach(ev => {
            this.uploadZone.addEventListener(ev, e => {
                e.preventDefault();
                e.stopPropagation();
                this.uploadZone.classList.add('drag-active');
            });
        });

        ['dragleave', 'drop'].forEach(ev => {
            this.uploadZone.addEventListener(ev, e => {
                e.preventDefault();
                e.stopPropagation();
                this.uploadZone.classList.remove('drag-active');
            });
        });

        this.uploadZone.addEventListener('drop', e => {
            const dt = e.dataTransfer;
            if (dt && dt.files) {
                this.handleFiles(dt.files);
            }
        });

        // Changement via file input
        this.fileInput.addEventListener('change', e => {
            this.handleFiles(e.target.files);
        });

        this.renderFileList();
    }

    handleFiles(fileList) {
        const newFiles = Array.from(fileList);

        // Limite du nombre de fichiers
        if (this.files.length + newFiles.length > this.maxFiles) {
            alert(`Vous pouvez charger au maximum ${this.maxFiles} fichiers.`);
            return;
        }

        newFiles.forEach(file => {
            // Éviter les doublons par nom et taille
            if (!this.files.some(f => f.name === file.name && f.size === file.size)) {
                this.files.push(file);
            }
        });

        this.renderFileList();
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.renderFileList();
    }

    renderFileList() {
        if (!this.fileListContainer) return;

        this.fileListContainer.innerHTML = '';

        if (this.files.length === 0) {
            this.uploadZone.classList.remove('has-file');
            this.actionButton.disabled = true;
            return;
        }

        this.uploadZone.classList.add('has-file');
        this.actionButton.disabled = false;

        const ul = document.createElement('ul');
        ul.className = 'list-group mt-3';

        this.files.forEach((file, idx) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            // Nom et taille
            const nameSpan = document.createElement('span');
            nameSpan.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;

            // Bouton supprimer
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-sm btn-outline-danger';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';
            removeBtn.addEventListener('click', () => this.removeFile(idx));

            li.appendChild(nameSpan);
            li.appendChild(removeBtn);
            ul.appendChild(li);
        });

        this.fileListContainer.appendChild(ul);
    }

    getFiles() {
        return this.files;
    }

    reset() {
        this.files = [];
        this.fileInput.value = '';
        this.renderFileList();
    }
}

// =====================
// Initialisation pour tous les outils
// =====================
document.addEventListener('DOMContentLoaded', () => {
    const tools = [
        {uploadZone: 'mergeUploadZone', fileInput: 'mergeFileInput', fileList: 'mergeFileInfo', actionButton: 'mergeButton'},
        {uploadZone: 'splitUploadZone', fileInput: 'splitFileInput', fileList: 'splitFileInfo', actionButton: 'splitButton'},
        {uploadZone: 'compressUploadZone', fileInput: 'compressFileInput', fileList: 'compressFileInfo', actionButton: 'compressButton'},
        {uploadZone: 'rotateUploadZone', fileInput: 'rotateFileInput', fileList: 'rotateFileInfo', actionButton: 'rotateButton'},
    ];

    window.uploadManagers = {};

    tools.forEach(tool => {
        window.uploadManagers[tool.uploadZone] = new UploadManager(
            tool.uploadZone,
            tool.fileInput,
            tool.fileList,
            tool.actionButton
        );
    });
});
