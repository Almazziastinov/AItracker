import asyncio
import os
from typing import List, TypedDict, Annotated, Dict
import operator
from datetime import datetime

from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, BaseMessage, ToolMessage, SystemMessage
from langchain.tools import tool
from langgraph.graph import StateGraph, END

from app.crud import actions
from app.services.ai_planner import plan_task
from app.services import maps

# --- Загрузка конфигурации ---
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
if not GIGACHAT_CREDENTIALS:
    raise ValueError("GIGACHAT_CREDENTIALS не найден в .env файле!")

# --- Системный промпт для агента ---
SYSTEM_PROMPT = f"""Ты — умный ассистент-планировщик Notemind. Твоя задача — помочь пользователю организовать его жизнь.
Текущая дата: {datetime.now().strftime('%Y-%m-%d')}.

Твоя главная цель — извлечь из сообщения пользователя ВСЕ возможные сущности (события, задачи, метрики здоровья) и вызвать для каждой из них соответствующий инструмент.

**Порядок действий:**
1.  **Полный анализ:** Внимательно прочти все сообщение. Найди в нем все упоминания событий, задач и состояний здоровья.
2.  **Параллельный вызов инструментов:** Для КАЖДОЙ найденной сущности вызови соответствующий инструмент. Ты можешь и должен вызывать несколько инструментов за один раз, если в сообщении несколько разных действий.
    *   `create_event`: для событий с точным временем.
    *   `create_task`: для задач, которые нужно сделать.
    *   `log_health_metric`: для записей о самочувствии.
    *   `get_travel_time`: **ОСОБЫЙ СЛУЧАЙ**. Если в событии есть адрес, но не указано место отправления, твоим ПЕРВЫМ действием ДОЛЖЕН быть вызов `get_travel_time`. После получения ответа от пользователя с уточнением адреса, ты сможешь создать событие.
3.  **Итоговый отчет:** После того, как все инструменты отработают, составь единый, краткий и дружелюбный отчет для пользователя. Например: "Готово! Добавил событие 'Созвон' на завтра в 10:00, задачу 'Сделать лабу' и отметил, что вы плохо спали." Не нужно спрашивать "Все верно?". Просто констатируй факт.

**Помощь пользователю:**
- Если пользователь прямо спрашивает "что ты умеешь?", "помощь" или "help", твоя задача — предоставить краткую инструкцию.
- В инструкции опиши свои три основные функции: создание событий, создание задач и запись о самочувствии.
- Приведи примеры фраз для каждой функции:
    - **Событие:** "Завтра в 11 встреча с инвестором"
    - **Задача:** "Нужно не забыть купить молоко" или "сделать презентацию (2 часа)"
    - **Самочувствие:** "Сегодня я чувствую себя отлично" или "плохо спал"
"""

# --- Состояние графа (AgentState) ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: int

# --- Инструменты (Tools) ---
# ВНИМАНИЕ: Это функции-заглушки.

@tool
async def create_event(user_id: int, title: str, start_time: str) -> str:
    """Создает событие с фиксированным временем в календаре. Не используй этот инструмент для сохранения адреса."""
    print(f"--- ИНСТРУМЕНТ: create_event для user_id={user_id} ---")
    await actions.save_event(user_id, title, start_time, location=None) # Location теперь всегда None
    return f"Событие '{title}' на {start_time} успешно сохранено."

@tool
async def create_task(user_id: int, title: str, duration_hours: float = None, deadline: str = None) -> str:
    """
    Создает задачу. Если указана длительность, пытается автоматически запланировать ее в календаре.
    """
    print(f"--- ИНСТРУМЕНТ: create_task для user_id={user_id} ---")
    
    # 1. Сохраняем саму задачу
    task = await actions.save_task(user_id, title, duration_hours, deadline)
    
    # 2. Если есть длительность, пытаемся ее запланировать
    if duration_hours:
        print(f"    -> У задачи есть длительность, запускаем планировщик...")
        planned_event = await plan_task(task, user_id)
        
        if planned_event:
            planned_time = datetime.fromisoformat(planned_event['start_time']).strftime('%d %B в %H:%M')
            return f"Задача '{title}' создана и автоматически запланирована на {planned_time}."
        else:
            return f"Задача '{title}' создана, но найти свободный слот для планирования не удалось."
            
    return f"Задача '{title}' успешно создана (без времени в календаре)."

