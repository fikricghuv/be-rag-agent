# router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.config_db import get_db
from services.chat_service import ChatService
from database.models import RoomConversation, Member, Chat
from typing import Optional, Dict
import time
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from sqlalchemy.future import select
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
    room_uuid: Optional[UUID] = None # room_id terasosiasi dengan koneksi user/chatbot ini saat dibuat

    if not hasattr(websocket.app.state, "active_websockets"):
        websocket.app.state.active_websockets = {}
    active_websockets: Dict[UUID, WebSocket] = websocket.app.state.active_websockets

    if not hasattr(websocket.app.state, "admin_room_associations"):
         websocket.app.state.admin_room_associations = {}
    admin_room_associations: Dict[UUID, UUID] = websocket.app.state.admin_room_associations


    print(f"🔑 Token diterima: user_id={user_id}, role={role}, api-key={api_key}")
    if not user_id or role not in {"user", "admin", "chatbot"}:
        await websocket.accept()
        await websocket.send_json({"error": "user_id dan/atau role tidak valid"})
        await websocket.close(code=1008)
        print("❌ Koneksi ditutup: user_id dan/atau role tidak valid.")
        return
   
    if not api_key or api_key != VALID_API_KEYS:
        await websocket.accept()
        await websocket.send_json({"error": "api_key tidak ada atau tidak valid"})
        await websocket.close(code=1008)
        print("❌ Koneksi ditutup: api_key tidak ada atau tidak valid")
        return

    try:
        user_uuid = UUID(user_id)

        await websocket.accept()
        print(f"✅ WebSocket terhubung: user_id={user_uuid}, role={role}")

        active_websockets[user_uuid] = websocket
        # Inisialisasi ChatService setelah websocket aktif
        chat_service = ChatService(db=db, active_websockets=active_websockets, admin_room_associations=admin_room_associations)


        # --- Logika untuk User/Chatbot pada Koneksi Awal ---
        if role in {"user", "chatbot"}:
             room_uuid = await chat_service.find_or_create_room_and_add_member(user_uuid, role)
             print(f"{role.capitalize()} {user_uuid} assigned to room {room_uuid}.")

             # Broadcast daftar room aktif ke semua admin yang online setelah user/chatbot join/create room
             await chat_service.broadcast_active_rooms()

        # Admin tidak diasosiasikan dengan room saat koneksi awal secara default

        # Main loop untuk menerima pesan
        while True:
            data = await websocket.receive_json()
            # print("📩 Data diterima:", data) # Logging sudah ada di service

            sender_id_str = data.get("user_id")
            sender_role = data.get("role")
            message_type = data.get("type", "message")

            if not sender_id_str or not sender_role:
                 print(f"⚠️ Pesan diterima tanpa sender_id atau role: {data}")
                 continue

            try:
                sender_uuid = UUID(sender_id_str)
            except ValueError:
                 print(f"⚠️ Invalid sender_id format: {sender_id_str}")
                 continue
            
            # --- Dispatch Pesan Berdasarkan Tipe dan Role ---

            if message_type == "message":
                # Handler pesan chat biasa dari user, admin, atau chatbot
                if role == "user":
                     print("/nmasuk useeerrrrr")
                     # Room ID untuk user sudah diketahui dari koneksi awal
                     if room_uuid:
                         await chat_service.handle_user_message(websocket, data, user_uuid, room_uuid, start_time)
                     else:
                         print(f"⚠️ User {user_uuid} mengirim pesan tanpa room_id terasosiasi.")
                         await websocket.send_json({"success": False, "error": "Anda tidak terasosiasi dengan room chat."})
                elif role == "admin":
                     # Pesan chat admin biasa memerlukan target_room_id dan target_user_id
                     target_room_id_str = data.get("room_id")
                     if not target_room_id_str:
                          await websocket.send_json({"success": False, "error": "Admin message requires room_id"})
                          continue
                     try:
                          target_room_uuid = UUID(target_room_id_str)
                     except ValueError:
                          await websocket.send_json({"success": False, "error": "Invalid room_id format in admin message"})
                          continue
                     # Panggil handler admin message
                     await chat_service.handle_admin_message(websocket, data, user_uuid, target_room_uuid)

                elif role == "chatbot":
                     # Room ID untuk chatbot sudah diketahui dari koneksi awal
                     if room_uuid:
                          await chat_service.handle_chatbot_message(websocket, data, user_uuid, room_uuid)
                     else:
                          print(f"⚠️ Chatbot {user_uuid} mengirim pesan tanpa room_id terasosiasi.")
                          await websocket.send_json({"success": False, "error": "Chatbot tidak terasosiasi dengan room chat."})

            # --- Tipe Pesan Khusus Admin ---
            elif role == "admin" and message_type == "admin_join_room":
                 target_room_id_str = data.get("room_id")
                 if not target_room_id_str:
                      await websocket.send_json({"success": False, "error": "Joining a room requires room_id"})
                      continue
                 try:
                      target_room_uuid = UUID(target_room_id_str)
                 except ValueError:
                      await websocket.send_json({"success": False, "error": "Invalid room_id format"})
                      return

                 # Validasi apakah room_id valid
                 room_exists_result = await db.execute(select(RoomConversation.id).where(RoomConversation.id == target_room_uuid).limit(1))
                 room_exists = room_exists_result.scalar_one_or_none()

                 if not room_exists:
                      await websocket.send_json({"success": False, "error": f"Room with ID {target_room_id_str} not found."})
                      return

                 # Set asosiasi admin dengan room di state
                 await chat_service.set_admin_room_association(user_uuid, target_room_uuid)
                 logger.info(f"Admin {user_uuid} diasosiasikan dengan room {target_room_uuid} di state.")

                 # Kirim konfirmasi ke admin
                 await websocket.send_json({"success": True, "type": "admin_room_joined", "room_id": target_room_id_str, "message": f"Berhasil bergabung ke room {target_room_id_str}"})

                 # Kirim riwayat chat ke admin
                 chat_history = await chat_service.get_room_history(target_room_uuid)
                 await websocket.send_json({"type": "chat_history", "room_id": target_room_id_str, "history": chat_history})

            elif role == "admin" and message_type == "admin_leave_room":
                 # Admin meninggalkan room yang sedang mereka lihat
                 # Ambil room_id dari asosiasi state saat ini
                 current_associated_room_id = admin_room_associations.get(user_uuid)
                 if current_associated_room_id:
                      await chat_service.remove_admin_room_association(user_uuid)
                      await websocket.send_json({"success": True, "type": "admin_room_left", "room_id": str(current_associated_room_id), "message": f"Berhasil keluar dari room {current_associated_room_id}"})
                 else:
                      await websocket.send_json({"success": False, "error": "Anda tidak sedang melihat room manapun."})

            # --- Tipe Pesan Admin untuk Kontrol Agen ---
            elif role == "admin" and message_type == "admin_take_over":
                 target_room_id_str = data.get("room_id")
                 if not target_room_id_str:
                      await websocket.send_json({"success": False, "error": "Take over requires room_id"})
                      return
                 try:
                      target_room_uuid = UUID(target_room_id_str)
                 except ValueError:
                      await websocket.send_json({"success": False, "error": "Invalid room_id format for take over"})
                      return

                 # Cek apakah room_id valid
                 room_exists_result = await db.execute(select(RoomConversation.id).where(RoomConversation.id == target_room_uuid).limit(1))
                 room_exists = room_exists_result.scalar_one_or_none()
                 if not room_exists:
                      await websocket.send_json({"success": False, "error": f"Room with ID {target_room_id_str} not found."})
                      return

                 # Ambil status agen saat ini untuk konfirmasi
                 room_status_result = await db.execute(select(RoomConversation.agent_active).where(RoomConversation.id == target_room_uuid).limit(1))
                 is_agent_active_before = room_status_result.scalar_one_or_none()


                 if is_agent_active_before is False:
                      await websocket.send_json({"success": True, "type": "admin_take_over_status", "room_id": target_room_id_str, "message": "Room sudah dalam mode admin.", "status": "already_taken_over"})
                      logger.info(f"Admin {user_uuid} attempted to take over room {target_room_uuid}, but it was already taken over.")
                 else:
                      # Set status agen menjadi nonaktif
                      await chat_service.set_room_agent_status(target_room_uuid, False)
                      await websocket.send_json({"success": True, "type": "admin_take_over_status", "room_id": target_room_id_str, "message": "Berhasil mengambil alih percakapan.", "status": "taken_over"})
                      logger.info(f"Admin {user_uuid} took over room {target_room_uuid}.")

                      # Opsional: Kirim notifikasi ke user di room tersebut
                      user_in_room_result = await db.execute(select(Member).where(Member.room_conversation_id == target_room_uuid, Member.role == "user", Member.is_online == True).limit(1))
                      user_member = user_in_room_result.scalars().one_or_none()
                      if user_member:
                           user_websocket = await chat_service.get_active_websocket(user_member.user_id)
                           if user_websocket:
                                await user_websocket.send_json({"type": "info", "room_id": str(target_room_uuid), "message": "Seorang admin telah bergabung untuk membantu Anda."})
                                logger.info(f"Sent takeover notification to user {user_member.user_id} in room {target_room_uuid}.")

                      # Broadcast update room aktif ke admin lain
                      await chat_service.broadcast_active_rooms()


            elif role == "admin" and message_type == "admin_hand_back":
                 target_room_id_str = data.get("room_id")
                 if not target_room_id_str:
                      await websocket.send_json({"success": False, "error": "Hand back requires room_id"})
                      return
                 try:
                      target_room_uuid = UUID(target_room_id_str)
                 except ValueError:
                      await websocket.send_json({"success": False, "error": "Invalid room_id format for hand back"})
                      return

                 # Cek apakah room_id valid
                 room_exists_result = await db.execute(select(RoomConversation.id).where(RoomConversation.id == target_room_uuid).limit(1))
                 room_exists = room_exists_result.scalar_one_or_none()
                 if not room_exists:
                      await websocket.send_json({"success": False, "error": f"Room with ID {target_room_id_str} not found."})
                      return

                 # Ambil status agen saat ini untuk konfirmasi
                 room_status_result = await db.execute(select(RoomConversation.agent_active).where(RoomConversation.id == target_room_uuid).limit(1))
                 is_agent_active_before = room_status_result.scalar_one_or_none()

                 if is_agent_active_before is True:
                      await websocket.send_json({"success": True, "type": "admin_hand_back_status", "room_id": target_room_id_str, "message": "Room sudah dalam mode agen.", "status": "already_handed_back"})
                      logger.info(f"Admin {user_uuid} attempted to hand back room {target_room_uuid}, but it was already handed back.")

                 else:
                     # Set status agen menjadi aktif
                     await chat_service.set_room_agent_status(target_room_uuid, True)
                     await websocket.send_json({"success": True, "type": "admin_hand_back_status", "room_id": target_room_id_str, "message": "Berhasil menyerahkan kembali percakapan ke agen.", "status": "handed_back"})
                     logger.info(f"Admin {user_uuid} handed back room {target_room_uuid}.")

                     # Opsional: Kirim notifikasi ke user di room tersebut
                     user_in_room_result = await db.execute(select(Member).where(Member.room_conversation_id == target_room_uuid, Member.role == "user", Member.is_online == True).limit(1))
                     user_member = user_in_room_result.scalars().one_or_none()
                     if user_member:
                          user_websocket = await chat_service.get_active_websocket(user_member.user_id)
                          if user_websocket:
                               await user_websocket.send_json({"type": "info", "room_id": str(target_room_uuid), "message": "Anda sekarang berbicara dengan agen otomatis kembali."})
                               logger.info(f"Sent hand back notification to user {user_member.user_id} in room {target_room_uuid}.")

                     # Broadcast update room aktif ke admin lain
                     await chat_service.broadcast_active_rooms()


            else:
                 print(f"⚠️ Tipe pesan tidak dikenali atau tidak diizinkan untuk role {role}: {message_type} data: {data}")
                 # await websocket.send_json({"error": f"Tipe pesan '{message_type}' tidak dikenali atau tidak diizinkan."})


    except WebSocketDisconnect as e:
        print(f"🔌 Koneksi terputus: {user_uuid} ({role}). Code: {e.code}, Reason: {e.reason}")
        if user_uuid:
            if user_uuid in active_websockets:
                del active_websockets[user_uuid]
                print(f"🗑️ WebSocket {user_uuid} dihapus dari active_websockets.")

            if role == "admin":
                 await chat_service.remove_admin_room_association(user_uuid) # Hapus asosiasi room jika admin disconnect
                 
            # Untuk user/chatbot, panggil handle_disconnect untuk update is_online
            if room_uuid: # Hanya panggil handle_disconnect jika room_uuid terasosiasi dengan koneksi ini
                 try:
                      await chat_service.handle_disconnect(user_uuid, role, room_uuid)
                      # Broadcast update room aktif ke admin setelah disconnect user/chatbot
                      # Ini penting agar admin UI melihat jumlah member online berkurang
                      await chat_service.broadcast_active_rooms()
                 except Exception as e_disconnect:
                      logging.exception(f"Error saat handle_disconnect atau broadcast active rooms for user/chatbot {user_uuid}:")
            elif role in {"user", "chatbot"} and not room_uuid:
                 print(f"⚠️ User/Chatbot {user_uuid} disconnected without an associated room_id. Cannot update DB status.")


    except ValueError as ve:
        logging.exception(f"ValueError di chat_ws for user {user_uuid}:")
        if user_uuid and user_uuid in active_websockets:
             del active_websockets[user_uuid]
             print(f"🗑️ WebSocket {user_uuid} dihapus dari active_websockets karena ValueError.")
        try:
            await websocket.send_json({"error": f"Format ID atau data tidak valid: {ve}"})
        except Exception as send_err:
            print(f"⚠️ Gagal kirim error sebelum close karena ValueError: {send_err}")
        await websocket.close(code=1008)

    except SQLAlchemyError as se:
        logging.exception(f"SQLAlchemyError di chat_ws for user {user_uuid}:")
        if user_uuid and user_uuid in active_websockets:
             del active_websockets[user_uuid]
             print(f"🗑️ WebSocket {user_uuid} dihapus dari active_websockets karena SQLAlchemyError.")
        try:
            await websocket.send_json({"error": f"Error database: {se}"})
        except Exception as send_err:
            print(f"⚠️ Gagal kirim error sebelum close karena SQLAlchemyError: {se}")
        await websocket.close(code=1011)

    except Exception as e:
        logging.exception(f"Kesalahan umum di chat_ws for user {user_uuid}:")
        if user_uuid and user_uuid in active_websockets:
             del active_websockets[user_uuid]
             print(f"🗑️ WebSocket {user_uuid} dihapus dari active_websockets karena Exception umum.")
        try:
            await websocket.send_json({"error": f"Terjadi kesalahan internal: {e}"})
        except Exception as send_err:
             print(f"⚠️ Gagal kirim error sebelum close karena Exception umum: {send_err}")
        await websocket.close(code=1011)

    finally:
        pass