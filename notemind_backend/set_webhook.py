import os
import requests
from dotenv import load_dotenv

# -------------------------------------------------------------
# ВАЖНО: УКАЖИТЕ АКТУАЛЬНЫЙ АДРЕС ВАШЕГО ТУННЕЛЯ LOCAL_TUNNEL
# -------------------------------------------------------------
WEBHOOK_URL = "https://short-mails-scream.loca.lt/webhook"
# -------------------------------------------------------------


load_dotenv()
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
MAX_API_URL = "https://platform-api.max.ru/setWebhook" # Предполагаемый эндпоинт для установки

def set_webhook():
    if not MAX_BOT_TOKEN:
        print("❌ ОШИБКА: MAX_BOT_TOKEN не найден. Проверьте .env")
        return
    
    print(f"--- 1. Установка Webhook на адрес: {WEBHOOK_URL} ---")
    
    headers = {
        "Authorization": f"Bearer {MAX_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": WEBHOOK_URL,
        # Здесь могут быть дополнительные параметры, если MAX их требует
    }
    
    try:
        response = requests.post(MAX_API_URL, headers=headers, json=payload)
        
        # Проверяем ответ
        if response.status_code == 200:
            print("✅ Webhook успешно установлен (HTTP 200 OK).")
            print(f"    Ответ MAX: {response.json()}")
        else:
            print(f"🛑 ОШИБКА УСТАНОВКИ WEBHOOK. Код: {response.status_code}")
            print(f"    Ответ: {response.text}")

    except Exception as e:
        print(f"❌ Критическая ошибка при запросе к серверу MAX: {e}")

if __name__ == "__main__":
    set_webhook()