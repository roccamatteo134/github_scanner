import requests
import json
import os
from deep_translator import GoogleTranslator
from langdetect import detect # Nuova libreria per il rilevamento

# Configurazione Secrets
GH_TOKEN = os.getenv('GH_TOKEN')
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DB_FILE = 'database_notifiche.json'

# Mappa delle lingue comuni per i Tag
LANG_MAP = {
    'en': 'Inglese',
    'zh-cn': 'Cinese',
    'zh-tw': 'Cinese',
    'ja': 'Giapponese',
    'ko': 'Coreano',
    'fr': 'Francese',
    'de': 'Tedesco',
    'es': 'Spagnolo',
    'ru': 'Russo',
    'it': 'Italiano'
}

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

def process_description(text):
    """Rileva la lingua, traduce e restituisce (testo_tradotto, tag_lingua)."""
    if not text or text.strip() == "":
        return "Nessuna descrizione disponibile.", "N/D"
    
    try:
        # 1. Rilevamento lingua
        lang_code = detect(text)
        orig_lang = LANG_MAP.get(lang_code, lang_code.upper())
        
        # 2. Traduzione se non è già italiano
        if lang_code == 'it':
            return text, "Italiano"
        
        translated = GoogleTranslator(source='auto', target='it').translate(text)
        return translated, orig_lang
    except Exception as e:
        print(f"⚠️ Errore processamento testo: {e}")
        return text, "Sconosciuta"

def send_telegram(repo_name, repo_url, description):
    """Invia il messaggio al bot Telegram."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ Errore: Variabili Telegram mancanti.")
        return

    # Processiamo descrizione e lingua
    desc_it, lang_tag = process_description(description)
    
    # Tronca se troppo lunga
    short_desc = (desc_it[:300] + '...') if len(desc_it) > 300 else desc_it

    # Messaggio con Tag della lingua originale
    text = (
        f"🌟 *Nuova Risorsa AI*: {repo_name}\n"
        f"🌍 *Lingua originale*: {lang_tag}\n\n"
        f"🇮🇹 *Descrizione*: {short_desc}\n\n"
        f"🔗 [Apri su GitHub]({repo_url})"
    )
    
    base_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {
        'chat_id': TG_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    try:
        requests.get(base_url, params=params, timeout=10)
        print(f"✅ Notifica inviata: {repo_name} ({lang_tag})")
    except Exception as e:
        print(f"❌ Eccezione invio: {e}")

def scan():
    history = get_history()
    headers = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
    
    queries = [
        "topic:mcp stars:>=1500", 
        "topic:ai-agents stars:>=1500",
        "topic:copilot-extension stars:>=1500",
        "topic:llm-tool stars:>=1500",
        "topic:vscode-extension stars:>=1500"
    ]

    msg_sent_this_session = 0
    MAX_MESSAGES = 5 

    for q in queries:
        if msg_sent_this_session >= MAX_MESSAGES: break

        for page in range(1, 3): 
            if msg_sent_this_session >= MAX_MESSAGES: break
                
            try:
                url = f"https://api.github.com/search/repositories?q={q}&sort=created&order=desc&per_page=100&page={page}"
                res = requests.get(url, headers=headers, timeout=15)
                
                if res.status_code != 200: break

                items = res.json().get('items', [])
                for repo in items:
                    if msg_sent_this_session >= MAX_MESSAGES: break

                    repo_id = str(repo['id'])
                    if repo_id not in history:
                        send_telegram(repo['full_name'], repo['html_url'], repo.get('description'))
                        history.add(repo_id)
                        msg_sent_this_session += 1
                        
            except Exception as e:
                print(f"Errore query {q}: {e}")
                break

    save_history(history)

if __name__ == "__main__":
    scan()