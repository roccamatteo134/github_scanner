import re
import requests
import json
import os
from deep_translator import GoogleTranslator
from langdetect import detect
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# Configurazione
GH_TOKEN = os.getenv('GH_TOKEN')
DB_FILE = 'database_notifiche.json'
RSS_FILE = 'feed.xml'
MAX_FEED_ITEMS = 50

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

def sanitize_xml_text(text):
    """Rimuove caratteri non validi in XML 1.0, emoji e normalizza gli a capo."""
    if not text:
        return text
    # Rimuove caratteri di controllo non permessi in XML 1.0 (raw string ok: \x is valid regex escape)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Rimuove emoji non-BMP (es. 🦍🚀📦) — stringa NON-raw: \U viene espanso da Python
    text = re.sub('[\U00010000-\U0010FFFF]', '', text)
    # Rimuove emoji e simboli BMP (stelle, frecce, dingbats, varianti) — stringa NON-raw
    text = re.sub('[\u2194-\u27FF\u2B00-\u2BFF\u3030\u303D\u3297\u3299\uFE00-\uFE0F]', '', text)
    # Sostituisce doppi a capo con separatore leggibile
    text = text.replace('\n\n', ' - ').replace('\n', ' ')
    return text

def get_history():
    """Returns set of already-seen repo URLs from feed.xml guids.
    Falls back to legacy numeric IDs from DB_FILE if feed doesn't exist yet."""
    if os.path.exists(RSS_FILE):
        try:
            tree = ET.parse(RSS_FILE)
            channel = tree.getroot().find('channel')
            return {item.findtext('guid') for item in channel.findall('item') if item.findtext('guid')}
        except ET.ParseError:
            pass
    # Legacy fallback before first migration
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            pass
    return set()

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
        print(f"[WARN] Errore processamento testo: {e}")
        return text, "Sconosciuta"

def load_or_create_feed():
    """Carica il feed RSS esistente o ne crea uno nuovo."""
    if os.path.exists(RSS_FILE):
        try:
            return ET.parse(RSS_FILE)
        except ET.ParseError:
            pass

    rss = ET.Element('rss')
    rss.set('version', '2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'GitHub AI Scanner'
    ET.SubElement(channel, 'link').text = 'https://github.com'
    ET.SubElement(channel, 'description').text = 'Nuove risorse AI trovate su GitHub'
    ET.SubElement(channel, 'language').text = 'it'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    return ET.ElementTree(rss)

def add_to_feed(repo_name, repo_url, description, stars):
    """Aggiunge un nuovo elemento al feed RSS."""
    tree = load_or_create_feed()
    channel = tree.getroot().find('channel')

    # Aggiorna lastBuildDate
    now_str = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    last_build = channel.find('lastBuildDate')
    if last_build is not None:
        last_build.text = now_str

    # Skip if already present in feed
    if any(i.findtext('guid') == repo_url for i in channel.findall('item')):
        return

    desc_it, lang_tag = process_description(description)
    short_desc = (desc_it[:500] + '...') if len(desc_it) > 500 else desc_it

    item = ET.Element('item')
    ET.SubElement(item, 'title').text = f"[{lang_tag}] {repo_name}"
    ET.SubElement(item, 'link').text = repo_url
    ET.SubElement(item, 'description').text = sanitize_xml_text(f"{stars} stelle | Lingua originale: {lang_tag} - {short_desc}")
    ET.SubElement(item, 'guid').text = repo_url
    ET.SubElement(item, 'pubDate').text = now_str

    # Inserisci in testa (più recenti prima)
    existing_items = channel.findall('item')
    if existing_items:
        channel.insert(list(channel).index(existing_items[0]), item)
    else:
        channel.append(item)

    # Mantieni al massimo MAX_FEED_ITEMS elementi
    for old in channel.findall('item')[MAX_FEED_ITEMS:]:
        channel.remove(old)

    ET.indent(tree, space='  ')
    tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)
    print(f"[OK] Aggiunto al feed: {repo_name} ({lang_tag})")

def migrate_db_to_feed():
    """Legge i repo già elaborati dal DB legacy, li importa nel feed RSS e rimuove il DB."""
    if not os.path.exists(DB_FILE):
        return

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        ids = json.load(f)

    if not ids:
        os.remove(DB_FILE)
        return

    headers = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
    print(f"[...] Migrazione di {len(ids)} repo dal database al feed RSS...")
    imported = 0

    for repo_id in ids:
        try:
            res = requests.get(
                f"https://api.github.com/repositories/{repo_id}",
                headers=headers,
                timeout=10
            )
            if res.status_code == 200:
                repo = res.json()
                add_to_feed(
                    repo['full_name'],
                    repo['html_url'],
                    repo.get('description'),
                    repo.get('stargazers_count', 0)
                )
                imported += 1
            else:
                print(f"[WARN] Repo {repo_id} non trovata (HTTP {res.status_code})")
        except Exception as e:
            print(f"[WARN] Errore recupero repo {repo_id}: {e}")

    os.remove(DB_FILE)
    print(f"[OK] Migrazione completata: {imported}/{len(ids)} repo importati. {DB_FILE} rimosso.")

def scan():
    history = get_history()
    headers = {'Authorization': f'token {GH_TOKEN}'} if GH_TOKEN else {}
    
    queries = [
        "topic:mcp stars:>=1000", 
        "topic:ai-agents stars:>=1000",
        "topic:copilot-extension stars:>=1000",
        "topic:llm-tool stars:>=1000",
        "topic:vscode-extension stars:>=1000"
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

                    repo_url = repo['html_url']
                    if repo_url not in history:
                        add_to_feed(repo['full_name'], repo_url, repo.get('description'), repo.get('stargazers_count', 0))
                        history.add(repo_url)
                        msg_sent_this_session += 1
                        
            except Exception as e:
                print(f"Errore query {q}: {e}")
                break

def repair_feed():
    """Normalizza le descrizioni nel feed.xml esistente per garantire XML ben formato."""
    if not os.path.exists(RSS_FILE):
        return
    try:
        tree = ET.parse(RSS_FILE)
    except ET.ParseError:
        return
    channel = tree.getroot().find('channel')
    changed = False
    for item in channel.findall('item'):
        desc = item.find('description')
        if desc is not None and desc.text and '\n' in desc.text:
            desc.text = sanitize_xml_text(desc.text)
            changed = True
    if changed:
        ET.indent(tree, space='  ')
        tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)
        print("[OK] feed.xml riparato: rimossi a capo dalle descrizioni.")

if __name__ == "__main__":
    repair_feed()
    migrate_db_to_feed()
    scan()