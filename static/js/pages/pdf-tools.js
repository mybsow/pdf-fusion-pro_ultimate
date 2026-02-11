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
                
                // Préparer les données selon l'outil
                if (tool === 'merge') {
                    // Pour la fusion, envoyer tous les fichiers
                    uploadManager.files.forEach(f => formData.append('files', f));
                } else {
                    // Pour split, rotate, compress: un seul fichier
                    if (uploadManager.files.length > 1) {
                        alert(`Pour ${tool}, veuillez sélectionner un seul fichier PDF.`);
                        toggleLoader(false);
                        return;
                    }
                    formData.append('file', uploadManager.files[0]);
                }
                
                // Ajouter les paramètres spécifiques
                if (tool === 'split' || tool === 'rotate') {
                    const pages = pagesInput?.value || 'all';
                    formData.append('pages', pages);
                }
                
                if (tool === 'rotate') {
                    const angle = document.querySelector('input[name="rotateAngle"]:checked')?.value || '90';
                    formData.append('angle', angle);
                }
                
                if (tool === 'compress') {
                    const level = document.querySelector('input[name="compressionLevel"]:checked')?.value || 'medium';
                    formData.append('level', level);
                }

                // CORRECTION: Envoyer à /{tool} (pas /pdf/{tool}) car le blueprint est à la racine
                const API_PREFIX = "/pdf";
                const endpoint = `${API_PREFIX}/${tool}`;
                console.log(`Envoi à: ${endpoint}`, tool, formData);
                
                const res = await fetch(endpoint, { 
                    method: 'POST', 
                    body: formData 
                });

                if (!res.ok) {
                    let errorText = await res.text();
                    console.error('Erreur serveur:', res.status, errorText);
                    
                    // Essayer d'extraire un message d'erreur lisible
                    try {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(errorText, 'text/html');
                        const errorMsg = doc.querySelector('h1, p, pre')?.textContent || errorText;
                        throw new Error(`Erreur ${res.status}: ${errorMsg.substring(0, 200)}`);
                    } catch {
                        throw new Error(`Erreur ${res.status}: ${errorText.substring(0, 200)}`);
                    }
                }

                // Récupérer le nom de fichier depuis les headers si possible
                const contentDisposition = res.headers.get('Content-Disposition');
                let filename = '';
                
                if (contentDisposition) {
                    const matches = contentDisposition.match(/filename="?(.+?)"?$/);
                    if (matches) {
                        filename = matches[1];
                    }
                }
                
                // Nom par défaut si pas trouvé dans les headers
                if (!filename) {
                    const defaultNames = {
                        merge: 'fichiers-fusionnes.pdf',
                        split: 'pages-separees.zip',
                        compress: 'fichier-compresse.pdf',
                        rotate: 'pages-tournees.pdf'
                    };
                    filename = defaultNames[tool] || 'fichier.pdf';
                }

                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;

                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                // Libérer la mémoire
                setTimeout(() => window.URL.revokeObjectURL(url), 100);

            } catch (err) {
                console.error('Erreur détaillée:', err);
                
                // Message utilisateur plus clair
                let message = 'Erreur lors du traitement';
                if (err.message.includes('404')) {
                    message = 'Le service est temporairement indisponible. Veuillez réessayer.';
                } else if (err.message.includes('NetworkError')) {
                    message = 'Problème de connexion. Vérifiez votre internet.';
                } else if (err.message.includes('500')) {
                    message = 'Erreur serveur. Le fichier PDF est peut-être corrompu.';
                } else {
                    message = err.message.substring(0, 100) + '...';
                }
                
                alert(message);
            } finally {
                toggleLoader(false);
            }
        });
    });

});