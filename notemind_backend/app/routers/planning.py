from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_processor import run_agent_async

# Создаем роутер
router = APIRouter()

# --- Модели данных для API (Pydantic) ---
class UserInput(BaseModel):
    """Модель для входящего запроса от пользователя."""
    user_id: int
    text: str

class AgentResponse(BaseModel):
    """Модель для ответа агента."""
    reply: str

# --- Эндпоинты ---
@router.post("/process", response_model=AgentResponse)
async def process_user_text(user_input: UserInput):
    """
    Принимает текст от пользователя, обрабатывает его с помощью LLM-агента
    и возвращает структурированный ответ.
    """
    print(f"--- API: Получен запрос для user_id={user_input.user_id} ---")
    print(f"    Текст: '{user_input.text}'")
    
    try:
        # Вызываем нашего агента
        agent_reply = await run_agent_async(user_input.text, user_input.user_id)
        
        print(f"    Ответ агента: '{agent_reply}'")
        return AgentResponse(reply=agent_reply)
    
    except Exception as e:
        # Обработка возможных ошибок во время выполнения агента
        print(f"!!! ОШИБКА API: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {e}")
