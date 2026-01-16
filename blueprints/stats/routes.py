"""
Routes pour les statistiques et santé
"""

from flask import jsonify, Response
from datetime import datetime
from . import stats_bp
from managers.rating_manager import rating_manager
from managers.contact_manager import contact_manager
from managers.stats_manager import stats_manager

from config import AppConfig

@stats_bp.route('/health')
def health_check():
    """Endpoint de santé de l'application"""
    stats = stats_manager.stats  # Utilisez l'instance
    return jsonify({
        "status": "healthy",
        "app": AppConfig.NAME,
        "version": AppConfig.VERSION,
        "developer": AppConfig.DEVELOPER_NAME,
        "email": AppConfig.DEVELOPER_EMAIL,
        "hosting": AppConfig.HOSTING,
        "domain": AppConfig.DOMAIN,
        "timestamp": datetime.now().isoformat(),
        "total_operations": stats.get("total_operations", 0),
        "merges": stats.get("merges", 0),
        "splits": stats.get("splits", 0),
        "rotations": stats.get("rotations", 0),
        "compressions": stats.get("compressions", 0),
        "user_sessions": stats.get("user_sessions", 0)
    })

@stats_bp.route('/stats')
def get_stats():
    """Retourne les statistiques complètes"""
    return jsonify(stats_manager.stats)  # Utilisez l'instance
