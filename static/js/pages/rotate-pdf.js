// static/js/pages/rotate-pdf.js
document.addEventListener('DOMContentLoaded', () => {
    const rotateButton = document.getElementById('rotateButton');

    rotateButton.addEventListener('click', () => {
        const files = UploadManager.getFiles('rotate');
        if (!files.length) return;

        const angle = document.querySelector('input[name="rotateAngle"]:checked').value;
        const pages = document.getElementById('rotatePages').value || 'all';

        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('angle', angle);
        formData.append('pages', pages);

        rotateButton.disabled = true;
        rotateButton.textContent = 'Rotation en cours...';

        fetch('/api/rotate', { method: 'POST', body: formData })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'rotated.pdf';
            a.click();
            rotateButton.disabled = false;
            rotateButton.textContent = 'Tourner le PDF';
        })
        .catch(err => {
            console.error(err);
            rotateButton.disabled = false;
            rotateButton.textContent = 'Tourner le PDF';
            alert('Erreur lors de la rotation');
        });
    });
});
