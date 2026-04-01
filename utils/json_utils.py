import json
import re

def safe_json_loads(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("JSON invalide, tentative de récupération...")

        candidates = re.findall(r'\{.*?\}|\[.*?\]', text, re.DOTALL)

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except:
                continue

        return None