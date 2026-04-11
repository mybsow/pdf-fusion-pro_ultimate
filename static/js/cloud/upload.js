/**
 * PDF Fusion Pro — Cloud Upload (version simple)
 * Ouvre le service cloud dans un nouvel onglet pour que l'utilisateur
 * télécharge son fichier, puis le charge via le bouton Parcourir.
 *
 * À placer dans : static/js/cloud/upload.js
 */
(function () {
    'use strict';

    var PROVIDERS = {
        google: {
            name: 'Google Drive',
            url: 'https://drive.google.com',
            icon: 'fab fa-google-drive',
            color: '#EA4335',
            tip: 'Ouvrez votre fichier dans Google Drive, puis téléchargez-le (clic droit → Télécharger) et importez-le ici.',
        },
        onedrive: {
            name: 'OneDrive',
            url: 'https://onedrive.live.com',
            icon: 'fab fa-microsoft',
            color: '#0078D4',
            tip: 'Ouvrez OneDrive, téléchargez votre fichier puis importez-le ici.',
        },
        dropbox: {
            name: 'Dropbox',
            url: 'https://www.dropbox.com/home',
            icon: 'fab fa-dropbox',
            color: '#0061FF',
            tip: 'Ouvrez Dropbox, téléchargez votre fichier puis importez-le ici.',
        },
        icloud: {
            name: 'iCloud Drive',
            url: 'https://www.icloud.com/iclouddrive',
            icon: 'fab fa-apple',
            color: '#444444',
            tip: 'Ouvrez iCloud Drive, téléchargez votre fichier puis importez-le ici.',
        },
    };

    /* ── CSS injecté une seule fois ── */
    function injectStyles() {
        if (document.getElementById('cu-styles')) return;
        var s = document.createElement('style');
        s.id = 'cu-styles';
        s.textContent = [
            '.cu-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:10000;',
            'display:flex;align-items:center;justify-content:center;',
            'animation:cu-in .15s ease}',
            '@keyframes cu-in{from{opacity:0}to{opacity:1}}',
            '.cu-modal{background:#fff;border-radius:16px;width:92%;max-width:420px;',
            'box-shadow:0 20px 60px rgba(0,0,0,.2);overflow:hidden;',
            'animation:cu-up .2s ease}',
            '@keyframes cu-up{from{transform:translateY(16px);opacity:0}to{transform:translateY(0);opacity:1}}',
            '.cu-head{padding:18px 20px 14px;border-bottom:1px solid #f0f0f0;',
            'display:flex;align-items:center;justify-content:space-between}',
            '.cu-head h5{margin:0;font-size:1rem;font-weight:700;color:#2c3e50}',
            '.cu-x{background:none;border:none;font-size:1.4rem;line-height:1;',
            'color:#aaa;cursor:pointer;padding:0 2px;transition:color .15s}',
            '.cu-x:hover{color:#2c3e50}',
            '.cu-body{padding:20px}',
            '.cu-sub{font-size:.82rem;color:#6c757d;margin:0 0 14px}',
            '.cu-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:18px}',
            '.cu-btn{display:flex;flex-direction:column;align-items:center;gap:7px;',
            'padding:16px 10px;border:2px solid #e9ecef;border-radius:12px;',
            'background:#fff;cursor:pointer;font-size:.8rem;font-weight:600;color:#555;',
            'transition:all .2s;text-decoration:none}',
            '.cu-btn:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.1);',
            'border-color:var(--cu-c);color:var(--cu-c)}',
            '.cu-btn i{font-size:1.9rem;color:var(--cu-c)}',
            '.cu-tip{display:none;background:#f8f9fa;border-left:3px solid #e74c3c;',
            'border-radius:6px;padding:10px 14px;font-size:.8rem;color:#555;',
            'margin-bottom:14px;line-height:1.5}',
            '.cu-tip.show{display:block}',
            '.cu-foot{text-align:center;font-size:.78rem;color:#aaa;line-height:1.6}',
        ].join('');
        document.head.appendChild(s);
    }

    var _backdrop = null;

    function showTip(text) {
        var tip = document.getElementById('cu-tip');
        if (!tip) return;
        tip.textContent = '👆 ' + text;
        tip.classList.add('show');
    }

    function buildModal() {
        /* Boutons providers */
        var grid = document.createElement('div');
        grid.className = 'cu-grid';

        Object.entries(PROVIDERS).forEach(function(entry) {
            var key = entry[0], p = entry[1];
            var a = document.createElement('a');
            a.className = 'cu-btn';
            a.href = p.url;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.style.setProperty('--cu-c', p.color);
            a.innerHTML = '<i class="' + p.icon + '"></i>' + p.name;
            a.addEventListener('click', function() { showTip(p.tip); });
            grid.appendChild(a);
        });

        /* Tip */
        var tip = document.createElement('div');
        tip.className = 'cu-tip';
        tip.id = 'cu-tip';

        /* Footer */
        var foot = document.createElement('p');
        foot.className = 'cu-foot';
        foot.innerHTML = 'Après avoir téléchargé votre fichier,<br>utilisez le bouton <strong>Parcourir</strong> pour l\'importer ici.';

        /* Body */
        var body = document.createElement('div');
        body.className = 'cu-body';
        var sub = document.createElement('p');
        sub.className = 'cu-sub';
        sub.textContent = 'Sélectionnez votre service pour l\'ouvrir dans un nouvel onglet :';
        body.appendChild(sub);
        body.appendChild(grid);
        body.appendChild(tip);
        body.appendChild(foot);

        /* Header */
        var closeBtn = document.createElement('button');
        closeBtn.className = 'cu-x';
        closeBtn.setAttribute('aria-label', 'Fermer');
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', close);

        var head = document.createElement('div');
        head.className = 'cu-head';
        var title = document.createElement('h5');
        title.innerHTML = '<i class="fas fa-cloud me-2" style="color:#e74c3c"></i>Ouvrir depuis le cloud';
        head.appendChild(title);
        head.appendChild(closeBtn);

        /* Modal */
        var modal = document.createElement('div');
        modal.className = 'cu-modal';
        modal.appendChild(head);
        modal.appendChild(body);
        return modal;
    }

    function open(provider) {
        injectStyles();
        close();

        var modal = buildModal();

        var backdrop = document.createElement('div');
        backdrop.className = 'cu-backdrop';
        backdrop.addEventListener('click', function(e) {
            if (e.target === backdrop) close();
        });
        backdrop.appendChild(modal);
        document.body.appendChild(backdrop);
        _backdrop = backdrop;

        /* Si provider précisé → ouvrir directement + afficher le tip */
        if (provider && PROVIDERS[provider]) {
            var p = PROVIDERS[provider];
            window.open(p.url, '_blank', 'noopener,noreferrer');
            showTip(p.tip);
        }
    }

    function close() {
        if (_backdrop && _backdrop.parentNode) {
            _backdrop.parentNode.removeChild(_backdrop);
        }
        _backdrop = null;
    }

    window.cloudUpload = { open: open, close: close };

})();