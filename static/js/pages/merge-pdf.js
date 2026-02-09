// static/js/pages/merge-pdf.js
document.addEventListener('DOMContentLoaded', () => {
    const mergeButton = document.getElementById('mergeButton');
    const previewGrid = document.getElementById('mergePreviewGrid');

    // Mettre à jour la prévisualisation PDF
    UploadManager.onChange('merge', (files) => {
        previewGrid.innerHTML = '';
        Array.from(files).forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'file-preview';
            div.textContent = `${index + 1}. ${file.name}`;
            previewGrid.appendChild(div);
        });
    });

    mergeButton.addEventListener('click', () => {
        const files = UploadManager.getFiles('merge');
        if (!files.length) return;
        
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        mergeButton.disabled = true;
        mergeButton.textContent = 'Fusion en cours...';

        fetch('/api/merge', {
            method: 'POST',
            body: formData
        })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'merged.pdf';
            a.click();
            mergeButton.disabled = false;
            mergeButton.textContent = 'Fusionner les PDFs';
        })
        .catch(err => {
            console.error(err);
            mergeButton.disabled = false;
            mergeButton.textContent = 'Fusionner les PDFs';
            alert('Erreur lors de la fusion');
        });
    });
});
