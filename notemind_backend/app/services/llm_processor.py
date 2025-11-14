import asyncio
import os
from dotenv import load_dotenv
from typing import List, TypedDict, Annotated
import operator
from datetime import datetime

from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, BaseMessage, ToolMessage, SystemMessage
from langchain.tools import tool
from langgraph.graph import StateGraph, END

# --- Загрузка конфигурации ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env'))
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
if not GIGACHAT_CREDENTIALS:
    raise ValueError("GIGACHAT_CREDENTIALS не найден в .env файле!")

# --- Системный промпт для агента ---
SYSTEM_PROMPT = f"""Ты — умный ассистент-планировщик Notemind. Твоя задача — помочь пользователю организовать его жизнь.
Анализируй сообщения пользователя, чтобы извлечь из них одно или несколько действий: создание события, создание задачи или запись о самочувствии.
Текущая дата: {datetime.now().strftime('%Y-%m-%d')}.

Правила:
1.  **Событие (Event):** Если пользователь упоминает что-то с конкретным временем (например, "в 10", "завтра в 14:30"), используй инструмент `create_event`. Обязательно извлеки название и время начала. Время и дату всегда приводи к формату ISO 8601 (YYYY-MM-DDTHH:MM:SS).
2.  **Задача (Task):** Если пользователь говорит о том, что нужно сделать, но без точного времени (например, "надо сделать лабу"), используй инструмент `create_task`. Обязательно извлеки название и, если есть, длительность или дедлайн.
3.  **Самочувствие (Health Metric):** Если пользователь упоминает свое состояние (сон, настроение, энергия), используй `log_health_metric`. Извлеки название метрики и ее значение.
4.  **Множественные действия:** В одном сообщении может быть несколько действий. Вызови все необходимые инструменты для каждого из них.
5.  **Подтверждение:** После выполнения действий всегда дружелюбно подтверждай, что ты сделал, в разговорной форме.
"""

# --- Состояние графа (AgentState) ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: int

# --- Инструменты (Tools) ---
# ВНИМАНИЕ: Это функции-заглушки.

@tool
async def create_event(user_id: int, title: str, start_time: str, location: str = None) -> str:
    """Создает событие с фиксированным временем в календаре."""
    print(f"--- ИНСТРУМЕНТ (ЗАГЛУШКА): create_event для user_id={user_id} ---")
    print(f"    Название: {title}, Время: {start_time}, Место: {location}")
    return f"Событие '{title}' на {start_time} успешно создано."

@tool
async def create_task(user_id: int, title: str, duration_hours: float = None, deadline: str = None) -> str:
    """Создает задачу, у которой есть длительность, но нет фиксированного времени начала."""
    print(f"--- ИНСТРУМЕНТ (ЗАГЛУШКА): create_task для user_id={user_id} ---")
    print(f"    Название: {title}, Длительность: {duration_hours}ч, Дедлайн: {deadline}")
    return f"Задача '{title}' успешно создана."

@tool
async def log_health_metric(user_id: int, metric: str, value: str) -> str:
    """Записывает метрику о самочувствии пользователя."""
    print(f"--- ИНСТРУМЕНТ (ЗАГЛУШКА): log_health_metric для user_id={user_id} ---")
    print(f"    Метрика: {metric}, Значение: {value}")
    return f"Запись о самочувствии '{metric}: {value}' сохранена."

# ... Другие инструменты, такие как get_travel_time и schedule_task, могут быть добавлены позже
tools = [create_event, create_task, log_health_metric]

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
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]
    final_state = await app_graph.ainvoke({
        "messages": messages,
        "user_id": user_id,
    })
    return final_state["messages"][-1].content