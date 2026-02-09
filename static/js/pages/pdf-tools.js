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
            const uploadManager = window.uploadManagers[`${tool}UploadZone`];
            if (!uploadManager) return;

            const files = uploadManager.getFiles();
            if (!files.length) {
                alert("Veuillez sélectionner au moins un fichier PDF.");
                return;
            }

            toggleLoader(true);

            try {
                const formData = new FormData();
                files.forEach(f => formData.append('files', f));

                if (tool === 'split' || tool === 'rotate') {
                    formData.append('pages', pagesInput?.value || 'all');
                }

                if (tool === 'rotate') {
                    const angle = document.querySelector('input[name="rotateAngle"]:checked').value;
                    formData.append('angle', angle);
                }

                // Requête POST vers ton endpoint
                const res = await fetch(`/pdf/${tool}`, { method: 'POST', body: formData });

                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(text || 'Erreur serveur inconnue');
                }

                const blob = await res.blob();

                // Téléchargement automatique
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                const defaultNames = {
                    merge: 'merged.pdf',
                    split: 'split.pdf',
                    compress: 'compressed.pdf',
                    rotate: 'rotated.pdf'
                };
                a.download = defaultNames[tool] || 'file.pdf';

                document.body.appendChild(a);
                a.click();
                a.remove();

            } catch (err) {
                console.error(err);
                alert(`Erreur lors du traitement : ${err.message}`);
            } finally {
                toggleLoader(false);
            }
        });
    });

});
