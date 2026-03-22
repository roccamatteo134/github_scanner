import os
import requests

# Recupera i segreti passati dalla Action
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def test_send():
    if not TG_TOKEN or not TG_CHAT_ID:
        print(f"❌ ERRORE: Variabili mancanti!")
        print(f"TOKEN presente: {bool(TG_TOKEN)}")
        print(f"CHAT_ID presente: {bool(TG_CHAT_ID)}")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        'chat_id': TG_CHAT_ID,
        'text': "Ciao! Se ricevi questo messaggio, il collegamento GitHub -> Telegram funziona correttamente. 🚀",
        'parse_mode': 'Markdown'
    }

    print(f"Tentativo di invio a ID: {TG_CHAT_ID}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ TEST SUPERATO: Messaggio inviato!")
        else:
            print(f"❌ TEST FALLITO: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ ERRORE CRITICO: {e}")

if __name__ == "__main__":
    test_send()
