# PDF Fusion Pro

Application web pour fusionner, modifier et compresser des PDFs. Maintenant disponible en plusieurs langues !

## 🌍 Internationalisation

L'application supporte actuellement les langues suivantes :
- 🇫🇷 Français (par défaut)
- 🇬🇧 Anglais
- 🇪🇸 Espagnol
- 🇩🇪 Allemand
- 🇮🇹 Italien
- 🇵🇹 Portugais
- 🇳🇱 Néerlandais
- 🇸🇦 Arabe
- 🇨🇳 Chinois
- 🇯🇵 Japonais
- 🇷🇺 Russe

La langue est automatiquement détectée selon les préférences de votre navigateur, mais vous pouvez aussi la changer manuellement via le sélecteur de langue dans l'interface.

## 🚀 Déploiement sur Render.com

1. **Créez un compte** sur [Render.com](https://render.com)
2. **Cliquez sur "New +"** → "Web Service"
3. **Connectez votre repository GitHub**
4. **Configurez le service :**
   - **Name :** `pdf-fusion-pro`
   - **Runtime :** Python 3
   - **Build Command :** `pip install -r requirements.txt && chmod +x scripts/init_translations.sh && ./scripts/init_translations.sh`
   - **Start Command :** `gunicorn app:app`
   - **Plan :** Free

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Configuration de l'application
SECRET_KEY=votre_cle_secrete
FLASK_ENV=production
FLASK_DEBUG=0

# Domaine (sans https://)
DOMAIN=pdf-fusion-pro-ultimate-ltd.onrender.com

# Contact
CONTACT_EMAIL=banousow@gmail.com

# Discord (optionnel)
DISCORD_WEBHOOK_URL=votre_webhook_url

# Google AdSense (optionnel)
ADSENSE_CLIENT_ID=ca-pub-8967416460526921