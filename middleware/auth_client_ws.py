from fastapi import WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from jose import jwt
from core.settings import SECRET_KEY_ADMIN, ALGORITHM
from utils.exception_handler import ServiceException
from database.models.client_model import Client

async def get_authenticated_client_ws(
    db: AsyncSession,
    websocket: WebSocket,
    api_key: str = None,
    role: str = None,
    access_token: str = None,
) -> Client | None:
    """
    Autentikasi client berdasarkan subdomain dan API Key untuk WebSocket (async version).
    Role 'user' pakai subdomain + api_key.
    Role 'admin' pakai access_token JWT.
    """

    host = websocket.headers.get("host")
    if not host:
        return None

    if role == "user":
        if not api_key:
            return None

        try:
            host_without_port = host.split(":")[0]
            subdomain = host_without_port.split(".")[0].lower()

            stmt = select(Client).filter(
                Client.subdomain == subdomain,
                Client.api_key == api_key
            )
            result = await db.execute(stmt)
            client = result.scalars().first()
            return client
        except Exception as e:
            print(f"DB Error (user): {e}")
            return None

    elif role == "admin":
        if not access_token:
            return None
        try:
            payload = jwt.decode(access_token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id:
                raise ServiceException(
                    code="INVALID_OR_MISSING_TOKEN",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id",
                )

            # Ambil client_id dari ms_admin_users (async)
            query = text("""
                SELECT client_id
                FROM ai.ms_admin_users
                WHERE id = :user_id
            """)
            result = await db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            if not row or not row.client_id:
                return None

            # Ambil Client instance berdasarkan client_id
            stmt_client = select(Client).filter(Client.id == row.client_id)
            client_result = await db.execute(stmt_client)
            client = client_result.scalars().first()
            return client

        except Exception as e:
            print(f"DB or JWT Error (admin): {e}")
            return None

    return None
