// static/js/pages/pdf-tools.js
document.addEventListener('DOMContentLoaded', () => {

    function toggleLoader(show = true) {
        const loader = document.getElementById('loaderOverlay');
        if (loader) loader.style.display = show ? 'flex' : 'none';
    }

    // Génération d'une miniature PDF
    async function generateThumbnail(file) {
        if (!window.pdfjsLib) return ''; // pdf.js non chargé
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 0.3 });
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await page.render({ canvasContext: context, viewport }).promise;
        return canvas.toDataURL('image/png');
    }

    const tools = ['merge', 'split', 'compress', 'rotate'];

    tools.forEach(tool => {
        const button = document.getElementById(`${tool}Button`);
        const pagesInput = document.getElementById(`${tool}Pages`);
        const uploadManager = window.uploadManagers[`${tool}UploadZone`];

        if (!button || !uploadManager) return;

        // Observer la liste de fichiers pour créer miniatures et drag & drop
        const fileInfoDiv = document.getElementById(uploadManager.fileInfo.id);
        const updateThumbnails = async () => {
            if (!fileInfoDiv) return;
            fileInfoDiv.innerHTML = '';

            for (let i = 0; i < uploadManager.files.length; i++) {
                const f = uploadManager.files[i];

                const li = document.createElement('div');
                li.className = 'file-thumb d-flex align-items-center mb-2';
                li.dataset.index = i;

                const thumb = document.createElement('img');
                thumb.className = 'thumb-img me-2';
                thumb.alt = f.name;

                try {
                    thumb.src = await generateThumbnail(f);
                } catch {
                    thumb.src = '/static/images/pdf-placeholder.png';
                }

                const info = document.createElement('span');
                info.textContent = `${f.name} (${(f.size/1024/1024).toFixed(2)} MB)`;

                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn-close btn-close-white btn-sm ms-auto';
                removeBtn.addEventListener('click', () => {
                    uploadManager.removeFile(i);
                });

                li.appendChild(thumb);
                li.appendChild(info);
                li.appendChild(removeBtn);

                fileInfoDiv.appendChild(li);
            }

            // Activation du bouton
            button.disabled = !uploadManager.files.length;

            // Initialiser le drag & drop pour réordonner
            if (uploadManager.files.length > 1) {
                new Sortable(fileInfoDiv, {
                    animation: 150,
                    onEnd: (evt) => {
                        const movedItem = uploadManager.files.splice(evt.oldIndex, 1)[0];
                        uploadManager.files.splice(evt.newIndex, 0, movedItem);
                    }
                });
            }
        };

        // Sur changement de fichiers
        const originalUpdateFileList = uploadManager.updateFileList.bind(uploadManager);
        uploadManager.updateFileList = () => {
            originalUpdateFileList();
            updateThumbnails();
        };

        // Bouton d'action
        button.addEventListener('click', async () => {
            if (!uploadManager.files.length) {
                alert("Veuillez sélectionner au moins un fichier PDF.");
                return;
            }

            toggleLoader(true);

            try {
                const formData = new FormData();
                uploadManager.files.forEach(f => formData.append('files', f));

                if (tool === 'split' || tool === 'rotate') {
                    formData.append('pages', pagesInput?.value || 'all');
                }
                if (tool === 'rotate') {
                    const angle = document.querySelector('input[name="rotateAngle"]:checked').value;
                    formData.append('angle', angle);
                }

                const res = await fetch(`/pdf/${tool}`, { method: 'POST', body: formData });

                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(text || 'Erreur serveur inconnue');
                }

                const blob = await res.blob();
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
