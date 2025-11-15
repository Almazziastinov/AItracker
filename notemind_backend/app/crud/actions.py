# Этот файл будет содержать CRUD-операции (Create, Read, Update, Delete)
# Временное решение: хранение данных в памяти
# В будущем это будет заменено на реальные запросы к базе данных

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from datetime import datetime, timedelta
from app.database import models

# --- Имитация базы данных ---
mock_db: Dict[str, List[Dict[str, Any]]] = {
    "events": [],
    "tasks": [],
    "health_metrics": [],
}

# --- Функции для сохранения данных ---

async def save_event(user_id: int, title: str, start_time: str, location: str = None) -> Dict[str, Any]:
    """
    Имитирует сохранение события в базу данных.
    Возвращает созданный объект.
    """
    print(f"--- CRUD-ДЕЙСТВИЕ: Сохранение события для user_id={user_id} ---")
    event = {
        "user_id": user_id,
        "title": title,
        "start_time": start_time,
        "location": location,
        "id": len(mock_db["events"]) + 1
    }
    mock_db["events"].append(event)
    print(f"    Событие сохранено: {event}")
    return event

async def save_task(user_id: int, title: str, duration_hours: float = None, deadline: str = None) -> Dict[str, Any]:
    """
    Имитирует сохранение задачи в базу данных.
    Возвращает созданный объект.
    """
    print(f"--- CRUD-ДЕЙСТВИЕ: Сохранение задачи для user_id={user_id} ---")
    task = {
        "user_id": user_id,
        "title": title,
        "duration_hours": duration_hours,
        "deadline": deadline,
        "id": len(mock_db["tasks"]) + 1
    }
    mock_db["tasks"].append(task)
    print(f"    Задача сохранена: {task}")
    return task

async def save_health_metric(user_id: int, metric: str, value: str) -> Dict[str, Any]:
    """
    Имитирует сохранение метрики здоровья в базу данных.
    Возвращает созданный объект.
    """
    print(f"--- CRUD-ДЕЙСТВИЕ: Сохранение метрики для user_id={user_id} ---")
    health_metric = {
        "user_id": user_id,
        "metric": metric,
        "value": value,
        "id": len(mock_db["health_metrics"]) + 1
    }
    mock_db["health_metrics"].append(health_metric)
    print(f"    Метрика сохранена: {health_metric}")
    return health_metric

# --- Функции для чтения данных ---

async def get_events(user_id: int) -> List[Dict[str, Any]]:
    """
    Имитирует получение всех событий для конкретного пользователя.
    """
    print(f"--- CRUD-ДЕЙСТВИЕ: Получение событий для user_id={user_id} ---")
    user_events = [event for event in mock_db["events"] if event["user_id"] == user_id]
    print(f"    Найдено событий: {len(user_events)}")
    return user_events

# --- АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ ---

# Асинхронные CRUD операции для User
async def get_user_by_max_id(db: AsyncSession, max_user_id: str):
    result = await db.execute(
        select(models.User).where(models.User.max_user_id == max_user_id)
    )
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: dict):
    db_user = models.User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user_home_address(db: AsyncSession, user_id: int, home_address: str):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if db_user:
        db_user.home_address = home_address
        await db.commit()
        await db.refresh(db_user)
    return db_user

# Асинхронные CRUD операции для Event
async def get_events_by_user_id(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Event)
        .where(models.Event.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_events_by_date_range(db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime):
    result = await db.execute(
        select(models.Event).where(
            and_(
                models.Event.user_id == user_id,
                models.Event.start_time >= start_date,
                models.Event.end_time <= end_date
            )
        )
    )
    return result.scalars().all()

async def get_event_by_id(db: AsyncSession, event_id: int):
    result = await db.execute(
        select(models.Event).where(models.Event.id == event_id)
    )
    return result.scalar_one_or_none()

async def create_event(db: AsyncSession, event_data: dict):
    db_event = models.Event(**event_data)
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

async def update_event(db: AsyncSession, event_id: int, event_data: dict):
    result = await db.execute(
        select(models.Event).where(models.Event.id == event_id)
    )
    db_event = result.scalar_one_or_none()
    if db_event:
        for key, value in event_data.items():
            setattr(db_event, key, value)
        await db.commit()
        await db.refresh(db_event)
    return db_event

async def delete_event(db: AsyncSession, event_id: int) -> bool:
    result = await db.execute(
        select(models.Event).where(models.Event.id == event_id)
    )
    db_event = result.scalar_one_or_none()
    if db_event:
        await db.delete(db_event)
        await db.commit()
        return True
    return False

# Асинхронные CRUD операции для Task
async def get_tasks_by_user_id(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Task)
        .where(models.Task.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_task_by_id(db: AsyncSession, task_id: int):
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    return result.scalar_one_or_none()

async def create_task(db: AsyncSession, task_data: dict):
    db_task = models.Task(**task_data)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def update_task(db: AsyncSession, task_id: int, task_data: dict):
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    db_task = result.scalar_one_or_none()
    if db_task:
        for key, value in task_data.items():
            setattr(db_task, key, value)
        await db.commit()
        await db.refresh(db_task)
    return db_task

async def delete_task(db: AsyncSession, task_id: int) -> bool:
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    db_task = result.scalar_one_or_none()
    if db_task:
        await db.delete(db_task)
        await db.commit()
        return True
    return False

async def get_pending_tasks_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.Task).where(
            and_(
                models.Task.user_id == user_id,
                models.Task.status == "pending"
            )
        )
    )
    return result.scalars().all()

# Асинхронные CRUD операции для HealthMetric
async def get_health_metrics_by_user(db: AsyncSession, user_id: int, metric_type: str = None):
    query = select(models.HealthMetric).where(models.HealthMetric.user_id == user_id)
    if metric_type:
        query = query.where(models.HealthMetric.metric_type == metric_type)
    
    result = await db.execute(query.order_by(models.HealthMetric.recorded_at.desc()))
    return result.scalars().all()

async def create_health_metric(db: AsyncSession, metric_data: dict):
    db_metric = models.HealthMetric(**metric_data)
    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)
    return db_metric

async def get_recent_health_metrics(db: AsyncSession, user_id: int, days: int = 7):
    cutoff_date = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(models.HealthMetric).where(
            and_(
                models.HealthMetric.user_id == user_id,
                models.HealthMetric.recorded_at >= cutoff_date
            )
        ).order_by(models.HealthMetric.recorded_at.asc())
    )
    return result.scalars().all()