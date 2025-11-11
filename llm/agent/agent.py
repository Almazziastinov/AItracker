import asyncio
import json
from datetime import datetime, timedelta
from langchain.tools import tool
from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from llm.agent.state import AgentState
from llm import llm_config
from db.schema import get_db, Event
from db.postgres import save_structured_data, get_events_for_user, save_event, get_user_home_address, set_user_home_address
from planning.planner import schedule_task
from maps import get_travel_time

# --- LLM ---
llm = GigaChat(
    credentials=llm_config.GIGACHAT_CREDENTIALS,
    model=llm_config.MODEL_NAME,
    verify_ssl_certs=False 
)
json_llm = GigaChat(
    credentials=llm_config.GIGACHAT_CREDENTIALS,
    model=llm_config.MODEL_NAME,
    verify_ssl_certs=False,
    response_format="json_object" 
)

# --- Tools ---
@tool
async def structure_user_input_tool(raw_text: str) -> dict:
    """
    Parses the user's raw text input to extract structured data like tasks, events, and health metrics.
    """
    json_extraction_prompt = """
    You are a data extraction specialist. Your task is to extract information about tasks, events, and health metrics from the user's text and format it as a JSON object.

    The JSON object should have the following structure:
    {
      "events": [
        {
          "type": "event",
          "title": "...",
          "start_time": "YYYY-MM-DDTHH:MM:SS" | null,
          "end_time": "YYYY-MM-DDTHH:MM:SS" | null,
          "location": "..." | null
        }
      ],
      "tasks": [
        {
          "type": "task",
          "title": "...",
          "duration": "..." | null,
          "deadline": "YYYY-MM-DDTHH:MM:SS" | null
        }
      ],
      "health_metrics": [
        {
          "type": "health",
          "metric": "...",
          "value": "..."
        }
      ]
    }

    - Today's date is 2025-11-11.
    - Extract all relevant entities. If a piece of information is not present, set its value to null.
    - For "location", extract the address or place name.

    Example 1:
    User text: "Завтра в 10 созвон, потом надо сделать лабу (часа на 3), и еще я плохо спал"
    JSON output:
    {
      "events": [
        {
          "type": "event",
          "title": "Созвон",
          "start_time": "2025-11-12T10:00:00",
          "end_time": null,
          "location": null
        }
      ],
      "tasks": [
        {
          "type": "task",
          "title": "Сделать лабу",
          "duration": "3 часа",
          "deadline": null
        }
      ],
      "health_metrics": [
        {
          "type": "health",
          "metric": "sleep_quality",
          "value": "poor"
        }
      ]
    }

    Example 2:
    User text: "Встреча в 15:00 на Мира, 15"
    JSON output:
    {
      "events": [
        {
          "type": "event",
          "title": "Встреча",
          "start_time": "2025-11-11T15:00:00",
          "end_time": null,
          "location": "Мира, 15"
        }
      ],
      "tasks": [],
      "health_metrics": []
    }
    """
    
    try:
        response = await json_llm.ainvoke([
            SystemMessage(content=json_extraction_prompt),
            HumanMessage(content=raw_text)
        ])
        json_data = json.loads(response.content)
        return json_data
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing JSON from LLM: {e}")
        return {"error": "Failed to structure input."}
    except Exception as e:
        print(f"An unexpected error occurred during structuring: {e}")
        return {"error": "An unexpected error occurred."}


tools = [structure_user_input_tool]
llm_with_tools = llm.bind_tools(tools)

# --- Graph ---
async def call_model(state: AgentState):
    """Calls the LLM with the user input and the available tools."""
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

