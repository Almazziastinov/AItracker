import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
# MAX Bot Token
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

# GigaChat API Credentials
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

# Sber Speech API Credentials (if different from GigaChat)
SBER_SPEECH_API_KEY = os.getenv("SBER_SPEECH_API_KEY")


# --- Database ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")