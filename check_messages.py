#!/usr/bin/env python3
"""
Script pour vérifier les messages de contact
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def list_contacts():
    """Lister tous les messages"""
    contacts_dir = Path("data/contacts")
    
    if not contacts_dir.exists():
        print("❌ Dossier 'data/contacts' introuvable")
        return []
    
    files = list(contacts_dir.glob("*.json"))
    
    if not files:
        print("📭 Aucun message trouvé")
        return []
    
    print(f"📨 {len(files)} messages trouvés\n")
    
    contacts = []
    for filepath in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['file'] = filepath.name
                contacts.append(data)
                
                # Afficher un résumé
                timestamp = data.get('received_at', '').replace('T', ' ').split('.')[0]
                print(f"📄 {filepath.name}")
                print(f"   👤 {data.get('first_name')} {data.get('last_name')}")
                print(f"   📧 {data.get('email')}")
                print(f"   🎯 {data.get('subject')}")
                print(f"   🕐 {timestamp}")
                print(f"   💬 {data.get('message', '')[:80]}...")
                print()
                
        except Exception as e:
            print(f"⚠️ Erreur lecture {filepath.name}: {e}")
    
    return contacts

def show_contact_details(filename=None):
    """Afficher les détails d'un message spécifique"""
    contacts_dir = Path("data/contacts")
    
    if filename:
        filepath = contacts_dir / filename
        if not filepath.exists():
            print(f"❌ Fichier {filename} introuvable")
            return
    
    # Si pas de filename, demander à l'utilisateur
    files = list(contacts_dir.glob("*.json"))
    if not files:
        print("❌ Aucun message trouvé")
        return
    
    if not filename:
        print("\n📋 Messages disponibles:")
        for i, filepath in enumerate(sorted(files, key=lambda x: x.stat().st_mtime, reverse=True), 1):
            print(f"{i}. {filepath.name}")
        
        choice = input("\n📝 Numéro du message à afficher (ou 'q' pour quitter): ")
        if choice.lower() == 'q':
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(files):
                filepath = files[index]
            else:
                print("❌ Choix invalide")
                return
        except:
            print("❌ Entrée invalide")
            return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n" + "="*60)
        print("📄 DÉTAILS DU MESSAGE")
        print("="*60)
        print(f"Fichier: {filepath.name}")
        print(f"Taille: {filepath.stat().st_size} octets")
        print(f"Créé: {datetime.fromtimestamp(filepath.stat().st_ctime)}")
        print("="*60)
        
        print(f"\n👤 CONTACT:")
        print(f"  Nom: {data.get('first_name')} {data.get('last_name')}")
        print(f"  Email: {data.get('email')}")
        print(f"  Téléphone: {data.get('phone', 'Non renseigné')}")
        
        print(f"\n📝 INFOS:")
        subject_map = {
            'bug': '🚨 Bug/Problème technique',
            'improvement': '💡 Amélioration/Suggestion',
            'partnership': '🤝 Partenariat',
            'other': '❓ Autre demande'
        }
        print(f"  Sujet: {subject_map.get(data.get('subject'), data.get('subject'))}")
        print(f"  Reçu le: {data.get('received_at')}")
        print(f"  IP: {data.get('ip_address', 'N/A')}")
        print(f"  Navigateur: {data.get('user_agent', 'N/A')[:80]}...")
        
        print(f"\n💬 MESSAGE:")
        print("-"*40)
        print(data.get('message', ''))
        print("-"*40)
        
        print(f"\n📊 STATS APPLICATION:")
        print(f"  App: {data.get('app_name', 'N/A')}")
        print(f"  Domaine: {data.get('domain', 'N/A')}")
        
        print("\n🔧 ACTIONS:")
        print(f"  1. Copier l'email: {data.get('email')}")
        print(f"  2. Ouvrir dans l'éditeur: nano {filepath}")
        print(f"  3. Supprimer ce message")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def export_contacts(format='json'):
    """Exporter les contacts"""
    contacts_dir = Path("data/contacts")
    files = list(contacts_dir.glob("*.json"))
    
    if not files:
        print("❌ Aucun message à exporter")
        return
    
    contacts = []
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                contacts.append(json.load(f))
        except:
            pass
    
    if format == 'json':
        output_file = f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
        print(f"✅ Exporté vers {output_file} ({len(contacts)} messages)")
    
    elif format == 'csv':
        import csv
        output_file = f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Nom', 'Prénom', 'Email', 'Téléphone', 'Sujet', 'Message'])
            for contact in contacts:
                writer.writerow([
                    contact.get('received_at', ''),
                    contact.get('last_name', ''),
                    contact.get('first_name', ''),
                    contact.get('email', ''),
                    contact.get('phone', ''),
                    contact.get('subject', ''),
                    contact.get('message', '')[:500]
                ])
        print(f"✅ Exporté vers {output_file} ({len(contacts)} messages)")

