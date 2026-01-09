#!/usr/bin/env python3
"""
Script pour vérifier et gérer les messages de contact
Usage: python check_contacts.py
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import csv
import subprocess
import webbrowser

class ContactManager:
    def __init__(self):
        self.contacts_dir = Path("data/contacts")
        self.ensure_directories()
        
    def ensure_directories(self):
        """S'assurer que les dossiers existent"""
        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        
    def list_contacts(self, limit=None):
        """Lister tous les messages"""
        if not self.contacts_dir.exists():
            print("❌ Dossier 'data/contacts' introuvable")
            return []
        
        files = list(self.contacts_dir.glob("*.json"))
        
        if not files:
            print("📭 Aucun message trouvé")
            return []
        
        # Trier par date de modification (plus récent d'abord)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if limit:
            files = files[:limit]
        
        contacts = []
        print(f"\n📨 {len(files)} messages trouvés\n")
        print("="*90)
        print(f"{'N°':3} | {'Date/Heure':19} | {'Nom':25} | {'Email':25} | {'Sujet':15}")
        print("="*90)
        
        for i, filepath in enumerate(files, 1):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    contacts.append((i, filepath, data))
                    
                    # Formater la date
                    received_at = data.get('received_at', '')
                    if 'T' in received_at:
                        date_part, time_part = received_at.split('T')
                        time_part = time_part.split('.')[0][:5]
                        display_date = f"{date_part} {time_part}"
                    else:
                        display_date = received_at[:16]
                    
                    # Tronquer les noms si trop longs
                    name = f"{data.get('first_name', '')} {data.get('last_name', '')}"
                    if len(name) > 25:
                        name = name[:22] + "..."
                    
                    email = data.get('email', '')
                    if len(email) > 25:
                        email = email[:22] + "..."
                    
                    # Mapper les sujets
                    subject_map = {
                        'bug': '🚨 Bug',
                        'improvement': '💡 Suggestion',
                        'partnership': '🤝 Partenariat',
                        'other': '❓ Autre'
                    }
                    subject = subject_map.get(data.get('subject', ''), data.get('subject', 'Inconnu'))
                    if len(subject) > 15:
                        subject = subject[:12] + "..."
                    
                    print(f"{i:3} | {display_date:19} | {name:25} | {email:25} | {subject:15}")
                    
            except Exception as e:
                print(f"{i:3} | ERREUR LECTURE FICHIER: {filepath.name}")
        
        print("="*90)
        return contacts
    
    def show_contact_details(self, contact_info=None):
        """Afficher les détails d'un message spécifique"""
        if contact_info is None:
            contacts = self.list_contacts(limit=20)
            if not contacts:
                return
            
            try:
                choice = input("\n📝 Numéro du message à afficher (0 pour annuler): ").strip()
                if choice == '0':
                    return
                
                index = int(choice) - 1
                if 0 <= index < len(contacts):
                    contact_num, filepath, data = contacts[index]
                else:
                    print("❌ Choix invalide")
                    return
                    
            except (ValueError, IndexError):
                print("❌ Entrée invalide")
                return
        else:
            contact_num, filepath, data = contact_info
        
        # Afficher les détails
        print("\n" + "="*80)
        print("📄 DÉTAILS COMPLETS DU MESSAGE")
        print("="*80)
        
        # Informations fichier
        print(f"\n📁 FICHIER:")
        print(f"  Nom: {filepath.name}")
        print(f"  Chemin: {filepath.absolute()}")
        print(f"  Taille: {filepath.stat().st_size:,} octets")
        print(f"  Créé: {datetime.fromtimestamp(filepath.stat().st_ctime).strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"  Modifié: {datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Informations contact
        print(f"\n👤 INFORMATIONS CONTACT:")
        print(f"  Prénom: {data.get('first_name', 'N/A')}")
        print(f"  Nom: {data.get('last_name', 'N/A')}")
        print(f"  Email: {data.get('email', 'N/A')}")
        print(f"  Téléphone: {data.get('phone', 'Non renseigné')}")
        
        # Métadonnées
        print(f"\n📊 MÉTADONNÉES:")
        print(f"  Reçu le: {data.get('received_at', 'N/A')}")
        print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"  Adresse IP: {data.get('ip_address', 'N/A')}")
        print(f"  Navigateur: {data.get('user_agent', 'N/A')}")
        print(f"  Application: {data.get('app_name', 'N/A')}")
        print(f"  Domaine: {data.get('domain', 'N/A')}")
        
        # Sujet
        subject_map = {
            'bug': '🚨 Bug/Problème technique',
            'improvement': '💡 Amélioration/Suggestion',
            'partnership': '🤝 Demande de partenariat',
            'other': '❓ Autre demande'
        }
        print(f"\n🎯 SUJET:")
        print(f"  Type: {subject_map.get(data.get('subject'), data.get('subject', 'Inconnu'))}")
        print(f"  Code: {data.get('subject', 'N/A')}")
        
        # Message
        print(f"\n💬 MESSAGE:")
        print("-"*40)
        message = data.get('message', '')
        print(message)
        print("-"*40)
        print(f"Longueur: {len(message)} caractères")
        
        print("\n" + "="*80)
        
        # Menu d'actions
        self.show_contact_actions(filepath, data)
    
    def show_contact_actions(self, filepath, data):
        """Afficher les actions possibles pour un contact"""
        print("\n🔧 ACTIONS:")
        print("1. ✉️  Ouvrir le client email pour répondre")
        print("2. 📋 Copier l'email dans le presse-papier")
        print("3. 📄 Ouvrir le fichier JSON")
        print("4. 📝 Éditer le fichier JSON")
        print("5. 🗑️  Supprimer ce message")
        print("6. 📊 Marquer comme traité")
        print("7. ↩️  Retour à la liste")
        print("8. 🚪 Quitter")
        
        try:
            choice = input("\n👉 Votre choix (1-8): ").strip()
            
            if choice == '1':
                self.open_email_client(data.get('email', ''))
            elif choice == '2':
                self.copy_to_clipboard(data.get('email', ''))
            elif choice == '3':
                self.open_file(filepath)
            elif choice == '4':
                self.edit_file(filepath)
            elif choice == '5':
                self.delete_contact(filepath)
            elif choice == '6':
                self.mark_as_processed(filepath, data)
            elif choice == '7':
                return
            elif choice == '8':
                print("👋 Au revoir!")
                sys.exit(0)
            else:
                print("❌ Choix invalide")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrompu par l'utilisateur")
            sys.exit(0)
    
    def open_email_client(self, email):
        """Ouvrir le client email"""
        if not email or '@' not in email:
            print("❌ Email invalide")
            return
        
        try:
            # Essayer différents moyens d'ouvrir le client email
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", f"mailto:{email}"])
            elif sys.platform == "win32":  # Windows
                os.startfile(f"mailto:{email}")
            else:  # Linux
                subprocess.run(["xdg-open", f"mailto:{email}"])
            print(f"✅ Client email ouvert pour: {email}")
        except:
            print(f"📧 Email à copier: {email}")
    
    def copy_to_clipboard(self, text):
        """Copier du texte dans le presse-papier"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run("pbcopy", universal_newlines=True, input=text)
            elif sys.platform == "win32":  # Windows
                subprocess.run("clip", universal_newlines=True, input=text)
            else:  # Linux
                subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode())
            print("✅ Texte copié dans le presse-papier")
        except:
            print("❌ Impossible de copier dans le presse-papier")
            print(f"📋 Texte à copier manuellement: {text}")
    
    def open_file(self, filepath):
        """Ouvrir le fichier"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(filepath)])
            elif sys.platform == "win32":  # Windows
                os.startfile(str(filepath))
            else:  # Linux
                subprocess.run(["xdg-open", str(filepath)])
            print(f"✅ Fichier ouvert: {filepath.name}")
        except:
            print(f"❌ Impossible d'ouvrir le fichier")
            print(f"📍 Chemin: {filepath.absolute()}")
    
    def edit_file(self, filepath):
        """Éditer le fichier avec l'éditeur par défaut"""
        try:
            editor = os.environ.get('EDITOR', 'nano' if sys.platform != 'win32' else 'notepad')
            subprocess.run([editor, str(filepath)])
            print(f"✅ Fichier édité: {filepath.name}")
        except Exception as e:
            print(f"❌ Erreur édition: {e}")
            print(f"📍 Éditez manuellement: {filepath.absolute()}")
    
    def delete_contact(self, filepath):
        """Supprimer un contact"""
        try:
            confirm = input(f"⚠️  Supprimer '{filepath.name}' ? (o/N): ").strip().lower()
            if confirm == 'o' or confirm == 'oui':
                filepath.unlink()
                print(f"✅ Supprimé: {filepath.name}")
            else:
                print("❌ Suppression annulée")
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
    
    def mark_as_processed(self, filepath, data):
        """Marquer un message comme traité"""
        try:
            data['processed'] = True
            data['processed_at'] = datetime.now().isoformat()
            data['processed_by'] = os.environ.get('USER', 'admin')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Message marqué comme traité")
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def show_statistics(self):
        """Afficher des statistiques"""
        files = list(self.contacts_dir.glob("*.json"))
        
        if not files:
            print("📭 Aucun message")
            return
        
        subjects = {}
        dates = {}
        processed_count = 0
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Compter par sujet
                    subject = data.get('subject', 'unknown')
                    subjects[subject] = subjects.get(subject, 0) + 1
                    
                    # Compter par date
                    date_str = data.get('received_at', '').split('T')[0]
                    if date_str:
                        dates[date_str] = dates.get(date_str, 0) + 1
                    
                    # Compter les traités
                    if data.get('processed'):
                        processed_count += 1
                        
            except:
                pass
        
        print("\n📊 STATISTIQUES DÉTAILLÉES")
        print("="*60)
        
        print(f"\n📨 TOTAUX:")
        print(f"  Messages totaux: {len(files)}")
        print(f"  Messages traités: {processed_count}")
        print(f"  Messages non traités: {len(files) - processed_count}")
        
        print(f"\n📈 RÉPARTITION PAR SUJET:")
        subject_names = {
            'bug': '🚨 Bugs/Problèmes',
            'improvement': '💡 Suggestions',
            'partnership': '🤝 Partenariats',
            'other': '❓ Autres demandes',
            'unknown': '🤔 Inconnu'
        }
        
        for subject, count in sorted(subjects.items(), key=lambda x: x[1], reverse=True):
            name = subject_names.get(subject, subject.capitalize())
            percentage = (count / len(files)) * 100
            bar = "█" * int(percentage / 2)  # Barre plus courte
            print(f"  {name:25} {count:3} messages {percentage:5.1f}% {bar}")
        
        print(f"\n📅 ACTIVITÉ PAR DATE (7 derniers jours):")
        today = datetime.now().date()
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            count = dates.get(date_str, 0)
            if count > 0:
                print(f"  {date.strftime('%d/%m/%Y')}: {count:2} message{'s' if count > 1 else ''}")
        
        print("\n📁 INFORMATIONS SYSTÈME:")
        total_size = sum(f.stat().st_size for f in files)
        print(f"  Taille totale: {total_size:,} octets")
        print(f"  Taille moyenne: {total_size//len(files):,} octets par message")
        
        # Ancien et récent
        if files:
            oldest = min(files, key=lambda x: x.stat().st_mtime)
            newest = max(files, key=lambda x: x.stat().st_mtime)
            print(f"  Plus ancien: {oldest.name} ({datetime.fromtimestamp(oldest.stat().st_mtime).strftime('%d/%m/%Y')})")
            print(f"  Plus récent: {newest.name} ({datetime.fromtimestamp(newest.stat().st_mtime).strftime('%d/%m/%Y %H:%M')})")
        
        print("="*60)
    
    def export_contacts(self, format_type='json'):
        """Exporter les contacts"""
        files = list(self.contacts_dir.glob("*.json"))
        
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
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            output_file = f"contacts_export_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(contacts, f, indent=2, ensure_ascii=False)
            print(f"✅ Exporté vers {output_file} ({len(contacts)} messages)")
            
        elif format_type == 'csv':
            output_file = f"contacts_export_{timestamp}.csv"
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # En-têtes
                writer.writerow([
                    'Date', 'Heure', 'Prénom', 'Nom', 'Email', 
                    'Téléphone', 'Sujet', 'Message', 'IP', 'Traité'
                ])
                
                for contact in contacts:
                    # Séparer date et heure
                    received = contact.get('received_at', '')
                    if 'T' in received:
                        date_part, time_part = received.split('T')
                        time_part = time_part.split('.')[0]
                    else:
                        date_part = received[:10]
                        time_part = received[11:19] if len(received) > 10 else ''
                    
                    writer.writerow([
                        date_part,
                        time_part,
                        contact.get('first_name', ''),
                        contact.get('last_name', ''),
                        contact.get('email', ''),
                        contact.get('phone', ''),
                        contact.get('subject', ''),
                        contact.get('message', '')[:500],  # Limiter la taille
                        contact.get('ip_address', ''),
                        'Oui' if contact.get('processed') else 'Non'
                    ])
            print(f"✅ Exporté vers {output_file} ({len(contacts)} messages)")
    
    def cleanup_old_messages(self, days=30, confirm=True):
        """Supprimer les vieux messages"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        old_files = []
        for filepath in self.contacts_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                old_files.append(filepath)
        
        if not old_files:
            print(f"✅ Aucun message plus vieux que {days} jours")
            return
        
        print(f"\n🗑️  MESSAGES À SUPPRIMER (> {days} jours):")
        for filepath in old_files:
            print(f"  • {filepath.name} ({datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%d/%m/%Y')})")
        
        if confirm:
            response = input(f"\n⚠️  Supprimer {len(old_files)} messages ? (o/N): ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("❌ Annulé")
                return
        
        deleted = 0
        for filepath in old_files:
            try:
                filepath.unlink()
                deleted += 1
            except Exception as e:
                print(f"❌ Erreur suppression {filepath.name}: {e}")
        
        print(f"✅ {deleted}/{len(old_files)} messages supprimés")
    
    def search_contacts(self, search_term):
        """Rechercher dans les messages"""
        files = list(self.contacts_dir.glob("*.json"))
        
        if not files:
            print("📭 Aucun message")
            return []
        
        results = []
        print(f"\n🔍 RECHERCHE DE: '{search_term}'")
        print("="*90)
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Rechercher dans tous les champs
                    search_text = json.dumps(data, ensure_ascii=False).lower()
                    if search_term.lower() in search_text:
                        results.append((filepath, data))
                        
                        # Afficher un aperçu
                        print(f"\n📄 {filepath.name}")
                        print(f"   👤 {data.get('first_name')} {data.get('last_name')}")
                        print(f"   📧 {data.get('email')}")
                        print(f"   🎯 {data.get('subject')}")
                        
                        # Afficher la partie du message contenant le terme
                        message = data.get('message', '').lower()
                        idx = message.find(search_term.lower())
                        if idx != -1:
                            start = max(0, idx - 50)
                            end = min(len(message), idx + len(search_term) + 50)
                            snippet = message[start:end]
                            if start > 0:
                                snippet = "..." + snippet
                            if end < len(message):
                                snippet = snippet + "..."
                            print(f"   📝 {snippet}")
                        
            except Exception as e:
                print(f"❌ Erreur lecture {filepath.name}: {e}")
        
        print("\n" + "="*90)
        print(f"✅ {len(results)} résultats trouvés")
        
        if results:
            try:
                choice = input("\n📝 Numéro du premier résultat à afficher (0 pour annuler): ").strip()
                if choice != '0':
                    index = int(choice) - 1
                    if 0 <= index < len(results):
                        filepath, data = results[index]
                        self.show_contact_details((index + 1, filepath, data))
            except (ValueError, IndexError):
                print("❌ Choix invalide")
        
        return results

def main_menu():
    """Menu principal"""
    manager = ContactManager()
    
    while True:
        print("\n" + "="*60)
        print("📨 GESTIONNAIRE DE MESSAGES - PDF FUSION PRO")
        print("="*60)
        print("\n📋 MENU PRINCIPAL:")
        print("1. 📄 Lister les messages (20 plus récents)")
        print("2. 📊 Afficher toutes les statistiques")
        print("3. 🔍 Rechercher dans les messages")
        print("4. 📥 Exporter les messages (JSON/CSV)")
        print("5. 🗑️  Nettoyer les vieux messages (>30 jours)")
        print("6. 📁 Vérifier le dossier des contacts")
        print("7. 🆘 Aide et informations")
        print("8. 🚪 Quitter")
        
        try:
            choice = input("\n👉 Votre choix (1-8): ").strip()
            
            if choice == '1':
                manager.list_contacts(limit=20)
                sub_choice = input("\n📝 Afficher un message détaillé ? (numéro ou 0 pour menu): ").strip()
                if sub_choice != '0':
                    try:
                        index = int(sub_choice) - 1
                        contacts = manager.list_contacts(limit=20)
                        if 0 <= index < len(contacts):
                            contact_num, filepath, data = contacts[index]
                            manager.show_contact_details((contact_num, filepath, data))
                    except:
                        print("❌ Choix invalide")
                        
            elif choice == '2':
                manager.show_statistics()
                
            elif choice == '3':
                search_term = input("\n🔍 Terme à rechercher: ").strip()
                if search_term:
                    manager.search_contacts(search_term)
                    
            elif choice == '4':
                print("\n📥 FORMAT D'EXPORT:")
                print("1. JSON (complet)")
                print("2. CSV (Excel/tableur)")
                format_choice = input("\n👉 Votre choix (1-2): ").strip()
                if format_choice == '1':
                    manager.export_contacts('json')
                elif format_choice == '2':
                    manager.export_contacts('csv')
                else:
                    print("❌ Choix invalide")
                    
            elif choice == '5':
                try:
                    days = int(input("\n🗑️  Supprimer les messages plus vieux que (jours): ").strip())
                    if days > 0:
                        manager.cleanup_old_messages(days=days)
                    else:
                        print("❌ Nombre de jours invalide")
                except ValueError:
                    print("❌ Entrée invalide")
                    
            elif choice == '6':
                manager.ensure_directories()
                files = list(manager.contacts_dir.glob("*.json"))
                print(f"\n📁 DOSSIER: {manager.contacts_dir.absolute()}")
                print(f"📦 {len(files)} fichiers JSON")
                if files:
                    size = sum(f.stat().st_size for f in files)
                    print(f"💾 Taille totale: {size:,} octets")
                    
            elif choice == '7':
                print("\n🆘 AIDE:")
                print("• Les messages sont sauvegardés dans data/contacts/")
                print("• Chaque message est un fichier JSON")
                print("• Vous pouvez exporter en JSON ou CSV")
                print("• Utilisez la recherche pour trouver des messages spécifiques")
                print("• Les vieux messages (>30j) peuvent être nettoyés automatiquement")
                print(f"\n📍 Chemin actuel: {Path.cwd()}")
                
            elif choice == '8':
                print("\n👋 Au revoir !")
                break
                
            else:
                print("❌ Choix invalide")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrompu par l'utilisateur")
            break

if __name__ == "__main__":
    # Vérifier si le script est exécuté directement
    if len(sys.argv) > 1:
        # Mode ligne de commande
        manager = ContactManager()
        if sys.argv[1] == "list":
            manager.list_contacts()
        elif sys.argv[1] == "stats":
            manager.show_statistics()
        elif sys.argv[1] == "export":
            format_type = sys.argv[2] if len(sys.argv) > 2 else "json"
            manager.export_contacts(format_type)
        elif sys.argv[1] == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            manager.cleanup_old_messages(days=days, confirm=False)
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            manager.search_contacts(sys.argv[2])
        else:
            print("Usage: python check_contacts.py [list|stats|export|cleanup|search]")
    else:
        # Mode interactif
        main_menu()