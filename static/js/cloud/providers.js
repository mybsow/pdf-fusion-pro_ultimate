// static/js/cloud/providers.js
// Configuration des providers cloud
const CloudProviders = {
    google: {
        name: 'Google Drive',
        icon: 'fab fa-google-drive',
        color: '#4285f4',
        authUrl: '/cloud/auth/google',
        apiUrl: '/cloud/files/google',
        downloadUrl: '/cloud/download/google'
    },
    onedrive: {
        name: 'OneDrive',
        icon: 'fab fa-microsoft',
        color: '#0078d4',
        authUrl: '/cloud/auth/onedrive',
        apiUrl: '/cloud/files/onedrive',
        downloadUrl: '/cloud/download/onedrive'
    },
    dropbox: {
        name: 'Dropbox',
        icon: 'fab fa-dropbox',
        color: '#0061ff',
        authUrl: '/cloud/auth/dropbox',
        apiUrl: '/cloud/files/dropbox',
        downloadUrl: '/cloud/download/dropbox'
    },
    icloud: {
        name: 'iCloud',
        icon: 'fab fa-apple',
        color: '#555555',
        authUrl: '/cloud/auth/icloud',
        apiUrl: '/cloud/files/icloud',
        downloadUrl: '/cloud/download/icloud'
    }
};