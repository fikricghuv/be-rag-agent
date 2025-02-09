import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve values from .env and provide defaults if necessary
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
URL_DB_POSTGRES = os.getenv("URL_DB_POSTGRES")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DB_NAME = os.getenv("DB_NAME")
USER_DB = os.getenv("USER_DB")
PASSWORD_DB = os.getenv("PASSWORD_DB")
URL_SERVER_FASTAPI = os.getenv("URL_SERVER_FASTAPI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")