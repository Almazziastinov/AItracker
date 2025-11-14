# Этот файл будет содержать CRUD-операции (Create, Read, Update, Delete)
# Временное решение: хранение данных в памяти
# В будущем это будет заменено на реальные запросы к базе данных

from typing import Dict, List, Any

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
