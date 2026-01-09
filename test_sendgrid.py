#!/usr/bin/env python3
"""
Test SendGrid configuration
"""

import os
import sys

def test_sendgrid_config():
    print("🔍 Test configuration SendGrid")
    print("="*50)
    
    # Vérifier les variables
    required = ['SMTP_USERNAME', 'SMTP_PASSWORD', 'DEVELOPER_EMAIL']
    
    for var in required:
        value = os.environ.get(var)
        if value:
            masked = '*' * len(value) if 'PASSWORD' in var else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: MANQUANT")
    
    # Vérifier spécifiquement SendGrid
    if os.environ.get('SMTP_USERNAME') != 'apikey':
        print("\n⚠️ ATTENTION: SMTP_USERNAME devrait être 'apikey' pour SendGrid")
        print("   Actuel:", os.environ.get('SMTP_USERNAME'))
    
    # Tester l'API Key
    api_key = os.environ.get('SMTP_PASSWORD', '')
    if api_key:
        if api_key.startswith('SG.'):
            print(f"✅ API Key format: Valide (commence par SG.)")
        else:
            print(f"⚠️ API Key format: Inattendu (devrait commencer par SG.)")
    
    print("\n📋 Configuration Render recommandée:")
    print("="*50)
    print("SMTP_SERVER=smtp.sendgrid.net")
    print("SMTP_PORT=587")
    print("SMTP_USERNAME=apikey")
    print("SMTP_PASSWORD=SG.votre_api_key_ici")
    print("DEVELOPER_EMAIL=votre@email.com")
    
    # Tester l'envoi
    test_send = input("\n🧪 Tester l'envoi d'email ? (o/N): ").lower()
    if test_send in ['o', 'oui', 'y', 'yes']:
        from test_smtp import test_smtp_config
        test_smtp_config()

if __name__ == "__main__":
    test_sendgrid_config()