// static/js/pages/pdf-tools.js
document.addEventListener('DOMContentLoaded', () => {

    function toggleLoader(show = true) {
        const loader = document.getElementById('loaderOverlay');
        if (loader) loader.style.display = show ? 'flex' : 'none';
    }

    const tools = ['merge', 'split', 'compress', 'rotate'];
    tools.forEach(tool => {
        const button = document.getElementById(`${tool}Button`);
        const pagesInput = document.getElementById(`${tool}Pages`);

        if (!button) return;

        button.addEventListener('click', async () => {
            const files = window.uploadManagers[`${tool}UploadZone`].getFiles();
            if (!files.length) return;

            toggleLoader(true);
            const formData = new FormData();

            files.forEach(f => formData.append('files', f));
            if (tool === 'split' || tool === 'rotate') {
                formData.append('pages', pagesInput?.value || 'all');
            }
            if (tool === 'rotate') {
                const angle = document.querySelector('input[name="rotateAngle"]:checked').value;
                formData.append('angle', angle);
            }

            try {
                const res = await fetch(`/pdf/${tool}`, { method: 'POST', body: formData });
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = tool === 'merge' ? 'merged.pdf'
                                : tool === 'split' ? 'split.pdf'
                                : tool === 'compress' ? 'compressed.pdf'
                                : 'rotated.pdf';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (err) {
                alert(`Erreur lors du traitement : ${err.message}`);
            } finally {
                toggleLoader(false);
            }
        });
    });

});
