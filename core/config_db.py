from core.settings import URL_DB_POSTGRES
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker


# Konfigurasi Database
# DATABASE_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"

async_engine = create_async_engine(URL_DB_POSTGRES, echo=True) # echo=True untuk melihat query SQL

# Ganti sessionmaker menjadi async_sessionmaker
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession
)

Base = declarative_base() # Jika Anda menggunakan declarative_base di sini

async def get_db():
    """Async Dependency for database session"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# Anda mungkin perlu fungsi init_db async jika menggunakan Alembic atau ORM sync sebelumnya
async def init_db():
    async with async_engine.begin() as conn:
        # Contoh jika menggunakan Base.metadata.create_all
        # await conn.run_sync(Base.metadata.create_all)
        pass # Sesuaikan dengan kebutuhan inisialisasi DB Anda
    
def config_db():

    engine = create_engine(URL_DB_POSTGRES)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()