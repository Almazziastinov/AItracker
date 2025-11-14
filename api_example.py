import requests
import json

# Данные для нашего запроса
url = "http://127.0.0.1:8000/api/v1/process"
payload = {
    "user_id": 777,
    "text": "сделать домашку по матану часа на 2, а потом созвон с научруком в 19:00"
}
headers = {
    "Content-Type": "application/json"
}

print("--- Отправка запроса на API... ---")
print(f"URL: {url}")
print(f"Тело запроса: {json.dumps(payload, ensure_ascii=False)}")

try:
    # Отправляем POST-запрос
    response = requests.post(url, json=payload, headers=headers, timeout=30)

    # Проверяем статус ответа
    response.raise_for_status()  # Вызовет исключение для плохих статусов (4xx, 5xx)

    print("\n--- Ответ от API получен ---")
    print(f"Статус-код: {response.status_code}")
    
    # Печатаем тело ответа
    response_json = response.json()
    print(f"Тело ответа: {json.dumps(response_json, ensure_ascii=False)}")

except requests.exceptions.RequestException as e:
    print(f"\n!!! ОШИБКА ЗАПРОСА: {e}")

except json.JSONDecodeError:
    print(f"\n!!! ОШИБКА ДЕКОДИРОВАНИЯ JSON. Ответ не является валидным JSON:")
    print(response.text)

