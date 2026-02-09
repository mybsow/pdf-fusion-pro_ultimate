// static/js/components/upload.js

class UploadManager {
    constructor(zoneId, fileInfoId, actionButtonId) {
        this.zone = document.getElementById(zoneId);
        this.fileInfo = document.getElementById(fileInfoId);
        this.actionButton = document.getElementById(actionButtonId);
        this.files = [];

        if (!this.zone) return;

        // Init events
        this.initEvents();
        this.updateButton();
    }

    initEvents() {
        // Click to open file dialog
        this.zone.addEventListener('click', () => {
            const input = this.zone.querySelector('input[type="file"]');
            if (input) input.click();
        });

        // Drag & Drop
        this.zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.zone.classList.add('drag-active');
        });
        this.zone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.zone.classList.remove('drag-active');
        });
        this.zone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.zone.classList.remove('drag-active');
            this.handleFiles(e.dataTransfer.files);
        });

        // Input change
        const input = this.zone.querySelector('input[type="file"]');
        if (input) {
            input.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
                input.value = ''; // reset input
            });
        }
    }

    handleFiles(fileList) {
        Array.from(fileList).forEach(file => {
            // Eviter les doublons
            if (!this.files.some(f => f.name === file.name && f.size === file.size)) {
                this.files.push(file);
            }
        });
        this.updateFileList();
        this.updateButton();
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.updateFileList();
        this.updateButton();
    }

    updateFileList() {
        if (!this.fileInfo) return;
        if (!this.files.length) {
            this.fileInfo.innerHTML = '';
            this.zone.classList.remove('has-file');
            return;
        }

        this.zone.classList.add('has-file');
        this.fileInfo.innerHTML = '<ul class="list-group mt-2">' +
            this.files.map((f, i) => `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${f.name} (${(f.size/1024/1024).toFixed(2)} MB)
                    <button type="button" class="btn-close btn-close-white btn-sm" data-index="${i}"></button>
                </li>
            `).join('') +
            '</ul>';

        // Supprimer un fichier
        this.fileInfo.querySelectorAll('.btn-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(btn.dataset.index);
                this.removeFile(idx);
            });
        });
    }

    updateButton() {
        if (!this.actionButton) return;
        this.actionButton.disabled = !this.files.length;
    }

    getFiles() {
        return this.files;
    }
}

// Initialisation globale
window.uploadManagers = {};
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.upload-zone-pro').forEach(zone => {
        const id = zone.id;
        const infoId = zone.dataset.infoId || id + 'Info';
        const btnId = zone.dataset.btnId || id + 'Button';
        window.uploadManagers[id] = new UploadManager(id, infoId, btnId);
    });
});
