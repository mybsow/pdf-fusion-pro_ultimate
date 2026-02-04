/* =====================================================
   GLOBAL HELPERS — PDF Fusion Pro
   ===================================================== */

// Loader
function showLoader() {
    const loader = document.getElementById("loaderOverlay");
    if (loader) loader.style.display = "flex";
}

function hideLoader() {
    const loader = document.getElementById("loaderOverlay");
    if (loader) loader.style.display = "none";
}


// Toast ultra léger (sans lib externe)
function showToast(type, title, message) {

    const colors = {
        success: "#22c55e",
        error: "#ef4444",
        warning: "#f59e0b",
        info: "#3b82f6"
    };

    const toast = document.createElement("div");

    toast.style.position = "fixed";
    toast.style.top = "20px";
    toast.style.right = "20px";
    toast.style.background = colors[type] || "#333";
    toast.style.color = "white";
    toast.style.padding = "14px 18px";
    toast.style.borderRadius = "10px";
    toast.style.boxShadow = "0 10px 30px rgba(0,0,0,0.2)";
    toast.style.zIndex = "9999";
    toast.style.maxWidth = "320px";
    toast.style.fontSize = "14px";

    toast.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "0.3s";

        setTimeout(() => toast.remove(), 300);
    }, 3500);
}


// Sécurité XSS
function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
}


// Format taille fichier
function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";

    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}


/* =====================================================
   FETCH WRAPPER (TRÈS RECOMMANDÉ)
   ===================================================== */

async function apiRequest(url, payload) {

    showLoader();

    try {

        const response = await fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur serveur");
        }

        return data;

    } catch (err) {

        showToast("error", "Erreur", err.message);
        throw err;

    } finally {
        hideLoader();
    }
}
