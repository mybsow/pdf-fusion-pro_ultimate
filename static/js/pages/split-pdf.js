// static/js/pages/split-pdf.js
document.addEventListener('DOMContentLoaded', () => {
    const splitButton = document.getElementById('splitButton');
    const zipButton = document.getElementById('splitZipButton');
    const previewGrid = document.getElementById('splitPreviewGrid');

    UploadManager.onChange('split', (files) => {
        previewGrid.innerHTML = '';
        Array.from(files).forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'file-preview';
            div.textContent = `${index + 1}. ${file.name}`;
            previewGrid.appendChild(div);
        });
    });

    const processSplit = (asZip = false) => {
        const files = UploadManager.getFiles('split');
        if (!files.length) return;

        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('mode', document.getElementById('splitMode').value);
        formData.append('arg', document.getElementById('splitArg').value || '');

        const button = asZip ? zipButton : splitButton;
        button.disabled = true;
        button.textContent = asZip ? 'Préparation ZIP...' : 'Division en cours...';

        fetch('/api/split', {
            method: 'POST',
            body: formData
        })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = asZip ? 'split.zip' : 'split.pdf';
            a.click();
            button.disabled = false;
            button.textContent = asZip ? 'Télécharger en ZIP' : 'Diviser le PDF';
        })
        .catch(err => {
            console.error(err);
            button.disabled = false;
            button.textContent = asZip ? 'Télécharger en ZIP' : 'Diviser le PDF';
            alert('Erreur lors de la division');
        });
    };

    splitButton.addEventListener('click', () => processSplit(false));
    zipButton.addEventListener('click', () => processSplit(true));
});
