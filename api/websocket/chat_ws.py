from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
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
from prometheus_client import Counter, Gauge
from middleware.auth_client_ws import get_authenticated_client_ws
import json

ws_connection_count = Counter("ws_connections_total", "Total WebSocket connections ever created")
ws_active_users = Gauge("ws_active_users", "Number of active WebSocket connections")

logger = logging.getLogger(__name__)
router = APIRouter()

active_websockets: Dict[UUID, Dict[UUID, WebSocket]] = {}

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
    client = None

    try:
        logger.info(f"Token diterima: user_id={user_id}, role={role}, api-key={api_key}")

        client = await get_authenticated_client_ws(db, websocket, api_key)
        
        if not client:
            await websocket.accept()
            await websocket.send_json({"error": "Unauthorized WebSocket connection"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        client_id = client.id
        
        if not user_id or role not in {"user", "admin", "chatbot"}:
            await websocket.accept()
            await websocket.send_json({"error": "user_id dan/atau role tidak valid"})
            await websocket.close(code=1008)
            return

        user_uuid = UUID(user_id)
        await websocket.accept()

        ws_connection_count.inc()
        ws_active_users.inc()

        logger.info(f"[WS] Authenticated connection for client_id={client_id}, user_id={user_uuid}, role={role}")

        active_websockets.setdefault(client_id, {})[user_uuid] = websocket

        chat_service = init_chat_service(db=db)

        await chat_service.mark_online(user_uuid, role, client_id)

        if role in {"user", "chatbot"}:
            room_uuid = await chat_service.find_or_create_room_and_add_member(db, user_uuid, role, client_id)
            
            online_admin_uuids = await chat_service.get_all_online("admin", client_id)
            logger.debug(f"Found {len(online_admin_uuids)} online admins from Redis for active rooms broadcast.")

        while True:
            data = await websocket.receive_json()
            sender_id_str = data.get("user_id")
            sender_role = data.get("role")
            message_type = data.get("type", "message")

            if not sender_id_str or not sender_role:
                logger.warning("Pesan tanpa user_id atau role: %s", data)
                continue

            if message_type == "message":
                if role == "user" and room_uuid:
                    await chat_service.set_user_room_mapping(
                        user_id=user_uuid,
                        client_id=client_id,
                        role=role,
                        room_id=room_uuid,
                        ttl=3600
                    )
                    await chat_service.handle_user_message(db, websocket, data, user_uuid, room_uuid, start_time, client_id)

                elif role == "admin":
                    await chat_service.set_user_room_mapping(
                        user_id=user_uuid,
                        client_id=client_id,
                        role=role,
                        room_id=room_uuid,
                        ttl=3600
                    )
                    target_room_id_str = data.get("room_id")
                    if not target_room_id_str:
                        await websocket.send_json({"success": False, "error": "room_id wajib untuk admin"})
                        continue
                    try:
                        target_room_uuid = UUID(target_room_id_str)
                        await redis_client.set(
                            f"admin_room:{user_uuid}:{client_id}",
                            json.dumps({"room": str(target_room_uuid), "client": str(client_id)})
                        )
                        await chat_service.handle_admin_message(db, websocket, data, user_uuid, target_room_uuid, client_id)
                    except ValueError:
                        await websocket.send_json({"success": False, "error": "room_id tidak valid"})
                        continue

                elif role == "chatbot" and room_uuid:
                    await chat_service.handle_chatbot_message(db, websocket, data, user_uuid, room_uuid, client_id)

            elif message_type == "file" and role == "user" and room_uuid:
                await chat_service.set_user_room_mapping(
                    user_id=user_uuid,
                    client_id=client_id,
                    role=role,
                    room_id=room_uuid,
                    ttl=3600
                )
                await chat_service.handle_user_file(db, websocket, data, user_uuid, room_uuid, start_time, client_id)

            elif message_type == "voice_note" and role == "user" and room_uuid:
                await chat_service.set_user_room_mapping(
                    user_id=user_uuid,
                    client_id=client_id,
                    role=role,
                    room_id=room_uuid,
                    ttl=3600
                )
                await chat_service.handle_user_audio(db, websocket, data, user_uuid, room_uuid, start_time, client_id)

            else:
                logger.warning(f"Tipe pesan tidak dikenali atau tidak valid untuk {role}: {message_type}")

    except WebSocketDisconnect as e:
        logger.info(f"WebSocket putus: {user_uuid} ({role}). Code: {e.code}")

        ws_active_users.dec()

        if client:
            
            if role == "admin":
                await redis_client.delete(f"admin_room:{user_uuid}:{client_id}")
            if role in {"user", "chatbot"}:
                await redis_client.delete(f"{role}_room:{user_uuid}:{client_id}")

            if client_id in active_websockets and user_uuid in active_websockets[client_id]:
                await chat_service.mark_offline(user_uuid, role, client_id)
                del active_websockets[client_id][user_uuid]
                if not active_websockets[client_id]:
                    del active_websockets[client_id]

        if room_uuid and client:
            try:
                await chat_service.handle_disconnect(db, user_uuid, role, room_uuid, client_id)
                # await chat_service.broadcast_active_rooms(db, client_id)
            except Exception as e_disconnect:
                logger.exception("Gagal saat disconnect user/chatbot %s", user_uuid)

    except Exception as e:
        logger.exception(f"Kesalahan fatal WebSocket: {e}")

        if client:
            await chat_service.mark_offline(user_uuid, role, client_id)
        ws_active_users.dec()

        try:
            await websocket.send_json({"error": f"Terjadi kesalahan internal: {e}"})
        except:
            pass
        await websocket.close(code=1011)
