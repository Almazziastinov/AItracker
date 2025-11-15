from fastapi import FastAPI
from app.database import core, models
from app.routers import planning, webhooks 
import uvicorn
import asyncio

app = FastAPI(
    title="Notemind Backend",
    description="Интеллектуальный ассистент по продуктивности",
    version="1.0.0"
)

# Функция для создания таблиц при запуске
async def create_tables():
    # Используем движок из core.py
    async with core.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    # Запускается при старте сервера
    await create_tables()
    print("✅ Database tables created")

# Подключение роутеров
# 1. Роутер планирования (для фронтенда /api/v1)
app.include_router(planning.router, prefix="/api/v1", tags=["planning"]) 

# 2. АКТИВАЦИЯ WEBHOOK (Для входящих запросов от MAX)
# Подключаем роутер без префикса, чтобы он слушал адрес /webhook
app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"]) 

@app.get("/")
async def root():
    return {"message": "Notemind API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Добавляем log_level="debug"
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")