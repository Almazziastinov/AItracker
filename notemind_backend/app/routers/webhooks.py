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
MAX_API_URL = "https://platform-api.max.ru/messages/send" 

router = APIRouter()

# --- Вспомогательная функция для отправки сообщений MAX ---
def send_max_message(user_id: str, text: str):
    """Отправляет ответное сообщение пользователю через API MAX."""
    if not MAX_BOT_TOKEN:
        print("ERROR: MAX_BOT_TOKEN not found. Cannot send message.")
        return
        
    headers = {
        "Authorization": f"Bearer {MAX_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_id": user_id, 
        "text": text,
    }
    try:
        response = requests.post(MAX_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Отправлено в MAX: {text}")
    except Exception as e:
        print(f"Ошибка отправки сообщения в MAX: {e}")
# ----------------------------------------------------------


@router.post("/")
async def handle_max_update(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Основной обработчик входящих сообщений от MAX.
    """
    
    try:
        # 1. Получение данных от MAX
        data = await request.json()
    except Exception:
        # Если пришел невалидный JSON
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    # Извлечение данных пользователя и текста сообщения
    max_user_id = str(data.get("user_id")) # ID пользователя MAX
    message_text = data.get("message", {}).get("text")
    
    if not message_text or not max_user_id:
        return {"status": "ignore", "detail": "No text or user_id found"}
        
    # --- 2. Аутентификация / Регистрация Пользователя ---
    user = await get_user_by_max_id(db, max_user_id)
    if not user:
        # Если пользователь не найден, создаем его
        try:
            user_data = UserCreate(max_user_id=max_user_id).model_dump(mode='json')
            # Передаем словарь (результат json.loads(user_data))
            user = await create_user(db, json.loads(user_data))
            
            send_max_message(max_user_id, "🎉 Добро пожаловать в Notemind! Я ваш AI-ассистент. Попробуйте: 'Завтра в 10 созвон, и я плохо спал'.")
        except Exception as e:
            print(f"ERROR creating user: {e}")
            send_max_message(max_user_id, "Ошибка при регистрации. Проверьте настройки БД.")
            return {"status": "user_creation_error"}

    user_id = user.id 
    
    # --- 3. Вызов LLM-Агента (Участник 1) ---
    try:
        # LLM-агент сам обрабатывает текст, вызывает CRUD и Maps, и возвращает финальный ответ.
        agent_final_reply = await run_agent_async(message_text, user_id)
        
        # --- 4. Отправка ответа пользователю ---
        send_max_message(max_user_id, agent_final_reply)
        
        return {"status": "processed", "reply": agent_final_reply}

    except Exception as e:
        print(f"!!! CRITICAL AGENT ERROR: {e}")
        send_max_message(max_user_id, "Произошла критическая ошибка в работе AI-агента. Пожалуйста, проверьте логи.")
        return {"status": "agent_error"}