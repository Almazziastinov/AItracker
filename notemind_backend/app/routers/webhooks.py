import os
import requests
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# --- ИМПОРТЫ МОДУЛЕЙ ПРОЕКТА ---
# Модуль для получения сессии БД
from app.database.core import get_db
# Модели для создания пользователя
from app.database.models import UserCreate 
# CRUD функции для работы с пользователем
from app.crud.actions import get_user_by_max_id, create_user 
# Функция LLM-агента
from app.services.llm_processor import run_agent_async 

load_dotenv()
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
MAX_API_URL = "https://platform-api.max.ru/messages" 

router = APIRouter()

# --- Вспомогательная функция для отправки сообщений MAX ---
def send_max_message(user_id: str, text: str):
    """Отправляет ответное сообщение пользователю через API MAX."""
    if not MAX_BOT_TOKEN:
        print("ERROR: MAX_BOT_TOKEN not found. Cannot send message.")
        return

    # АУТЕНТИФИКАЦИЯ: токен передается как query-параметр 'access_token'
    # АДРЕСАТ: user_id также передается как query-параметр
    params = {
        "user_id": user_id,
        "access_token": MAX_BOT_TOKEN
    }

    # ТЕЛО ЗАПРОСА: текст и обязательные пустые поля
    json_body = {
        "text": text,
        "attachments": None,
        "link": None
    }

    # Заголовок Authorization не нужен
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(MAX_API_URL, headers=headers, params=params, json=json_body)
        response.raise_for_status()
        print(f"Отправлено в MAX: {text}")
    except Exception as e:
        print(f"Ошибка отправки сообщения в MAX: {e}")
# ----------------------------------------------------------


@router.post("")
async def handle_max_update(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Основной обработчик входящих сообщений от MAX.
    """
    print("\n--- WEBHOOK: Получен новый запрос ---")
    try:
        # 1. Получение данных от MAX
        data = await request.json()
        print(f"    Данные: {data}")
    except Exception:
        # Если пришел невалидный JSON
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    # Извлечение данных пользователя и текста сообщения
    sender_info = data.get("message", {}).get("sender", {})
    max_user_id = str(sender_info.get("user_id")) if sender_info.get("user_id") else None

    message_body = data.get("message", {}).get("body", {})
    message_text = message_body.get("text")
    print(f"    ID пользователя MAX: {max_user_id}, Текст: '{message_text}'")
    
    if not message_text or not max_user_id:
        return {"status": "ignore", "detail": "No text or user_id found"}
        
    # --- 2. Аутентификация / Регистрация Пользователя ---
    user = await get_user_by_max_id(db, max_user_id)
    if not user:
        print(f"    Пользователь {max_user_id} не найден. Создание нового...")
        # Если пользователь не найден, создаем его
        try:
            user_data = UserCreate(max_user_id=max_user_id).model_dump()
            # Передаем словарь напрямую
            user = await create_user(db, user_data)
            print(f"    Пользователь создан с ID: {user.id}")
            
            send_max_message(max_user_id, "🎉 Добро пожаловать в Notemind! Я ваш AI-ассистент. Попробуйте: 'Завтра в 10 созвон, и я плохо спал'.")
            # После приветствия завершаем обработку этого запроса
            return {"status": "user_created"}
        except Exception as e:
            print(f"!!! ERROR creating user: {e}")
            send_max_message(max_user_id, "Ошибка при регистрации. Проверьте настройки БД.")
            return {"status": "user_creation_error"}
    
    print(f"    Пользователь найден, внутренний ID: {user.id}")
    user_id = user.id 
    
    # --- 3. Вызов LLM-Агента (Участник 1) ---
    try:
        print("    -> Вызов LLM-агента...")
        # LLM-агент сам обрабатывает текст, вызывает CRUD и Maps, и возвращает финальный ответ.
        agent_final_reply = await run_agent_async(message_text, user_id)
        print(f"    <- Ответ агента: '{agent_final_reply}'")
        
        # --- 4. Отправка ответа пользователю ---
        print("    -> Отправка ответа в MAX...")
        send_max_message(max_user_id, agent_final_reply)
        
        print("--- WEBHOOK: Запрос успешно обработан ---")
        return {"status": "processed", "reply": agent_final_reply}

    except Exception as e:
        print(f"!!! CRITICAL AGENT ERROR: {e}")
        send_max_message(max_user_id, "Произошла критическая ошибка в работе AI-агента. Пожалуйста, проверьте логи.")
        return {"status": "agent_error"}