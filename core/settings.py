import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve values from .env and provide defaults if necessary
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
URL_DB_POSTGRES = os.getenv("URL_DB_POSTGRES")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DB_NAME = os.getenv("DB_NAME")
USER_DB = os.getenv("USER_DB")
PASSWORD_DB = os.getenv("PASSWORD_DB")
SCHEMA_TABLE = os.getenv("SCHEMA_TABLE")
SESSION_TABLE_NAME = os.getenv("SESSION_TABLE_NAME")
KNOWLEDGE_TABLE_NAME = os.getenv("KNOWLEDGE_TABLE_NAME")
URL_SERVER_FASTAPI = os.getenv("URL_SERVER_FASTAPI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VALID_API_KEYS  = os.getenv("VALID_API_KEYS")
SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY_ADMIN = os.getenv("SECRET_KEY_ADMIN")
ALGORITHM = os.getenv("ALGORITHM")
SECRET_KEY_REFRESH_USER = os.getenv("SECRET_KEY_REFRESH_USER")
SECRET_KEY_REFRESH_ADMIN = os.getenv("SECRET_KEY_REFRESH_ADMIN")
FIREBASE_CONFIG = os.getenv("FIREBASE_CONFIG")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT") 