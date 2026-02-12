// static/js/pages/pdf-tools.js
document.addEventListener('DOMContentLoaded', () => {

    function toggleLoader(show = true) {
        const loader = document.getElementById('loaderOverlay');
        if (loader) loader.style.display = show ? 'flex' : 'none';
    }

    // Génération d'une miniature PDF
    async function generateThumbnail(file) {
        if (!window.pdfjsLib) {
            console.warn('pdf.js non chargé');
            return '/static/images/pdf-placeholder.png';
        }
        
        try {
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
        } catch (error) {
            console.error('Erreur génération miniature:', error);
            return '/static/images/pdf-placeholder.png';
        }
    }

    // Fonction pour formater la taille du fichier
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
            
            if (files.length === 0) {
                // Afficher un message si aucun fichier
                const emptyMsg = document.createElement('div');
                emptyMsg.className = 'text-muted text-center p-3';
                emptyMsg.innerHTML = '<i class="bi bi-files"></i> Aucun fichier sélectionné';
                fileInfoDiv.appendChild(emptyMsg);
                button.disabled = true;
                return;
            }

            // Pour split/rotate/compress, limiter à 1 fichier visuellement
            const isSingleMode = ['split', 'rotate', 'compress'].includes(tool);
            if (isSingleMode && files.length > 1) {
                const warningMsg = document.createElement('div');
                warningMsg.className = 'alert alert-warning py-2';
                warningMsg.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Un seul fichier sera traité.';
                fileInfoDiv.appendChild(warningMsg);
            }

            for (let i = 0; i < files.length; i++) {
                const f = files[i];

                const li = document.createElement('div');
                li.className = 'file-thumb d-flex align-items-center mb-2 p-2 bg-dark rounded';
                li.dataset.index = i;
                li.style.position = 'relative';
                li.style.transition = 'all 0.2s';

                // Conteneur miniature
                const thumbContainer = document.createElement('div');
                thumbContainer.className = 'position-relative me-2';
                thumbContainer.style.width = '50px';
                thumbContainer.style.height = '50px';

                const thumb = document.createElement('img');
                thumb.className = 'thumb-img rounded';
                thumb.style.width = '50px';
                thumb.style.height = '50px';
                thumb.style.objectFit = 'cover';
                thumb.style.border = '1px solid rgba(255,255,255,0.1)';
                thumb.alt = f.name;

                try {
                    thumb.src = await generateThumbnail(f);
                } catch {
                    thumb.src = '/static/images/pdf-placeholder.png';
                }

                // Badge nombre de pages (simulé)
                const pageBadge = document.createElement('span');
                pageBadge.className = 'position-absolute bottom-0 end-0 bg-dark text-white rounded-pill px-1';
                pageBadge.style.fontSize = '0.65rem';
                pageBadge.style.lineHeight = '1.2';
                pageBadge.style.border = '1px solid rgba(255,255,255,0.3)';
                pageBadge.textContent = 'PDF';

                thumbContainer.appendChild(thumb);
                thumbContainer.appendChild(pageBadge);

                // Informations fichier
                const infoContainer = document.createElement('div');
                infoContainer.className = 'flex-grow-1 ms-2';
                
                const fileName = document.createElement('div');
                fileName.className = 'fw-bold text-truncate';
                fileName.style.maxWidth = '200px';
                fileName.textContent = f.name;
                fileName.title = f.name;
                
                const fileMeta = document.createElement('div');
                fileMeta.className = 'text-muted small';
                fileMeta.textContent = formatFileSize(f.size);

                infoContainer.appendChild(fileName);
                infoContainer.appendChild(fileMeta);

                // Bouton suppression (poubelle)
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn btn-sm btn-outline-danger ms-auto';
                removeBtn.setAttribute('aria-label', 'Supprimer');
                removeBtn.style.border = 'none';
                removeBtn.style.padding = '6px 8px';
                removeBtn.innerHTML = '<i class="fas fa-trash" style="font-size: 1.1rem;"></i>'; // ⭐ CHANGÉ ICI
                
                // Effet hover sur le bouton
                removeBtn.addEventListener('mouseenter', () => {
                    li.style.backgroundColor = 'rgba(220, 53, 69, 0.1)';
                });
                removeBtn.addEventListener('mouseleave', () => {
                    li.style.backgroundColor = '';
                });

                removeBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Animation de suppression
                    li.style.transform = 'translateX(20px)';
                    li.style.opacity = '0';
                    
                    setTimeout(() => {
                        // Créer un nouveau FileList sans le fichier supprimé
                        const dt = new DataTransfer();
                        const newFiles = Array.from(fileInput.files).filter((_, index) => index !== i);
                        newFiles.forEach(file => dt.items.add(file));
                        fileInput.files = dt.files;
                        
                        // Déclencher l'événement change
                        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }, 200);
                });

                li.appendChild(thumbContainer);
                li.appendChild(infoContainer);
                li.appendChild(removeBtn);

                fileInfoDiv.appendChild(li);
            }

            // Activation du bouton
            button.disabled = files.length === 0;
            
            // Désactiver pour split/rotate/compress si plus d'un fichier
            if (isSingleMode && files.length > 1) {
                button.disabled = true;
            }
        };

        // Écouter les changements de fichiers
        fileInput.addEventListener('change', updateThumbnails);

        // Initialiser les miniatures si des fichiers sont déjà sélectionnés
        if (fileInput.files.length > 0) {
            updateThumbnails();
        }

        // Drag & drop amélioré avec visuel
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        uploadZone.addEventListener('dragenter', () => {
            uploadZone.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
        });

        uploadZone.addEventListener('dragover', () => {
            uploadZone.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
        });

        uploadZone.addEventListener('dragleave', (e) => {
            if (!uploadZone.contains(e.relatedTarget)) {
                uploadZone.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
            }
        });

        uploadZone.addEventListener('drop', (e) => {
            uploadZone.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
            const dt = e.dataTransfer;
            const droppedFiles = dt.files;
            
            if (droppedFiles.length > 0) {
                // Pour split/rotate/compress, on remplace les fichiers
                const isSingleMode = ['split', 'rotate', 'compress'].includes(tool);
                
                const dtTransfer = new DataTransfer();
                
                if (isSingleMode) {
                    // Remplacer par le premier fichier
                    dtTransfer.items.add(droppedFiles[0]);
                } else {
                    // Ajouter aux fichiers existants
                    Array.from(fileInput.files).forEach(f => dtTransfer.items.add(f));
                    Array.from(droppedFiles).forEach(f => dtTransfer.items.add(f));
                }
                
                fileInput.files = dtTransfer.files;
                fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Bouton d'action
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const files = Array.from(fileInput.files);
            
            if (!files.length) {
                alert("Veuillez sélectionner au moins un fichier PDF.");
                return;
            }

            // Vérification pour split/rotate/compress
            const isSingleMode = ['split', 'rotate', 'compress'].includes(tool);
            if (isSingleMode && files.length > 1) {
                alert(`Pour ${tool}, veuillez sélectionner un seul fichier PDF.`);
                return;
            }

            toggleLoader(true);

            try {
                const formData = new FormData();
                
                if (tool === 'merge') {
                    // Pour la fusion, envoyer TOUS les fichiers
                    files.forEach(f => {
                        formData.append('files', f);
                        console.log(`📎 Merge: ${f.name} (${formatFileSize(f.size)})`);
                    });
                } else {
                    // Pour split, rotate, compress: UN SEUL fichier
                    formData.append('file', files[0]);
                    console.log(`📎 ${tool}: ${files[0].name} (${formatFileSize(files[0].size)})`);
                }
                
                // Paramètres spécifiques
                if (tool === 'split') {
                    const pages = pagesInput?.value || 'all';
                    formData.append('mode', 'range');
                    formData.append('arg', pages);
                    console.log(`📄 Split pages: ${pages}`);
                }
                
                if (tool === 'rotate') {
                    const pages = pagesInput?.value || 'all';
                    formData.append('pages', pages);
                    
                    const angle = document.querySelector('input[name="rotateAngle"]:checked')?.value || '90';
                    formData.append('angle', angle);
                    console.log(`🔄 Rotation: ${angle}°, pages: ${pages}`);
                }
                
                if (tool === 'compress') {
                    const level = document.querySelector('input[name="compressionLevel"]:checked')?.value || 'medium';
                    formData.append('level', level);
                    console.log(`🗜️ Compression: ${level}`);
                }

                // Endpoint
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

                // Téléchargement
                const contentDisposition = res.headers.get('Content-Disposition');
                let filename = '';
                
                if (contentDisposition) {
                    const matches = contentDisposition.match(/filename="?(.+?)"?$/);
                    if (matches) {
                        filename = decodeURIComponent(matches[1]);
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
                
                console.log(`✅ Téléchargé: ${filename} (${formatFileSize(blob.size)})`);

                // Feedback visuel de succès
                button.classList.add('btn-success');
                setTimeout(() => button.classList.remove('btn-success'), 1000);

            } catch (err) {
                console.error('❌ Erreur:', err);
                
                let message = 'Erreur lors du traitement';
                if (err.message.includes('404')) {
                    message = 'Service temporairement indisponible.';
                } else if (err.message.includes('NetworkError')) {
                    message = 'Problème de connexion.';
                } else if (err.message.includes('500')) {
                    message = 'Erreur serveur. PDF peut-être corrompu.';
                } else if (err.message.includes('Fichier trop volumineux')) {
                    message = 'Fichier trop volumineux.';
                } else {
                    message = err.message.substring(0, 150);
                }
                
                // Afficher dans un toast ou alert
                alert(`❌ ${message}`);
                
            } finally {
                toggleLoader(false);
            }
        });
    });

    // Charger pdf.js si nécessaire
    if (!window.pdfjsLib && document.getElementById('mergeUploadZone')) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js';
        script.integrity = 'sha512-U1UYJ+isT2Fqo6xM4/3F53EMmyF5RoTcA/sB5z2SR8MTMlKk5SUgwUvLth3V/0g0hH2BkA20jPKJfPWB1Uiw0Q==';
        script.crossOrigin = 'anonymous';
        script.referrerPolicy = 'no-referrer';
        document.head.appendChild(script);
        
        const scriptWorker = document.createElement('script');
        scriptWorker.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
        scriptWorker.integrity = 'sha512-5zY3N2VQnCQrU+K/Iq0vQuufuM1EqTuf0puyAbQ/LI6DoJp5DXzWcLJkUF8S1uDvS/7W9Q5MkU9Ksw+J2tQnfg==';
        scriptWorker.crossOrigin = 'anonymous';
        scriptWorker.referrerPolicy = 'no-referrer';
        document.head.appendChild(scriptWorker);
    }

});