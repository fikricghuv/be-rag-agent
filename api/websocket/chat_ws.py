
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.config_db import get_db
from services.chat_service import ChatService
from typing import Optional, Dict
import time
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from core.settings import VALID_API_KEYS
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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

    if not hasattr(websocket.app.state, "active_websockets"):
        websocket.app.state.active_websockets = {}
    active_websockets: Dict[UUID, WebSocket] = websocket.app.state.active_websockets

    if not hasattr(websocket.app.state, "admin_room_associations"):
         websocket.app.state.admin_room_associations = {}
    admin_room_associations: Dict[UUID, UUID] = websocket.app.state.admin_room_associations


    logger.info(f"Token diterima: user_id={user_id}, role={role}, api-key={api_key}")
    if not user_id or role not in {"user", "admin", "chatbot"}:
        await websocket.accept()
        await websocket.send_json({"error": "user_id dan/atau role tidak valid"})
        await websocket.close(code=1008)
        logger.warning("Koneksi ditutup: user_id dan/atau role tidak valid.")
        return
   
    if not api_key or api_key != VALID_API_KEYS:
        await websocket.accept()
        await websocket.send_json({"error": "api_key tidak ada atau tidak valid"})
        await websocket.close(code=1008)
        logger.warning("Koneksi ditutup: api_key tidak ada atau tidak valid")
        return

    try:
        user_uuid = UUID(user_id)

        await websocket.accept()
        logger.info(f"WebSocket terhubung: user_id={user_uuid}, role={role}")

        active_websockets[user_uuid] = websocket
        
        chat_service = ChatService(db=db, active_websockets=active_websockets, admin_room_associations=admin_room_associations)

        if role in {"user", "chatbot"}:
             room_uuid = await chat_service.find_or_create_room_and_add_member(user_uuid, role)
             logger.info(f"{role.capitalize()} {user_uuid} assigned to room {room_uuid}.")

             await chat_service.broadcast_active_rooms()

        while True:
            data = await websocket.receive_json()
            
            sender_id_str = data.get("user_id")
            sender_role = data.get("role")
            message_type = data.get("type", "message")

            if not sender_id_str or not sender_role:
                 logger.warning(f"Pesan diterima tanpa sender_id atau role: {data}")
                 continue

            try:
                sender_uuid = UUID(sender_id_str)
            except ValueError:
                 logger.warning(f"Invalid sender_id format: {sender_id_str}")
                 continue
            
            if message_type == "message":
                
                if role == "user":
                     
                     if room_uuid:
                         await chat_service.handle_user_message(websocket, data, user_uuid, room_uuid, start_time)
                     
                     else:
                         logger.warning(f"User {user_uuid} mengirim pesan tanpa room_id terasosiasi.")
                         await websocket.send_json({"success": False, "error": "Anda tidak terasosiasi dengan room chat."})
                elif role == "admin":
                     
                     target_room_id_str = data.get("room_id")
                     if not target_room_id_str:
                          await websocket.send_json({"success": False, "error": "Admin message requires room_id"})
                          continue
                     try:
                          target_room_uuid = UUID(target_room_id_str)
                     except ValueError:
                          await websocket.send_json({"success": False, "error": "Invalid room_id format in admin message"})
                          continue
                     
                     await chat_service.handle_admin_message(websocket, data, user_uuid, target_room_uuid)

                elif role == "chatbot":
                     
                     if room_uuid:
                          await chat_service.handle_chatbot_message(websocket, data, user_uuid, room_uuid)
                     else:
                          logger.warning(f"Chatbot {user_uuid} mengirim pesan tanpa room_id terasosiasi.")
                          await websocket.send_json({"success": False, "error": "Chatbot tidak terasosiasi dengan room chat."})
                          
            elif message_type == "file":
                 if role == "user":
                     
                     if room_uuid:
                         await chat_service.handle_user_file(websocket, data, user_uuid, room_uuid, start_time)
                     else:
                         logger.warning(f"User {user_uuid} mengirim file tanpa room_id terasosiasi.")
                         await websocket.send_json({"success": False, "error": "Anda tidak terasosiasi dengan room chat."})

            else:
                 logger.warning(f"Tipe pesan tidak dikenali atau tidak diizinkan untuk role {role}: {message_type}, data: {data}")

    except WebSocketDisconnect as e:
        logger.info(f"Koneksi terputus: {user_uuid} ({role}). Code: {e.code}, Reason: {e.reason}")
        if user_uuid:
            if user_uuid in active_websockets:
                del active_websockets[user_uuid]
                logger.info(f"WebSocket {user_uuid} dihapus dari active_websockets.")

            if role == "admin":
                 await chat_service.remove_admin_room_association(user_uuid) 
                 
            if room_uuid: 
                 try:
                      await chat_service.handle_disconnect(user_uuid, role, room_uuid)
                      await chat_service.broadcast_active_rooms()
                 except Exception as e_disconnect:
                      logger.exception(f"Error saat handle_disconnect atau broadcast active rooms for user/chatbot {user_uuid}:")
            elif role in {"user", "chatbot"} and not room_uuid:
                 logger.warning(f"User/Chatbot {user_uuid} disconnected without an associated room_id. Cannot update DB status.")


    except ValueError as ve:
        logger.exception(f"ValueError di chat_ws for user {user_uuid}:")
        if user_uuid in active_websockets:
            del active_websockets[user_uuid]
        try:
            await websocket.send_json({"error": f"Format ID atau data tidak valid: {ve}"})
        except Exception as send_err:
            logger.warning(f"Gagal kirim error sebelum close karena ValueError: {send_err}")
        await websocket.close(code=1008)

    except SQLAlchemyError as se:
        logger.exception(f"SQLAlchemyError di chat_ws for user {user_uuid}:")
        if user_uuid in active_websockets:
            del active_websockets[user_uuid]
        try:
            await websocket.send_json({"error": f"Error database: {se}"})
        except Exception as send_err:
            logger.warning(f"Gagal kirim error sebelum close karena SQLAlchemyError: {send_err}")
        await websocket.close(code=1011)

    except Exception as e:
        logger.exception(f"Kesalahan umum di chat_ws for user {user_uuid}:")
        if user_uuid in active_websockets:
            del active_websockets[user_uuid]
        try:
            await websocket.send_json({"error": f"Terjadi kesalahan internal: {e}"})
        except Exception as send_err:
            logger.warning(f"Gagal kirim error sebelum close karena Exception umum: {send_err}")
        await websocket.close(code=1011)

    finally:
        pass