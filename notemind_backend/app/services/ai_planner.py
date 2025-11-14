from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.crud import actions

# --- Константы для планировщика ---
WORK_HOURS_START = 9  # Начало рабочего дня (9:00)
WORK_HOURS_END = 21   # Конец рабочего дня (21:00)
MIN_SLOT_MINUTES = 15 # Минимальный интервал между событиями

async def plan_task(task: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
    """
    Основная функция AI-планировщика.
    Находит свободный слот для задачи и создает событие.
    
    :param task: Словарь с данными задачи (должен содержать 'duration_hours').
    :param user_id: ID пользователя.
    :return: Созданное событие или None, если слот не найден.
    """
    print(f"--- AI-ПЛАНИРОВЩИК: Начало планирования задачи '{task.get('title')}' ---")
    
    duration_hours = task.get("duration_hours")
    if not duration_hours:
        print("    ОШИБКА: У задачи нет длительности, планирование невозможно.")
        return None

    task_duration = timedelta(hours=duration_hours)
    
    # 1. Получаем все существующие события пользователя
    user_events = await actions.get_events(user_id)
    
    # 2. Сортируем события по времени начала
    # Убедимся, что время в строковом формате ISO можно сравнивать
    sorted_events = sorted(user_events, key=lambda x: x['start_time'])
    
    # 3. Ищем свободный слот
    
    # Начинаем поиск с текущего времени, округленного до ближайших 15 минут
    search_start_time = datetime.now()
    search_start_time = search_start_time.replace(second=0, microsecond=0) + timedelta(minutes=MIN_SLOT_MINUTES - search_start_time.minute % MIN_SLOT_MINUTES)

    # Добавляем "виртуальное" событие в конце, чтобы ограничить поиск
    calendar = []
    for event in sorted_events:
        try:
            start = datetime.fromisoformat(event['start_time'])
            # Предположим, что все события длятся 1 час, если нет данных
            # В будущем это нужно будет уточнять
            end = start + timedelta(hours=event.get('duration_hours', 1))
            calendar.append({"start": start, "end": end})
        except (ValueError, TypeError):
            print(f"    ПРЕДУПРЕЖДЕНИЕ: Неверный формат времени у события: {event}")
            continue

    # Основной цикл поиска
    while True:
        # Проверяем, что время находится в пределах рабочего дня
        if not (WORK_HOURS_START <= search_start_time.hour < WORK_HOURS_END):
            # Если нет, переходим на следующее утро
            search_start_time = search_start_time.replace(hour=WORK_HOURS_START, minute=0, second=0) + timedelta(days=1)
            continue

        slot_end_time = search_start_time + task_duration
        
        # Проверяем, что слот не выходит за рамки рабочего дня
        if slot_end_time.hour > WORK_HOURS_END or (slot_end_time.hour == WORK_HOURS_END and slot_end_time.minute > 0):
            search_start_time = search_start_time.replace(hour=WORK_HOURS_START, minute=0, second=0) + timedelta(days=1)
            continue

        # Проверяем на пересечения с существующими событиями
        is_slot_free = True
        for event_slot in calendar:
            if max(search_start_time, event_slot['start']) < min(slot_end_time, event_slot['end']):
                # Найдено пересечение, слот занят.
                # Перемещаем начало поиска на конец этого события + минимальный интервал
                search_start_time = event_slot['end'] + timedelta(minutes=MIN_SLOT_MINUTES)
                is_slot_free = False
                break
        
        if is_slot_free:
            # Слот найден!
            print(f"    Найден свободный слот: {search_start_time.isoformat()}")
            
            # 4. Создаем новое событие
            new_event = await actions.save_event(
                user_id=user_id,
                title=f"Задача: {task.get('title')}",
                start_time=search_start_time.isoformat(),
                location=None # У задач пока нет локации
            )
            print("--- AI-ПЛАНИРОВЩИК: Задача успешно запланирована ---")
            return new_event

        # Если мы дошли сюда, значит, слот был занят, и search_start_time был обновлен.
        # Цикл начнется снова с нового времени.
        
        # Защита от бесконечного цикла (например, если задача длиннее рабочего дня)
        if search_start_time > datetime.now() + timedelta(days=30): # Ищем на месяц вперед
             print("    ОШИБКА: Не удалось найти свободный слот в течение 30 дней.")
             return None