@tool
async def log_health_metric(user_id: int, metric: str, value: str) -> str:
    """Записывает метрику о самочувствии пользователя."""
    print(f"--- ИНСТРУМЕНТ: log_health_metric для user_id={user_id} ---")
    await actions.save_health_metric(user_id, metric, value)
    return f"Запись о самочувствии '{metric}: {value}' сохранена."

@tool
async def get_travel_time(origin_address: str, destination_address: str) -> str:
    """
    Рассчитывает время в пути между двумя адресами.
    """
    print(f"--- ИНСТРУМЕНТ: get_travel_time ---")

    # --- Имитация получения профиля пользователя ---
    # В реальном приложении этот город нужно будет брать из базы данных
    user_home_city = "Москва" 
    print(f"    Имитация профиля: домашний город пользователя - {user_home_city}")
    # -----------------------------------------

    # В реальном приложении 'дом' нужно заменять на реальный адрес из профиля пользователя
    if origin_address.lower() in ["дом", "из дома", "от дома"]:
        origin_address = user_home_city 

    # Получаем координаты домашнего города для более точного поиска
    bias_coords = maps.get_coords_by_address(user_home_city)

    # Ищем адрес назначения с привязкой к домашнему городу
    destination_coords = maps.get_coords_by_address(destination_address, bias_coords=bias_coords)
    if not destination_coords:
        return f"Не удалось найти координаты для адреса назначения: {destination_address}"

    # Ищем адрес отправления (он может быть не из домашнего города, поэтому без привязки)
    origin_coords = maps.get_coords_by_address(origin_address)
    if not origin_coords:
        return f"Не удалось найти координаты для адреса отправления: {origin_address}"

    time_minutes = maps.get_travel_time(origin_coords, destination_coords)
    
    return f"Расчетное время в пути от '{origin_address}' до '{destination_address}' составляет {time_minutes} минут."


# ... Другие инструменты, такие как get_travel_time и schedule_task, могут быть добавлены позже
tools = [create_event, create_task, log_health_metric, get_travel_time]

# --- Настройка LLM ---
llm = GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False, scope="GIGACHAT_API_PERS")
llm_with_tools = llm.bind_tools(tools)

# --- Узлы графа (Nodes) ---
async def call_model(state: AgentState):
    print("--- УЗЕЛ: call_model ---")
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

async def call_tools_node(state: AgentState):
    print("--- УЗЕЛ: call_tools_node ---")
    tool_messages = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        tool_input["user_id"] = state["user_id"] # Внедряем user_id
        print(f"Вызов: {tool_name} с {tool_input}")
        selected_tool = next((t for t in tools if t.name == tool_name), None)
        if selected_tool:
            message = await selected_tool.ainvoke(tool_input)
            tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(message)))
    return {"messages": tool_messages}

def should_continue(state: AgentState):
    print("--- УЗЕЛ: should_continue ---")
    return "tools" if state["messages"][-1].tool_calls else END

# --- Управление состоянием диалогов ---
# Простое in-memory хранилище для истории чатов.
# Ключ - user_id, значение - список сообщений.
chat_histories: Dict[int, List[BaseMessage]] = {}


# --- Построение графа ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
app_graph = workflow.compile()

# --- Функция для запуска агента ---
async def run_agent_async(user_input: str, user_id: int):
    """
    Запускает LLM-агента с поддержкой истории сообщений.
    """
    # 1. Получаем историю сообщений для данного пользователя
    # Если истории нет, создаем новую с системным промптом
    messages = chat_histories.get(user_id, [SystemMessage(content=SYSTEM_PROMPT)])
    
    # 2. Добавляем новое сообщение от пользователя в историю
    messages.append(HumanMessage(content=user_input))
    
    # 3. Вызываем графа с полной историей сообщений
    final_state = await app_graph.ainvoke({
        "messages": messages,
        "user_id": user_id,
    })
    
    # 4. Получаем последнее сообщение (ответ агента)
    response_message = final_state["messages"][-1]
    
    # 5. Обновляем историю, добавляя и сообщение пользователя, и ответ агента
    # Мы уже добавили HumanMessage, теперь добавим ответ
    chat_histories[user_id] = messages + [response_message]

    # 6. Возвращаем только текст ответа
    return response_message.content