def main():
    """Menu principal"""
    print("\n" + "="*60)
    print("📨 GESTIONNAIRE DE MESSAGES PDF FUSION PRO")
    print("="*60)
    
    while True:
        print("\n📋 MENU:")
        print("1. 📄 Lister tous les messages")
        print("2. 🔍 Voir les détails d'un message")
        print("3. 📥 Exporter en JSON")
        print("4. 📊 Exporter en CSV")
        print("5. 📊 Statistiques")
        print("6. 🗑️ Nettoyer les vieux messages (>30 jours)")
        print("7. 🚪 Quitter")
        
        choice = input("\n👉 Votre choix (1-7): ")
        
        if choice == '1':
            list_contacts()
        elif choice == '2':
            show_contact_details()
        elif choice == '3':
            export_contacts('json')
        elif choice == '4':
            export_contacts('csv')
        elif choice == '5':
            show_stats()
        elif choice == '6':
            cleanup_old_messages()
        elif choice == '7':
            print("👋 Au revoir!")
            break
        else:
            print("❌ Choix invalide")

def show_stats():
    """Afficher des statistiques"""
    contacts_dir = Path("data/contacts")
    files = list(contacts_dir.glob("*.json"))
    
    if not files:
        print("📭 Aucun message")
        return
    
    subjects = {}
    dates = []
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                subject = data.get('subject', 'unknown')
                subjects[subject] = subjects.get(subject, 0) + 1
                
                date_str = data.get('received_at', '').split('T')[0]
                if date_str:
                    dates.append(date_str)
        except:
            pass
    
    print(f"\n📊 STATISTIQUES:")
    print(f"📨 Total messages: {len(files)}")
    
    print(f"\n📈 Répartition par sujet:")
    subject_names = {
        'bug': '🚨 Bugs',
        'improvement': '💡 Suggestions',
        'partnership': '🤝 Partenariats',
        'other': '❓ Autres',
        'unknown': '🤔 Inconnu'
    }
    
    for subject, count in sorted(subjects.items(), key=lambda x: x[1], reverse=True):
        name = subject_names.get(subject, subject)
        percentage = (count / len(files)) * 100
        bar = "█" * int(percentage / 5)
        print(f"  {name:20} {count:3} {percentage:5.1f}% {bar}")

def cleanup_old_messages(days=30):
    """Supprimer les vieux messages"""
    import time
    from datetime import datetime, timedelta
    
    contacts_dir = Path("data/contacts")
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    deleted = 0
    for filepath in contacts_dir.glob("*.json"):
        if filepath.stat().st_mtime < cutoff_time:
            try:
                filepath.unlink()
                deleted += 1
                print(f"🗑️ Supprimé: {filepath.name}")
            except:
                print(f"❌ Erreur suppression: {filepath.name}")
    
    print(f"\n✅ {deleted} messages supprimés (> {days} jours)")

if __name__ == "__main__":
    main()