# blueprints/cloud/providers/dropbox.py
import os
import requests
import base64

class DropboxProvider:
    def __init__(self):
        self.app_key = os.environ.get('DROPBOX_APP_KEY', '')
        self.app_secret = os.environ.get('DROPBOX_APP_SECRET', '')
        self.redirect_uri = os.environ.get('DROPBOX_REDIRECT_URI', '')
    
    def get_auth_url(self):
        return f"https://www.dropbox.com/oauth2/authorize?client_id={self.app_key}&redirect_uri={self.redirect_uri}&response_type=code&token_access_type=offline"
    
    def exchange_code(self, code):
        data = {
            'code': code,
            'client_id': self.app_key,
            'client_secret': self.app_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        response = requests.post('https://api.dropboxapi.com/oauth2/token', data=data)
        response.raise_for_status()
        return response.json()
    
    def list_files(self, token, path='/'):
        access_token = token.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Convertir le chemin
        if path == '/':
            dropbox_path = ''
        else:
            dropbox_path = path
        
        data = {
            'path': dropbox_path,
            'recursive': False,
            'include_media_info': False,
            'include_deleted': False,
            'include_has_explicit_shared_members': False
        }
        
        response = requests.post('https://api.dropboxapi.com/2/files/list_folder', headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        files = []
        for entry in result.get('entries', []):
            files.append({
                'name': entry['name'],
                'path': entry['path_lower'],
                'size': entry.get('size', 0),
                'type': 'folder' if entry['.tag'] == 'folder' else 'file',
                'mime_type': ''
            })
        
        return files
    
    def download_file(self, token, file_path):
        access_token = token.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Dropbox-API-Arg': f'{{"path":"{file_path}"}}'
        }
        
        response = requests.post('https://content.dropboxapi.com/2/files/download', headers=headers)
        response.raise_for_status()
        
        filename = file_path.split('/')[-1]
        return response.content, filename