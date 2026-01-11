from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/api/rating', methods=['POST'])
def submit_rating():
    try:
        data = request.get_json()
        print(f"Données reçues: {data}")
        
        rating = int(data.get('rating', 0))
        rating_data = {
            'rating': rating,
            'feedback': data.get('feedback', ''),
            'timestamp': datetime.now().isoformat(),
        }
        
        # Sauvegarder
        os.makedirs('data', exist_ok=True)
        ratings_file = 'data/ratings.json'
        
        ratings = []
        if os.path.exists(ratings_file):
            with open(ratings_file, 'r') as f:
                try:
                    ratings = json.load(f)
                except:
                    ratings = []
        
        ratings.append(rating_data)
        
        with open(ratings_file, 'w') as f:
            json.dump(ratings, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Évaluation enregistrée"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Serveur de test - API disponible sur /api/rating"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
