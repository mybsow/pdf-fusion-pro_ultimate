# blueprints/cloud/providers/onedrive.py
import os
import requests

class OneDriveProvider:
    def __init__(self):
        self.client_id = os.environ.get('ONEDRIVE_CLIENT_ID', '')
        self.client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET', '')
        self.redirect_uri = os.environ.get('ONEDRIVE_REDIRECT_URI', '')
        self.scopes = 'files.read offline_access'
    
    def get_auth_url(self):
        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}&scope={self.scopes}"
    
    def exchange_code(self, code):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        response = requests.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data=data)
        response.raise_for_status()
        return response.json()
    
    def list_files(self, token, path='/'):
        access_token = token.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        if path == '/':
            url = 'https://graph.microsoft.com/v1.0/me/drive/root/children'
        else:
            url = f'https://graph.microsoft.com/v1.0/me/drive/items/{path}/children'
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        files = []
        for item in data.get('value', []):
            files.append({
                'name': item['name'],
                'path': item['id'],
                'size': item.get('size', 0),
                'type': 'folder' if 'folder' in item else 'file',
                'mime_type': item.get('file', {}).get('mimeType', '')
            })
        
        return files
    
    def download_file(self, token, file_id):
        access_token = token.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Récupérer les métadonnées
        metadata_url = f'https://graph.microsoft.com/v1.0/me/drive/items/{file_id}'
        meta_response = requests.get(metadata_url, headers=headers)
        meta_response.raise_for_status()
        filename = meta_response.json().get('name', 'file')
        
        # Télécharger le contenu
        url = f'https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.content, filename