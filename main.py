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
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_history(history):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(history), f)

def send_telegram(repo_name, repo_url, description):
    """Invia il messaggio al bot Telegram via richiesta GET."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ Errore: Variabili TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti.")
        return

    # Tronca la descrizione se troppo lunga (Telegram ha dei limiti)
    short_desc = (description[:200] + '...') if description and len(description) > 200 else (description or "Nessuna descrizione disponibile.")

    text = (
        f"🌟 *Nuova Risorsa AI*: {repo_name}\n\n"
        f"📝 *Descrizione*: {short_desc}\n\n"
        f"🔗 [Apri su GitHub]({repo_url})"
    )
    
    base_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {
        'chat_id': TG_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            print(f"✅ Notifica inviata: {repo_name}")
        else:
            print(f"❌ ERRORE TELEGRAM: {response.status_code}")
    except Exception as e:
        print(f"❌ Eccezione invio: {e}")

def scan():
    history = get_history()
    headers = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
    
    queries = [
        "topic:mcp stars:>=1500", 
        "topic:ai-agents stars:>=1500",
        "topic:copilot-extension stars:>=1500",
        "topic:llm-tool stars:>=1500"
    ]

    msg_sent_this_session = 0
    MAX_MESSAGES = 5  # Limite di messaggi per esecuzione

    for q in queries:
        if msg_sent_this_session >= MAX_MESSAGES:
            break

        for page in range(1, 11):
            if msg_sent_this_session >= MAX_MESSAGES:
                break
                
            try:
                print(f"🔍 Scansione: {q} (Pagina {page})")
                url = f"https://api.github.com/search/repositories?q={q}&sort=created&order=desc&per_page=100&page={page}"
                res = requests.get(url, headers=headers, timeout=15)
                
                if res.status_code != 200:
                    print(f"⚠️ Errore GitHub API: {res.status_code}")
                    break

                items = res.json().get('items', [])
                if not items:
                    break

                for repo in items:
                    if msg_sent_this_session >= MAX_MESSAGES:
                        print("ℹ️ Raggiunto il limite di 5 messaggi per questa sessione.")
                        break

                    repo_id = str(repo['id'])
                    if repo_id not in history:
                        name = repo['full_name']
                        link = repo['html_url']
                        desc = repo.get('description', "Nessuna descrizione.")
                        
                        send_telegram(name, link, desc)
                        
                        history.add(repo_id)
                        msg_sent_this_session += 1
                        
            except Exception as e:
                print(f"Errore query {q}: {e}")
                break

    save_history(history)

if __name__ == "__main__":
    scan()
