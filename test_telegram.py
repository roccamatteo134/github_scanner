import os
import json
import requests

# Configurazione file e variabili
DB_FILE = "database_repositories.json"
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(repo_name, repo_url):
    """Invia il messaggio al bot Telegram via richiesta GET."""
    if not TOKEN or not CHAT_ID:
        print("❌ Errore: Variabili TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti negli Environment Secrets.")
        return

    text = f"🌟 *Nuova Risorsa AI*: {repo_name}\n🔗 *Link*: {repo_url}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    params = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'  # Rende il testo più carino (grassetto e link)
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f"✅ Notifica inviata: {repo_name}")
        else:
            print(f"❌ Errore API Telegram ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Eccezione durante l'invio: {e}")

def main():
    # 1. Verifica se il file esiste
    if not os.path.exists(DB_FILE):
        print(f"⚠️ File {DB_FILE} non trovato. Interrompo lo script.")
        return

    # 2. Carica i dati dal file JSON
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Gestione caso lista vuota o formato errato
        if not data or not isinstance(data, list):
            print("📭 Il database è vuoto o non è nel formato corretto (lista).")
            return

        print(f"📂 Trovate {len(data)} voci nel database. Inizio l'invio...")

        # 3. Itera e invia
        for item in data:
            # Recupera i dati (usa i nomi delle chiavi presenti nel tuo JSON)
            name = item.get('name', 'Nome non disponibile')
            url = item.get('html_url', 'URL non disponibile')
            
            send_telegram(name, url)

    except json.JSONDecodeError:
        print(f"❌ Errore critico: Il file {DB_FILE} non è un JSON valido.")
    except Exception as e:
        print(f"❌ Errore imprevisto: {e}")

if __name__ == "__main__":
    main()
