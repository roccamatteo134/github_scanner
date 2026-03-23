import requests
import json
import os
import urllib.parse

# Configurazione Secrets
GH_TOKEN = os.getenv('GH_TOKEN')
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DB_FILE = 'database_notifiche.json'

def get_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_history(history):
    with open(DB_FILE, 'w') as f:
        json.dump(list(history), f)

def send_telegram(repo_name, repo_url):
    """Invia il messaggio al bot Telegram via richiesta GET con debug dell'URL."""
    
    # Verifica variabili globali
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ Errore: Variabili TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti.")
        return

    # Prepariamo il testo
    text = f"🌟 *Nuova Risorsa AI*: {repo_name}\n🔗 *Link*: {repo_url}"
    
    # Costruzione URL con Path Parameter (il Token fa parte del path)
    base_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        params = {
        'chat_id': TG_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    query_string = urllib.parse.urlencode(params)
    full_debug_url = f"{base_url}?{query_string}"
    
    print(f"📡 Tentativo di invio URL: {full_debug_url}")
    
    try:
        # requests.get gestisce internamente la pulizia dei caratteri speciali (encoding)
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Notifica inviata con successo per: {repo_name}")
        else:
            print(f"❌ ERRORE TELEGRAM: {response.status_code} - {response.text}")
            # Se l'errore è 400, l'URL stampato sopra ti aiuterà a capire se l'ID è sbagliato
            
    except Exception as e:
        print(f"❌ Eccezione durante l'invio: {e}")

def scan():
    history = get_history()
    headers = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
    
    queries = [
        "topic:mcp+stars:>1500", 
        "topic:ai-agents+stars:>1500",
        "topic:copilot-extension",
        "topic:llm-tool+stars:>1500"
    ]

    for q in queries:
        try:
            print(f"🔍 Scansione query: {q}")
            res = requests.get(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc", headers=headers)
            
            if res.status_code != 200:
                print(f"⚠️ Errore GitHub API ({res.status_code}): {res.text}")
                continue

            items = res.json().get('items', [])
            for repo in items:
                repo_id = str(repo['id'])
                if repo_id not in history:
                    # CORREZIONE: Passiamo i due argomenti richiesti dalla funzione
                    send_telegram(repo['full_name'], repo['html_url'])
                    history.add(repo_id)
        except Exception as e:
            print(f"Errore query {q}: {e}")

    save_history(history)

if __name__ == "__main__":
    scan()
