#!/usr/bin/env python3
import json
from datetime import datetime

# Test des contacts
contacts = []
for i in range(3):
    contacts.append({
        "id": i + 1,
        "first_name": f"Test{i}",
        "last_name": f"User{i}",
        "email": f"test{i}@example.com",
        "phone": "0123456789",
        "subject": "Test subject",
        "message": "Test message",
        "timestamp": datetime.now().isoformat(),
        "seen": False,
        "archived": False
    })

with open('data/contacts.json', 'w') as f:
    json.dump(contacts, f, indent=2)

print("Contacts créés dans data/contacts.json")

# Test des ratings
import os
os.makedirs('data/ratings', exist_ok=True)

for i in range(3):
    rating_data = {
        "id": f"rating_test_{i}",
        "timestamp": datetime.now().isoformat() + "Z",
        "rating": i + 3,
        "feedback": f"Test feedback {i}",
        "page": "/",
        "user_agent": "Test",
        "ip": "127.0.0.1",
        "seen": False
    }
    
    with open(f'data/ratings/rating_test_{i}.json', 'w') as f:
        json.dump(rating_data, f, indent=2)

print("Ratings créés dans data/ratings/")
