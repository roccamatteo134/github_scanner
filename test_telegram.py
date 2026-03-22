import os
import requests

# Recupera i segreti passati dalla Action
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(repo_name, repo_url):
    # Usiamo lo stesso metodo del browser: parametri nell'URL (GET)
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    text = f"🌟 Nuova Risorsa AI: {repo_name}\nLink: {repo_url}"
    
    # Costruiamo l'URL esattamente come quello del tuo test
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        'chat_id': chat_id,
        'text': text
    }
    
    try:
        # requests.get aggiunge automaticamente i ?chat_id=...&text=...
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print(f"✅ Notifica inviata per {repo_name}")
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Errore durante l'invio: {e}")

if __name__ == "__main__":
    test_send()
