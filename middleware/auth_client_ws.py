from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models.client_model import Client

async def get_authenticated_client_ws(db: AsyncSession, websocket: WebSocket, api_key: str):
    """
    Autentikasi client berdasarkan subdomain dan API Key untuk WebSocket (async version).
    """
    host = websocket.headers.get("host")
    if not host or not api_key:
        return None

    host_without_port = host.split(":")[0]
    subdomain = host_without_port.split(".")[0].lower()

    try:
        stmt = select(Client).filter(
            Client.subdomain == subdomain,
            Client.api_key == api_key
        )
        result = await db.execute(stmt)
        client = result.scalars().first()
        return client
    except Exception as e:
        print(f"DB Error: {e}")
        return None
