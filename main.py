import requests
import json
import os

# Configurazione Secrets
GH_TOKEN = os.getenv('GH_TOKEN')
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DB_FILE = 'database_notifiche.json'

def get_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(DB_FILE, 'w') as f:
        json.dump(list(history), f)

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

def scan():
    history = get_history()
    headers = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
    
    # Lista di query mirate per intercettare l'ecosistema AI
    queries = [
        "topic:mcp+stars:>1500", 
        "topic:ai-agents+stars:>1500",
        "topic:copilot-extension",
        "topic:llm-tool+stars:>1500"
    ]

    for q in queries:
        try:
            res = requests.get(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc", headers=headers)
            items = res.json().get('items', [])
            for repo in items:
                repo_id = str(repo['id'])
                if repo_id not in history:
                    send_telegram(repo)
                    history.add(repo_id)
        except Exception as e:
            print(f"Errore query {q}: {e}")

    save_history(history)

if __name__ == "__main__":
    scan()
