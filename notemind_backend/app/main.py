<<<<<<< HEAD
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
=======
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import core, models
from app.routers import planning, webhooks
import uvicorn
import asyncio

app = FastAPI(
    title="Notemind Backend",
    description="Интеллектуальный ассистент по продуктивности",
    version="1.0.0"
)

# Подключение роутеров
app.include_router(planning.router, prefix="/api/v1", tags=["planning"])
# app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])

@app.get("/")
async def root():
    return {"message": "Notemind API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Функция для создания таблиц при запуске
async def create_tables():
    async with core.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    await create_tables()
    print("✅ Database tables created")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
>>>>>>> origin/dev_danya
