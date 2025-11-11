import asyncio
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from maxapi import Bot, Dispatcher
from max_bot.handlers import router
from max_bot import config
from db.schema import init_db

logging.basicConfig(level=logging.INFO)

bot = Bot(config.MAX_BOT_TOKEN)
dp = Dispatcher()

# Include the handlers from max_bot/handlers.py
dp.include_router(router)

async def main():
    # Initialize the database
    init_db()
    
    # Start the webhook listener
    await dp.handle_webhook(
        bot=bot,
        host='0.0.0.0',
        port=8000, # Running on port 8000 as in the previous FastAPI setup
    )

if __name__ == '__main__':
    asyncio.run(main())