// static/js/pages/pdf-tools.js
document.addEventListener('DOMContentLoaded', () => {

    function toggleLoader(show = true) {
        const loader = document.getElementById('loaderOverlay');
        if (loader) loader.style.display = show ? 'flex' : 'none';
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
        
        if (!button || !uploadZone) return;

        // Récupérer le UploadManager existant
        const uploadManager = window.uploadManagers?.[`${tool}UploadZone`];
        
        if (!uploadManager) {
            console.error(`UploadManager non trouvé pour ${tool}`);
            return;
        }

        // ⭐ STOCKER L'ANCIENNE MÉTHODE
        const originalUpdateFileList = uploadManager.updateFileList.bind(uploadManager);
        const originalUpdateButton = uploadManager.updateButton.bind(uploadManager);

        // ⭐ NOUVELLE MÉTHODE updateFileList AVEC POUBELLES
        uploadManager.updateFileList = function() {
            // Appeler la méthode originale d'abord
            originalUpdateFileList();
            
            // Si pas de fileInfo, sortir
            if (!this.fileInfo) return;
            
            // ⭐ REMPLACER LES BOUTONS DE SUPPRESSION PAR DES POUBELLES
            const listItems = this.fileInfo.querySelectorAll('.list-group-item');
            
            listItems.forEach((item, index) => {
                // Remplacer le bouton existant
                const existingBtn = item.querySelector('.btn-close');
                if (existingBtn) {
                    // Créer une poubelle Font Awesome
                    const trashBtn = document.createElement('button');
                    trashBtn.type = 'button';
                    trashBtn.className = 'btn btn-sm btn-outline-danger';
                    trashBtn.setAttribute('aria-label', 'Supprimer');
                    trashBtn.style.border = 'none';
                    trashBtn.style.padding = '4px 8px';
                    trashBtn.style.borderRadius = '4px';
                    trashBtn.innerHTML = '<i class="fas fa-trash-alt" style="font-size: 1rem;"></i>';
                    trashBtn.dataset.index = index;
                    
                    // Remplacer
                    existingBtn.replaceWith(trashBtn);
                    
                    // Ajouter l'événement de suppression avec animation
                    trashBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Animation de suppression
                        item.style.transform = 'translateX(20px)';
                        item.style.opacity = '0';
                        item.style.transition = 'all 0.2s';
                        
                        setTimeout(() => {
                            this.removeFile(parseInt(trashBtn.dataset.index));
                        }, 200);
                    });
                }
            });
            
            // ⭐ AJOUTER DES POUBELLES DANS LES MINIATURES
            const thumbsContainer = document.getElementById(this.zone.id + 'Thumbnails');
            if (thumbsContainer) {
                const thumbItems = thumbsContainer.querySelectorAll('canvas, img, .pdf-thumb');
                thumbItems.forEach((thumb, index) => {
                    // Créer un conteneur si nécessaire
                    let container = thumb.parentElement;
                    if (!container.classList.contains('thumb-container')) {
                        // Envelopper dans un conteneur
                        container = document.createElement('div');
                        container.className = 'thumb-container position-relative';
                        container.style.display = 'inline-block';
                        container.style.margin = '5px';
                        thumb.parentNode.insertBefore(container, thumb);
                        container.appendChild(thumb);
                    }
                    
                    // Vérifier si une poubelle existe déjà
                    if (!container.querySelector('.trash-btn')) {
                        const trashBtn = document.createElement('button');
                        trashBtn.className = 'trash-btn btn btn-sm btn-danger position-absolute';
                        trashBtn.style.top = '5px';
                        trashBtn.style.right = '5px';
                        trashBtn.style.padding = '2px 6px';
                        trashBtn.style.borderRadius = '4px';
                        trashBtn.style.opacity = '0';
                        trashBtn.style.transition = 'opacity 0.2s';
                        trashBtn.style.zIndex = '10';
                        trashBtn.innerHTML = '<i class="fas fa-trash-alt" style="font-size: 0.8rem;"></i>';
                        trashBtn.dataset.index = index;
                        
                        container.appendChild(trashBtn);
                        
                        // Afficher la poubelle au survol
                        container.addEventListener('mouseenter', () => {
                            trashBtn.style.opacity = '1';
                        });
                        container.addEventListener('mouseleave', () => {
                            trashBtn.style.opacity = '0';
                        });
                        
                        // Suppression
                        trashBtn.addEventListener('click', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            container.style.transform = 'scale(0.8)';
                            container.style.opacity = '0';
                            container.style.transition = 'all 0.2s';
                            
                            setTimeout(() => {
                                this.removeFile(parseInt(trashBtn.dataset.index));
                            }, 200);
                        });
                    }
                });
            }
        };

        // ⭐ METTRE À JOUR LE BOUTON AU CHANGEMENT
        uploadManager.updateButton = function() {
            originalUpdateButton();
            button.disabled = !this.files.length;
            
            // Pour split/rotate/compress, désactiver si plus d'un fichier
            if (['split', 'rotate', 'compress'].includes(tool)) {
                if (this.files.length > 1) {
                    button.disabled = true;
                    button.title = "Un seul fichier autorisé";
                } else {
                    button.title = "";
                }
            }
        };

        // ⭐ BOUTON RÉINITIALISATION (supprimer tout)
        const resetBtn = document.querySelector(`button[onclick*="${tool}UploadZone.removeFile"]`);
        if (resetBtn) {
            resetBtn.onclick = (e) => {
                e.preventDefault();
                if (uploadManager.files.length > 0) {
                    // Supprimer tous les fichiers un par un
                    while (uploadManager.files.length > 0) {
                        uploadManager.removeFile(0);
                    }
                }
            };
        }

        // ⭐ FORCER LA MISE À JOUR INITIALE
        setTimeout(() => {
            uploadManager.updateFileList();
        }, 100);

        // ⭐ INTERCEPTER LES AJOUTS DE FICHIERS POUR METTRE À JOUR
        const originalHandleFiles = uploadManager.handleFiles.bind(uploadManager);
        uploadManager.handleFiles = function(fileList) {
            originalHandleFiles(fileList);
            // Forcer la mise à jour des poubelles après ajout
            setTimeout(() => this.updateFileList(), 50);
        };

        // ⭐ BOUTON D'ACTION PRINCIPAL
        button.addEventListener('click', async (e) => {
            e.preventDefault();

                // ✅ VÉRIFICATION DE SÉCURITÉ - AJOUTER CES 3 LIGNES
            if (typeof uploadManager.getFiles !== 'function') {
                alert('❌ Erreur: méthode getFiles() non disponible');
                console.error('getFiles() manquant dans uploadManager');
                return;
            }
            
            const files = uploadManager.getFiles();
            
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
                    files.forEach(f => {
                        formData.append('files', f);
                        console.log(`📎 Merge: ${f.name} (${formatFileSize(f.size)})`);
                    });
                } else {
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

                const endpoint = `/pdf/${tool}`;
                console.log(`🚀 Envoi à: ${endpoint}`);
                
                const res = await fetch(endpoint, { 
                    method: 'POST', 
                    body: formData 
                });

                if (!res.ok) {
                    let errorText = await res.text();
                    console.error('❌ Erreur serveur:', res.status, errorText);
                    throw new Error(`Erreur ${res.status}: ${errorText.substring(0, 200)}`);
                }

                // Téléchargement
                const contentDisposition = res.headers.get('Content-Disposition');
                let filename = '';
                
                if (contentDisposition) {
                    const matches = contentDisposition.match(/filename="?(.+?)"?$/);
                    if (matches) filename = decodeURIComponent(matches[1]);
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
                alert(`❌ ${err.message.substring(0, 150)}`);
            } finally {
                toggleLoader(false);
            }
        });
    });

});