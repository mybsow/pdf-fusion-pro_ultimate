"""
gunicorn.conf.py — Configuration Render Free (512 MB RAM)

Démarrer avec :
    gunicorn -c gunicorn.conf.py app:application

Sur render.yaml / Start Command :
    gunicorn -c gunicorn.conf.py app:application
"""

import multiprocessing
import os

# ── Workers ────────────────────────────────────────────────────────────────
# Render Free = 1 vCPU, 512 MB RAM.
# Règle classique : (2 × CPU) + 1 = 3 workers, mais chaque worker Flask
# avec Pillow/pypdf charge ~100–150 MB → 3 workers = 450 MB → OOM garanti.
# 1 worker = safe. 2 workers = acceptable si vos conversions < 200 MB pic.
workers = 1

# Gevent ou gthread permettent la concurrence sans multi-process (économise RAM).
# gthread : n threads par worker, partage la mémoire du processus.
worker_class = "gthread"
threads = 4          # 4 threads concurrents dans 1 seul processus

# ── Timeouts ───────────────────────────────────────────────────────────────
# Les conversions Gemini peuvent durer 60–120 s pour les gros PDF.
timeout          = 300   # kill worker si pas de réponse en 5 min
graceful_timeout = 30    # délai de grâce avant SIGKILL
keepalive        = 5     # connexions HTTP keep-alive (réduit overhead TLS)

# ── Mémoire ────────────────────────────────────────────────────────────────
# Redémarre le worker après N requêtes pour éviter l'accumulation de mémoire
# (fuites PIL, buffers non libérés, etc.)
max_requests          = 100   # redémarre après 100 requêtes
max_requests_jitter   = 20    # ± 20 requêtes (évite redémarrages simultanés)

# ── Réseau ─────────────────────────────────────────────────────────────────
bind         = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog      = 64        # file d'attente connexions entrantes (Render Free : faible charge)

# ── Logs ───────────────────────────────────────────────────────────────────
# errorlog / accesslog sur "-" = stdout (capturé par Render)
errorlog  = "-"
accesslog = None         # ← désactiver l'access log en prod (I/O inutile)
loglevel  = "warning"   # "info" génère ~1 ligne/requête → I/O sur Render disque SSD partagé

# ── Préchargement ──────────────────────────────────────────────────────────
# preload_app=True : charge l'app UNE fois avant fork des workers.
# Économise RAM grâce au copy-on-write (utile si workers > 1).
# Avec workers=1 : peu de différence, mais évite le rechargement à chaque restart.
preload_app = True

# ── Sécurité ───────────────────────────────────────────────────────────────
limit_request_line   = 4096   # taille max URI (défaut 8190, inutilement large)
limit_request_fields = 100    # nb max headers HTTP
forwarded_allow_ips  = "*"    # Render passe les IPs via X-Forwarded-For