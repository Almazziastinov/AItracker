import asyncio
from app.services.llm_processor import run_agent_async

async def main():
    """
    Тестовый запуск обновленного LLM агента.
    """
    print("--- Запуск тестового прогона обновленного LLM агента ---")
    
    # Сложный пример из ТЗ, включающий событие, задачу и метрику здоровья
    user_input = "Завтра в 10 созвон, потом надо сделать лабу (часа на 3), и еще я плохо спал"
    user_id = 12345

    print(f"\n[Тест] Вход: '{user_input}' для пользователя {user_id}")
    
    # Вызов агента
    response = await run_agent_async(user_input, user_id)
    
    print("\n--- Итоговый ответ агента ---")
    print(response)
    print("--------------------------")


if __name__ == "__main__":
    # Убедитесь, что у вас есть .env файл с GIGACHAT_CREDENTIALS
    # в корне проекта и установлены все зависимости.
    asyncio.run(main())