# managers/__init__.py
"""
Managers pour la logique métier
Exportation centralisée des managers
"""

from .contact_manager import ContactManager
from .conversion_manager import ConversionManager
from .rating_manager import RatingManager
from .stats_manager import StatisticsManager

# Instances singleton pour réutilisation
contact_manager = ContactManager()
conversion_manager = ConversionManager()
rating_manager = RatingManager()
stats_manager = StatisticsManager()

__all__ = [
    'ContactManager',
    'ConversionManager',
    'RatingManager', 
    'StatisticsManager',
    'contact_manager',
    'conversion_manager',
    'rating_manager',
    'stats_manager'
]