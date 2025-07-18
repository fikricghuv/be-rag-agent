
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.config_db import get_db
from api.websocket.redis_client import redis_client
from services.chat_service import ChatService
from typing import Optional, Dict
import time
from uuid import UUID
from core.settings import VALID_API_KEYS
import logging
from services.chat_singleton import init_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()

# active_websockets: Dict[UUID, WebSocket] = {}

@router.websocket("/ws/chat")
async def chat_ws(
    websocket: WebSocket,
    user_id: str = None,
    role: str = None,
    api_key: str = None,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    user_uuid: Optional[UUID] = None
    room_uuid: Optional[UUID] = None

    logger.info(f"Token diterima: user_id={user_id}, role={role}, api-key={api_key}")
    if not user_id or role not in {"user", "admin", "chatbot"}:
        await websocket.accept()
        await websocket.send_json({"error": "user_id dan/atau role tidak valid"})
        await websocket.close(code=1008)
        return

    if not api_key or api_key != VALID_API_KEYS:
        await websocket.accept()
        await websocket.send_json({"error": "api_key tidak ada atau tidak valid"})
        await websocket.close(code=1008)
        return

    try:
        user_uuid = UUID(user_id)

        await websocket.accept()
        logger.info(f"WebSocket terhubung: user_id={user_uuid}, role={role}")
        # active_websockets[user_uuid] = websocket

        chat_service = init_chat_service(db=db)
        
        await chat_service.mark_online(user_uuid, role)

        if role in {"user", "chatbot"}:
            room_uuid = await chat_service.find_or_create_room_and_add_member(db, user_uuid, role)
            await redis_client.set(f"{role}_room:{user_uuid}", str(room_uuid))
            await chat_service.broadcast_active_rooms(db)

        while True:
            data = await websocket.receive_json()
            sender_id_str = data.get("user_id")
            sender_role = data.get("role")
            message_type = data.get("type", "message")

            if not sender_id_str or not sender_role:
                logger.warning("Pesan tanpa user_id atau role: %s", data)
                continue

            try:
                sender_uuid = UUID(sender_id_str)
            except ValueError:
                logger.warning("Format user_id salah: %s", sender_id_str)
                continue

            if message_type == "message":
                if role == "user" and room_uuid:
                    await chat_service.handle_user_message(db, websocket, data, user_uuid, room_uuid, start_time)

                elif role == "admin":
                    target_room_id_str = data.get("room_id")
                    if not target_room_id_str:
                        await websocket.send_json({"success": False, "error": "room_id wajib untuk admin"})
                        continue
                    try:
                        target_room_uuid = UUID(target_room_id_str)
                        await redis_client.set(f"admin_room:{user_uuid}", str(target_room_uuid))
                        await chat_service.handle_admin_message(db, websocket, data, user_uuid, target_room_uuid)
                    except ValueError:
                        await websocket.send_json({"success": False, "error": "room_id tidak valid"})
                        continue

                elif role == "chatbot" and room_uuid:
                    await chat_service.handle_chatbot_message(db, websocket, data, user_uuid, room_uuid)

            elif message_type == "file" and role == "user" and room_uuid:
                await chat_service.handle_user_file(db, websocket, data, user_uuid, room_uuid, start_time)

            elif message_type == "voice_note" and role == "user" and room_uuid:
                await chat_service.handle_user_audio(db, websocket, data, user_uuid, room_uuid, start_time)

            else:
                logger.warning(f"Tipe pesan tidak dikenali atau tidak valid untuk {role}: {message_type}")

    except WebSocketDisconnect as e:
        logger.info(f"WebSocket putus: {user_uuid} ({role}). Code: {e.code}")
        
        await chat_service.mark_offline(user_uuid, role)

        # if user_uuid in active_websockets:
        #     del active_websockets[user_uuid]

        if role == "admin":
            await redis_client.delete(f"admin_room:{user_uuid}")

        if role in {"user", "chatbot"}:
            await redis_client.delete(f"{role}_room:{user_uuid}")

        if room_uuid:
            try:
                await chat_service.handle_disconnect(db, user_uuid, role, room_uuid)
                await chat_service.broadcast_active_rooms(db)
            except Exception as e_disconnect:
                logger.exception("Gagal saat disconnect user/chatbot %s", user_uuid)

    except Exception as e:
        logger.exception(f"Kesalahan fatal WebSocket: {e}")
        # if user_uuid in active_websockets:
        #     del active_websockets[user_uuid]
        try:
            await websocket.send_json({"error": f"Terjadi kesalahan internal: {e}"})
        except:
            pass
        await websocket.close(code=1011)
