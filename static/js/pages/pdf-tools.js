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
        const uploadZone = document.getElementById(`${tool}UploadZone`);
        const fileInput = uploadZone ? uploadZone.querySelector('input[type="file"]') : null;

        if (!button || !uploadZone || !fileInput) return;

        // Élément pour afficher les miniatures
        const fileInfoId = `${tool}FileInfo`;
        let fileInfoDiv = document.getElementById(fileInfoId);
        
        // Créer le conteneur de miniatures s'il n'existe pas
        if (!fileInfoDiv) {
            fileInfoDiv = document.createElement('div');
            fileInfoDiv.id = fileInfoId;
            fileInfoDiv.className = 'file-info mt-3';
            uploadZone.appendChild(fileInfoDiv);
        }

        // Fonction pour mettre à jour les miniatures
        const updateThumbnails = async () => {
            if (!fileInfoDiv) return;
            fileInfoDiv.innerHTML = '';

            const files = Array.from(fileInput.files);
            
            for (let i = 0; i < files.length; i++) {
                const f = files[i];

                const li = document.createElement('div');
                li.className = 'file-thumb d-flex align-items-center mb-2 p-2 bg-dark rounded';
                li.dataset.index = i;

                const thumb = document.createElement('img');
                thumb.className = 'thumb-img me-2 rounded';
                thumb.style.width = '50px';
                thumb.style.height = '50px';
                thumb.style.objectFit = 'cover';
                thumb.alt = f.name;

                try {
                    thumb.src = await generateThumbnail(f);
                } catch {
                    thumb.src = '/static/images/pdf-placeholder.png';
                }

                const info = document.createElement('span');
                info.className = 'flex-grow-1';
                info.textContent = `${f.name} (${(f.size/1024/1024).toFixed(2)} MB)`;

                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn-close btn-close-white btn-sm ms-auto';
                removeBtn.setAttribute('aria-label', 'Supprimer');
                removeBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Créer un nouveau FileList sans le fichier supprimé
                    const dt = new DataTransfer();
                    const newFiles = Array.from(fileInput.files).filter((_, index) => index !== i);
                    newFiles.forEach(file => dt.items.add(file));
                    fileInput.files = dt.files;
                    
                    // Déclencher l'événement change
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                });

                li.appendChild(thumb);
                li.appendChild(info);
                li.appendChild(removeBtn);

                fileInfoDiv.appendChild(li);
            }

            // Activation du bouton
            button.disabled = files.length === 0;
        };

        // Écouter les changements de fichiers
        fileInput.addEventListener('change', updateThumbnails);

        // Initialiser les miniatures si des fichiers sont déjà sélectionnés
        if (fileInput.files.length > 0) {
            updateThumbnails();
        }

        // Bouton d'action
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const files = Array.from(fileInput.files);
            
            if (!files.length) {
                alert("Veuillez sélectionner au moins un fichier PDF.");
                return;
            }

            toggleLoader(true);

            try {
                const formData = new FormData();
                
                // === RÉCUPÉRATION RADICALE DIRECTEMENT DEPUIS L'INPUT ===
                if (tool === 'merge') {
                    // Pour la fusion, envoyer TOUS les fichiers
                    files.forEach(f => {
                        formData.append('files', f);
                        console.log(`Fichier ajouté (merge): ${f.name}, taille: ${f.size}, type: ${f.type}`);
                    });
                } else {
                    // Pour split, rotate, compress: UN SEUL fichier
                    if (files.length > 1) {
                        alert(`Pour ${tool}, veuillez sélectionner un seul fichier PDF.`);
                        toggleLoader(false);
                        return;
                    }
                    formData.append('file', files[0]);
                    console.log(`Fichier ajouté (${tool}): ${files[0].name}, taille: ${files[0].size}, type: ${files[0].type}`);
                }
                
                // === PARAMÈTRES SPÉCIFIQUES ===
                if (tool === 'split') {
                    const pages = pagesInput?.value || 'all';
                    formData.append('mode', 'range');
                    formData.append('arg', pages);
                    console.log(`Split params: mode=range, arg=${pages}`);
                }
                
                if (tool === 'rotate') {
                    const pages = pagesInput?.value || 'all';
                    formData.append('pages', pages);
                    
                    const angle = document.querySelector('input[name="rotateAngle"]:checked')?.value || '90';
                    formData.append('angle', angle);
                    console.log(`Rotate params: pages=${pages}, angle=${angle}`);
                }
                
                if (tool === 'compress') {
                    const level = document.querySelector('input[name="compressionLevel"]:checked')?.value || 'medium';
                    formData.append('level', level);
                    console.log(`Compress params: level=${level}`);
                }

                // === ENDPOINT CORRECT ===
                const endpoint = `/pdf/${tool}`;
                console.log(`🚀 Envoi à: ${endpoint}`);
                
                const res = await fetch(endpoint, { 
                    method: 'POST', 
                    body: formData 
                });

                if (!res.ok) {
                    let errorText = await res.text();
                    console.error('❌ Erreur serveur:', res.status, errorText);
                    
                    try {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(errorText, 'text/html');
                        const errorMsg = doc.querySelector('h1, p, pre')?.textContent || errorText;
                        throw new Error(`Erreur ${res.status}: ${errorMsg.substring(0, 200)}`);
                    } catch {
                        throw new Error(`Erreur ${res.status}: ${errorText.substring(0, 200)}`);
                    }
                }

                // === TÉLÉCHARGEMENT ===
                const contentDisposition = res.headers.get('Content-Disposition');
                let filename = '';
                
                if (contentDisposition) {
                    const matches = contentDisposition.match(/filename="?(.+?)"?$/);
                    if (matches) {
                        filename = matches[1];
                    }
                }
                
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
                
                setTimeout(() => window.URL.revokeObjectURL(url), 100);
                
                console.log(`✅ Téléchargement: ${filename}`);

            } catch (err) {
                console.error('❌ Erreur détaillée:', err);
                
                let message = 'Erreur lors du traitement';
                if (err.message.includes('404')) {
                    message = 'Le service est temporairement indisponible. Veuillez réessayer.';
                } else if (err.message.includes('NetworkError')) {
                    message = 'Problème de connexion. Vérifiez votre internet.';
                } else if (err.message.includes('500')) {
                    message = 'Erreur serveur. Le fichier PDF est peut-être corrompu.';
                } else if (err.message.includes('Aucun fichier')) {
                    message = 'Fichier non reçu par le serveur. Vérifiez le format PDF.';
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