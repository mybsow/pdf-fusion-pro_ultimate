// static/js/components/upload.js

class UploadManager {
    constructor(zoneId, fileInfoId, actionButtonId, previewId) {
        this.zone = document.getElementById(zoneId);
        this.fileInfo = document.getElementById(fileInfoId);
        this.preview = previewId ? document.getElementById(previewId) : null;
        this.actionButton = document.getElementById(actionButtonId);
        this.files = [];

        if (!this.zone) return;

        this.initEvents();
        this.updateButton();
    }

    initEvents() {
        // Click pour ouvrir le file picker
        this.zone.addEventListener('click', () => {
            const input = this.zone.querySelector('input[type="file"]');
            if (input) input.click();
        });

        // Drag & Drop
        this.zone.addEventListener('dragover', e => {
            e.preventDefault();
            this.zone.classList.add('drag-active');
        });
        this.zone.addEventListener('dragleave', e => {
            e.preventDefault();
            this.zone.classList.remove('drag-active');
        });
        this.zone.addEventListener('drop', e => {
            e.preventDefault();
            this.zone.classList.remove('drag-active');
            this.handleFiles(e.dataTransfer.files);
        });

        // Input change
        const input = this.zone.querySelector('input[type="file"]');
        if (input) {
            input.addEventListener('change', e => {
                this.handleFiles(e.target.files);
                input.value = '';
            });
        }
    }

    handleFiles(fileList) {
        Array.from(fileList).forEach(file => {
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
            if (this.preview) this.preview.innerHTML = '';
            this.zone.classList.remove('has-file');
            return;
        }

        this.zone.classList.add('has-file');

        // Liste
        this.fileInfo.innerHTML = '<ul class="list-group mt-2">' +
            this.files.map((f, i) => `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${f.name} (${(f.size / 1024 / 1024).toFixed(2)} MB)
                    <button type="button" class="btn-close btn-close-white btn-sm" data-index="${i}"></button>
                </li>
            `).join('') + '</ul>';

        this.fileInfo.querySelectorAll('.btn-close').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index);
                this.removeFile(idx);
            });
        });

        // Prévisualisation PDF (miniatures)
        if (this.preview) {
            this.preview.innerHTML = '';
            this.files.forEach(file => {
                const thumb = document.createElement('div');
                thumb.className = 'pdf-thumb border p-1 text-center';
                thumb.style.width = '80px';
                thumb.style.height = '100px';
                thumb.style.display = 'flex';
                thumb.style.alignItems = 'center';
                thumb.style.justifyContent = 'center';
                thumb.style.fontSize = '12px';
                thumb.style.background = '#f8f9fa';
                thumb.style.color = '#333';
                thumb.innerText = file.name.split('.').slice(0, -1).join('.');
                this.preview.appendChild(thumb);
            });
        }
    }

    updateButton() {
        if (!this.actionButton) return;
        this.actionButton.disabled = !this.files.length;
    }

    getFiles() {
        return this.files;
    }

    async getFilesBase64() {
        const results = [];
        for (const file of this.files) {
            const base64 = await this.fileToBase64(file);
            results.push({ name: file.name, data: base64 });
        }
        return results;
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
}

// Initialisation globale
window.uploadManagers = {};
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.upload-zone-pro').forEach(zone => {
        const id = zone.id;
        const infoId = zone.dataset.infoId || id + 'Info';
        const btnId = zone.dataset.btnId || id + 'Button';
        const previewId = zone.dataset.previewId || null;
        window.uploadManagers[id] = new UploadManager(id, infoId, btnId, previewId);
    });
});
