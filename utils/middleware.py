"""
Middleware pour l'application Flask
"""

import uuid
from flask import g, request, Response

def setup_middleware(app, stats_manager_instance):  # Renommez le paramètre
    """Configure le middleware de l'application"""
    
    @app.before_request
    def before_request():
        """Exécuté avant chaque requête"""
        if not request.cookies.get("session_id"):
            stats_manager_instance.new_session()  # Utilisez l'instance passée en paramètre
            g._create_session_cookie = True
    
    @app.after_request
    def add_security_headers(response):
        """Ajoute les en-têtes de sécurité HTTP"""
        # Sécurité
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "fullscreen=(self)"
        
        # Cache
        if request.path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=31536000"
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        # Cookie de session
        if getattr(g, "_create_session_cookie", False):
            response.set_cookie(
                "session_id",
                str(uuid.uuid4()),
                httponly=True,
                secure=request.is_secure,
                samesite="Lax",
                max_age=60 * 60 * 24 * 30,  # 30 jours
            )
        
        return response