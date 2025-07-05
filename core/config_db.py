from core.settings import URL_DB_POSTGRES
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base() 

async_engine = create_async_engine(URL_DB_POSTGRES, echo=True) 

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession
)

async def get_db():
    """Async Dependency for database session"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    
def config_db():

    engine = create_engine(URL_DB_POSTGRES)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()