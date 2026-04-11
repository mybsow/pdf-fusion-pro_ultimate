# blueprints/cloud/providers/google_drive.py
import os
import requests
import io

class GoogleDriveProvider:
    def __init__(self):
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        self.redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', '')
        self.scopes = 'https://www.googleapis.com/auth/drive.readonly'
    
    def get_auth_url(self):
        return f"https://accounts.google.com/o/oauth2/v2/auth?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={self.scopes}&response_type=code&access_type=offline&prompt=consent"
    
    def exchange_code(self, code):
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        response = requests.post('https://oauth2.googleapis.com/token', data=data)
        response.raise_for_status()
        return response.json()
    
    def list_files(self, token, path='/'):
        access_token = token.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Pour simplifier, on liste tous les fichiers (pas de gestion des dossiers imbriqués)
        url = 'https://www.googleapis.com/drive/v3/files'
        params = {
            'q': "mimeType != 'application/vnd.google-apps.folder'",
            'pageSize': 100,
            'fields': 'files(id, name, size, mimeType, webViewLink)'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        files = []
        for item in data.get('files', []):
            files.append({
                'name': item['name'],
                'path': item['id'],
                'size': int(item.get('size', 0)),
                'type': 'file',
                'mime_type': item.get('mimeType', '')
            })
        
        return files
    
    def download_file(self, token, file_id):
        access_token = token.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Récupérer le nom du fichier
        metadata_url = f'https://www.googleapis.com/drive/v3/files/{file_id}'
        meta_response = requests.get(metadata_url, headers=headers)
        filename = meta_response.json().get('name', 'file')
        
        return response.content, filename