async def call_tools(state: AgentState):
    """Calls the tools that the LLM has decided to use."""
    tool_call = state["messages"][-1].tool_calls[0]
    raw_text = tool_call["args"]["raw_text"]
    
    structured_data = await structure_user_input_tool.ainvoke({"raw_text": raw_text})
    
    if "error" in structured_data:
        return {"messages": [HumanMessage(content="Простите, я не смог обработать ваш запрос. Попробуйте переформулировать.")]}

    db_session = next(get_db())
    new_tasks = save_structured_data(db_session, state["user_id"], structured_data)
    
    scheduled_tasks_info = []
    if new_tasks:
        existing_events = get_events_for_user(db_session, state["user_id"])
        for task in new_tasks:
            scheduled_event = schedule_task(task, existing_events)
            if scheduled_event:
                save_event(db_session, scheduled_event)
                existing_events.append(scheduled_event)
                start_time_str = scheduled_event.start_time.strftime("%H:%M")
                scheduled_tasks_info.append(f"{task.title} (в {start_time_str})")

    # --- Logistics Integration ---
    travel_events_info = []
    for event_data in structured_data.get("events", []):
        if event_data.get("location") and event_data.get("start_time"):
            event_start_time = datetime.fromisoformat(event_data["start_time"])
            
            user_home_address = get_user_home_address(db_session, state["user_id"])
            
            if not user_home_address:
                # For now, we'll just inform the user. In a real bot, this would trigger a follow-up.
                print(f"User {state['user_id']} needs to set their home address for travel time calculation.")
                travel_events_info.append(f"Для события '{event_data['title']}' не удалось рассчитать время в пути, так как не указан ваш домашний адрес.")
                continue

            travel_time_minutes = await get_travel_time(user_home_address, event_data["location"])

            if travel_time_minutes:
                # Create "Дорога туда" event
                travel_to_start = event_start_time - timedelta(minutes=travel_time_minutes)
                travel_to_event = Event(
                    user_id=state["user_id"],
                    title=f"Дорога туда ({travel_time_minutes} мин)",
                    start_time=travel_to_start,
                    end_time=event_start_time,
                    location=f"Из {user_home_address} в {event_data['location']}"
                )
                save_event(db_session, travel_to_event)
                travel_events_info.append(f"Добавлена дорога туда ({travel_time_minutes} мин) для '{event_data['title']}'")

                # Create "Дорога обратно" event (assuming same travel time)
                # This is a simplification, ideally it would be after the event's end_time
                # For now, we'll just add it after the event's start time + 1 hour (placeholder)
                event_end_time = event_data.get("end_time")
                if event_end_time:
                    event_end_time = datetime.fromisoformat(event_end_time)
                else:
                    event_end_time = event_start_time + timedelta(hours=1) # Default event duration

                travel_from_start = event_end_time
                travel_from_event = Event(
                    user_id=state["user_id"],
                    title=f"Дорога обратно ({travel_time_minutes} мин)",
                    start_time=travel_from_start,
                    end_time=travel_from_start + timedelta(minutes=travel_time_minutes),
                    location=f"Из {event_data['location']} в {user_home_address}"
                )
                save_event(db_session, travel_from_event)
                travel_events_info.append(f"Добавлена дорога обратно ({travel_time_minutes} мин) для '{event_data['title']}'")
            else:
                travel_events_info.append(f"Не удалось рассчитать время в пути для '{event_data['title']}'.")

    db_session.close()

    parts = []
    if structured_data.get("events"):
        parts.append(f"события: {', '.join([e['title'] for e in structured_data['events']])}")
    if scheduled_tasks_info:
        parts.append(f"запланированные задачи: {', '.join(scheduled_tasks_info)}")
    elif structured_data.get("tasks"):
        parts.append(f"задачи (не удалось запланировать): {', '.join([t['title'] for t in structured_data['tasks']])}")
    if structured_data.get("health_metrics"):
        parts.append(f"самочувствие: {', '.join([h['metric'] for h in structured_data['health_metrics']])}")
    if travel_events_info:
        parts.append(f"логистика: {'; '.join(travel_events_info)}")
    
    if not parts:
        confirmation_message = "Я вас не совсем понял. Попробуйте еще раз."
    else:
        confirmation_message = f"Добавил {'; '.join(parts)}. Все верно?"

    return {"messages": [HumanMessage(content=confirmation_message)]}


def should_continue(state: AgentState):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", END)

app = workflow.compile()

# --- Agent Runner ---
async def run_agent_async(user_input: str, user_id: int):
    system_prompt = """
    You are a helpful personal assistant called Notemind.
    Your task is to understand the user's input. If the input is a request to add a task, event, or health metric, use the 'structure_user_input_tool' to process it.
    For simple greetings or questions, answer directly.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    result = await app.ainvoke({"messages": messages, "user_id": user_id})
    return result["messages"][-1].content

def run_agent(user_input: str, user_id: int):
    return asyncio.run(run_agent_async(user_input, user_id))