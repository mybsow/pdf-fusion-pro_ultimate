// static/js/pages/compress-pdf.js
document.addEventListener('DOMContentLoaded', () => {
    const compressButton = document.getElementById('compressButton');

    compressButton.addEventListener('click', () => {
        const files = UploadManager.getFiles('compress');
        if (!files.length) return;

        const level = document.querySelector('input[name="compressionLevel"]:checked').value;
        const optimizeImages = document.getElementById('optimizeImages').checked;
        const removeMetadata = document.getElementById('removeMetadata').checked;
        const embedFonts = document.getElementById('embedFonts').checked;

        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('level', level);
        formData.append('optimizeImages', optimizeImages);
        formData.append('removeMetadata', removeMetadata);
        formData.append('embedFonts', embedFonts);

        compressButton.disabled = true;
        compressButton.textContent = 'Compression en cours...';

        fetch('/api/compress', { method: 'POST', body: formData })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'compressed.pdf';
            a.click();
            compressButton.disabled = false;
            compressButton.textContent = 'Compresser le PDF';
        })
        .catch(err => {
            console.error(err);
            compressButton.disabled = false;
            compressButton.textContent = 'Compresser le PDF';
            alert('Erreur lors de la compression');
        });
    });
});
