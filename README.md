# PDF Fusion Pro

Application web pour fusionner, modifier et compresser des PDFs.

## 🚀 Déploiement sur Render.com

1. **Créez un compte** sur [Render.com](https://render.com)
2. **Cliquez sur "New +"** → "Web Service"
3. **Connectez votre repository GitHub**
4. **Configurez le service :**
   - **Name :** `pdf-fusion-pro`
   - **Runtime :** Python 3
   - **Build Command :** `pip install -r requirements.txt`
   - **Start Command :** `gunicorn app:app`
   - **Plan :** Free

## 🔧 Configuration

### Variables d'environnement
