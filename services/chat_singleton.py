# services/chat_singleton.py
from services.chat_service import ChatService
from api.websocket.redis_client import redis_client
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from uuid import UUID
from starlette.websockets import WebSocket

active_websockets: Dict[UUID, WebSocket] = {}

chat_service_singleton: ChatService = None

def init_chat_service(db: AsyncSession):
    global chat_service_singleton
    if chat_service_singleton is None:
        chat_service_singleton = ChatService(
            db=db,
            redis=redis_client,
            active_websockets=active_websockets,
        )
    return chat_service_singleton
