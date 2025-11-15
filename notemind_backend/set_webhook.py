import os
import requests
from dotenv import load_dotenv

# -------------------------------------------------------------
# ВАЖНО: УКАЖИТЕ АКТУАЛЬНЫЙ АДРЕС ВАШЕГО ТУННЕЛЯ LOCAL_TUNNEL
# -------------------------------------------------------------
WEBHOOK_URL = "https://short-mails-scream.loca.lt/webhook" # Обновите перед запуском!
# -------------------------------------------------------------


load_dotenv()
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

# ТОЧНЫЙ ЭНДПОИНТ ИЗ ДОКУМЕНТАЦИИ (POST /subscriptions)
MAX_API_SET_URL = "https://platform-api.max.ru/subscriptions" 


def attempt_set_webhook(api_url: str, headers: dict, payload: dict, attempt_name: str) -> bool:
    """Выполняет одну попытку установки Webhook."""
    print(f"\n--- {attempt_name}: Установка Webhook на {api_url} ---")
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ УСПЕХ! Webhook установлен (HTTP 200 OK).")
            # Проверяем JSON-ответ, чтобы убедиться, что он вернул success
            result = response.json()
            if result.get('success') is True:
                print(f"    Ответ MAX: {result}")
                return True
            else:
                print(f"🛑 ОШИБКА. Ответ: {response.text}")
                return False
        else:
            print(f"🛑 ОШИБКА. Код: {response.status_code}. Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Критическая ошибка при запросе: {e}")
        return False

def set_webhook():
    if not MAX_BOT_TOKEN:
        print("❌ ОШИБКА: MAX_BOT_TOKEN не найден. Проверьте .env")
        return
    
    # 1. СТРАТЕГИЯ АВТОРИЗАЦИИ: ТОЧНОЕ СООТВЕТСТВИЕ ДОКУМЕНТАЦИИ MAX
    # Документация: "Authorization: <token>" (без префикса)
    headers_max_compliant = {"Authorization": f"{MAX_BOT_TOKEN}", "Content-Type": "application/json"}
    
    # 2. ТЕЛО ЗАПРОСА: SubscriptionRequestBody требует URL и update_types
    payload = {
        "url": WEBHOOK_URL,
        "update_types": [
            "message_created", # Основные сообщения от пользователя (критично)
            "message_callback", # Нажатие кнопок (для мини-приложения)
            "bot_started"      # Когда пользователь нажимает /start
        ]
    }
    
    # --- ВЫПОЛНЕНИЕ ПОПЫТКИ ---
    
    # Попытка 1: Используем точный метод /subscriptions с MAX-Compliant заголовком
    success = attempt_set_webhook(MAX_API_SET_URL, headers_max_compliant, payload, "Попытка 1 (ПОСЛЕДНЯЯ) - POST /subscriptions")
    if success: return
    
    print("\n--- Финальная ошибка: Проблема в правах доступа к токену. ---")


if __name__ == "__main__":
    set_webhook()