from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла в корне проекта
# Это нужно сделать до импорта других модулей, которые их используют
load_dotenv()

from fastapi import FastAPI
from app.routers import planning, webhooks

# Создаем экземпляр FastAPI
app = FastAPI(
    title="Notemind API",
    description="API для интеллектуального планировщика Notemind",
    version="0.1.0",
)

# Подключаем роутеры
app.include_router(planning.router, prefix="/api/v1", tags=["AI-Планирование"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Вебхуки"])

@app.get("/", tags=["Root"])
async def read_root():
    """
    Корневой эндпоинт для проверки работоспособности API.
    """
    return {"message": "Welcome to Notemind API!"}
