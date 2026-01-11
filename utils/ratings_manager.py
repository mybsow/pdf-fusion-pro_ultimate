"""
Gestionnaire des évaluations
"""

import json
import os
from datetime import datetime
from pathlib import Path

class RatingsManager:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.ratings_file = self.data_dir / 'ratings.json'
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Crée les répertoires nécessaires"""
        self.data_dir.mkdir(exist_ok=True)
    
    def save_rating(self, rating_data):
        """Sauvegarde une évaluation"""
        try:
            # Charger les évaluations existantes
            ratings = self.get_all_ratings()
            
            # Ajouter la nouvelle évaluation
            rating_data['id'] = f"rating_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            rating_data['timestamp'] = datetime.now().isoformat()
            ratings.append(rating_data)
            
            # Sauvegarder
            with open(self.ratings_file, 'w', encoding='utf-8') as f:
                json.dump(ratings, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Évaluation sauvegardée: {rating_data['id']}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde évaluation: {e}")
            return False
    
    def get_all_ratings(self):
        """Récupère toutes les évaluations"""
        try:
            if self.ratings_file.exists():
                with open(self.ratings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"❌ Erreur lecture évaluations: {e}")
            return []
    
    def get_stats(self):
        """Calcule les statistiques des évaluations"""
        ratings = self.get_all_ratings()
        
        if not ratings:
            return {
                'total': 0,
                'average': 0,
                'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'recent_count': 0
            }
        
        # Calculer la moyenne
        total_ratings = len(ratings)
        average = sum(r['rating'] for r in ratings) / total_ratings
        
        # Distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in ratings:
            distribution[r['rating']] += 1
        
        # Récentes (7 derniers jours)
        recent_count = 0
        week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
        for r in ratings:
            if 'timestamp' in r:
                try:
                    rating_time = datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')).timestamp()
                    if rating_time > week_ago:
                        recent_count += 1
                except:
                    pass
        
        return {
            'total': total_ratings,
            'average': round(average, 2),
            'distribution': distribution,
            'recent_count': recent_count,
            'recent_percentage': round((recent_count / total_ratings * 100) if total_ratings > 0 else 0, 1)
        }
    
    def delete_rating(self, rating_id):
        """Supprime une évaluation"""
        try:
            ratings = self.get_all_ratings()
            new_ratings = [r for r in ratings if r.get('id') != rating_id]
            
            if len(new_ratings) < len(ratings):
                with open(self.ratings_file, 'w', encoding='utf-8') as f:
                    json.dump(new_ratings, f, indent=2, ensure_ascii=False)
                print(f"✅ Évaluation supprimée: {rating_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur suppression évaluation: {e}")
            return False

# Instance globale
ratings_manager = RatingsManager()