/* =====================================================
   INDEX PAGE — PDF Fusion Pro
   JS spécifique à la page d'accueil
   ===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    setupDragAndDrop();
    setupFileInput();
    setupForms();

});


/* =====================================================
   DRAG & DROP
   ===================================================== */

function setupDragAndDrop() {

    const dropZones = document.querySelectorAll(".drop-zone");

    dropZones.forEach(zone => {

        const input = zone.querySelector("input[type='file']");

        if (!input) return;

        zone.addEventListener("click", () => input.click());

        zone.addEventListener("dragover", (e) => {
            e.preventDefault();
            zone.classList.add("dragover");
        });

        zone.addEventListener("dragleave", () => {
            zone.classList.remove("dragover");
        });

        zone.addEventListener("drop", (e) => {
            e.preventDefault();
            zone.classList.remove("dragover");

            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                displayFiles(input);
            }
        });

    });

}


/* =====================================================
   FILE INPUT
   ===================================================== */

function setupFileInput() {

    const inputs = document.querySelectorAll("input[type='file']");

    inputs.forEach(input => {

        input.addEventListener("change", () => {
            displayFiles(input);
        });

    });

}


function displayFiles(input) {

    const container = input.closest(".file-container");

    if (!container) return;

    const list = container.querySelector(".file-list");

    if (!list) return;

    list.innerHTML = "";

    const files = Array.from(input.files);

    files.forEach(file => {

        const item = document.createElement("div");
        item.className = "file-item";

        item.innerHTML = `
            <strong>${escapeHtml(file.name)}</strong>
            <span>${formatFileSize(file.size)}</span>
        `;

        list.appendChild(item);
    });

}


/* =====================================================
   FORM SUBMIT (API CALL)
   ===================================================== */

function setupForms() {

    const forms = document.querySelectorAll("form[data-api]");

    forms.forEach(form => {

        form.addEventListener("submit", async (e) => {

            e.preventDefault();

            const url = form.dataset.api;

            const formData = new FormData(form);

            try {

                showLoader();

                const response = await fetch(url, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Erreur serveur");
                }

                showToast(
                    "success",
                    "Succès",
                    data.message || "Traitement terminé"
                );

                // téléchargement auto si présent
                if (data.download_url) {
                    window.location.href = data.download_url;
                }

            } catch (err) {

                showToast("error", "Erreur", err.message);

            } finally {
                hideLoader();
            }

        });

    });

}
