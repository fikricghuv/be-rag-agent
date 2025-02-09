from config.settings import URL_DB_POSTGRES
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Konfigurasi Database
# DATABASE_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"

def config_db():

    engine = create_engine(URL_DB_POSTGRES)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()