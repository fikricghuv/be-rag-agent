# services/chat_service_test.py
from sqlalchemy.ext.asyncio import AsyncSession
from agents.customer_service_agent.customer_service_agent import call_customer_service_agent
from fastapi import WebSocket
import asyncio
import time
import re
from database.models import RoomConversation, Member, Chat
from typing import Dict, Optional, List, Any
from sqlalchemy.exc import SQLAlchemyError
import uuid
import logging
import json
from datetime import timedelta
from sqlalchemy.future import select
from sqlalchemy import update, insert, delete
import sqlalchemy
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from agno.media import File
import base64
import os

client = OpenAI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession, active_websockets: Dict[uuid.UUID, WebSocket], admin_room_associations: Dict[uuid.UUID, uuid.UUID]):
        self.db: AsyncSession = db
        self.active_websockets = active_websockets
        self.admin_room_associations = admin_room_associations
        
    def classify_zero_shot(self, response_text: str) -> str:
        prompt = f"""
        Kategorikan pesan ini ke salah satu kategori berikut:
        - Sapa
        - Informasi Umum
        - Produk Asuransi Oto
        - Produk Asuransi Asri
        - Produk Asuransi Sepeda
        - Produk Asuransi Apartemen
        - Produk Asuransi Ruko
        - Produk Asuransi Diri
        - Claim
        - Payment
        - Policy
        - Complaint
        - Others

        Pesan: "{response_text}"

        Jawab hanya dengan 1 nama kategorinya saja. Pilih yang paling sesuai dengan konteks pesan di atas.
        """
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip().lower()


    async def get_active_websocket(self, user_id: uuid.UUID) -> Optional[WebSocket]:
        logger.debug(f"🔍 Mencari websocket aktif untuk user_id: {user_id}")
        return self.active_websockets.get(user_id)

    async def get_user_room_id(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        # ... (kode metode ini tetap sama) ...
         try:
             result = await self.db.execute(
                 select(Member.room_conversation_id)
                 .where(Member.user_id == user_id)
                 .limit(1)
             )
             room_id = result.scalar_one_or_none()
             logger.debug(f"Room ID untuk user {user_id}: {room_id}")
             return room_id
         except SQLAlchemyError as e:
             logger.error(f"Error in get_user_room_id: {e}", exc_info=True)
             raise

    async def find_or_create_room_and_add_member(self, user_id: uuid.UUID, role: str) -> uuid.UUID:
        # ... (kode metode ini tetap sama) ...
        try:
            # 1. Cek apakah user sudah punya room terbuka (atau room aktif lainnya)
            result = await self.db.execute(
                select(RoomConversation.id)
                .join(Member, Member.room_conversation_id == RoomConversation.id)
                .where(Member.user_id == user_id, RoomConversation.status != "closed")
                .limit(1)
            )
            existing_room_id = result.scalar_one_or_none()

            if existing_room_id:
                room_uuid = existing_room_id
                logger.info(f"Found existing room {room_uuid} for user {user_id}.")

                # Pastikan member user ada dan update status online
                member_result = await self.db.execute(
                    select(Member).where(Member.room_conversation_id == room_uuid, Member.user_id == user_id)
                )
                member = member_result.scalar_one_or_none()
                if member:
                    if not member.is_online:
                         await self.db.execute(
                             update(Member)
                             .where(Member.id == member.id)
                             .values(is_online=True)
                         )
                         await self.db.commit()
                         logger.info(f"Updated user {user_id} online status in room {room_uuid}.")
                else:
                    # Jika member user tidak ada di room yang ditemukan (kasus aneh, mungkin data korup),
                    # buat member baru
                    new_member = Member(
                        id=uuid.uuid4(),
                        room_conversation_id=room_uuid,
                        user_id=user_id,
                        role=role,
                        is_online=True,
                    )
                    self.db.add(new_member)
                    await self.db.commit()
                    logger.warning(f"User {user_id} not found in existing room {room_uuid} database entry, added new member.")


            else:
                # 2. Jika tidak ada room terbuka, buat room baru
                room_uuid = uuid.uuid4()
                logger.info(f"Creating new room: {room_uuid} for user: {user_id}")

                new_room = RoomConversation(id=room_uuid, status="open", agent_active=True) # <-- agent_active=True secara eksplisit jika default di DB/model tidak jalan
                self.db.add(new_room)

                # Tambahkan user sebagai member
                user_member_id = uuid.uuid4()
                user_member = Member(
                    id=user_member_id,
                    room_conversation_id=room_uuid,
                    user_id=user_id,
                    role=role,
                    is_online=True,
                )
                self.db.add(user_member)
                logger.info(f"Added user member {user_member_id} to new room {room_uuid}.")

                # Tambahkan chatbot sebagai member default
                chatbot_member_user_id = uuid.uuid4()
                chatbot_member_id = uuid.uuid4()
                chatbot_member = Member(
                    id=chatbot_member_id,
                    room_conversation_id=room_uuid,
                    user_id=chatbot_member_user_id,
                    role="chatbot",
                    is_online=False,
                )
                self.db.add(chatbot_member)
                logger.info(f"Added chatbot member {chatbot_member_id} ({chatbot_member_user_id}) to new room {room_uuid}.")


                await self.db.commit()

            return room_uuid

        except SQLAlchemyError as e:
            logger.error(f"Error in find_or_create_room_and_add_member: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def save_chat_history(
       # ... (kode metode ini tetap sama) ...
       self,
       room_conversation_id: uuid.UUID,
       sender_id: uuid.UUID,
       message: str,
       agent_response_category: str = None,
       agent_response_latency: timedelta = None,
       agent_total_tokens: int = None,
       agent_input_tokens: int = None,
       agent_output_tokens: int = None,
       agent_other_metrics: dict = None,
       agent_tools_call: List[str] = None,
       role: str = None
    ):
        logger.info(f"Saving chat history for room: {room_conversation_id}, sender: {sender_id}, role: {role}")
        chat_history = Chat(
            room_conversation_id=room_conversation_id,
            sender_id=sender_id,
            message=message,
            agent_response_category=agent_response_category,
            agent_response_latency=agent_response_latency,
            agent_total_tokens=agent_total_tokens,
            agent_input_tokens=agent_input_tokens,
            agent_output_tokens=agent_output_tokens,
            agent_other_metrics=agent_other_metrics,
            agent_tools_call=agent_tools_call,
            role=role
        )
        self.db.add(chat_history)
        try:
            await self.db.commit()
            logger.info("Chat history saved successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error saving chat history: {e}", exc_info=True)
            await self.db.rollback()
            raise
        return message

    # --- Metode Baru untuk Mengubah Status Agen di Room ---
    async def set_room_agent_status(self, room_id: uuid.UUID, status: bool):
        """Mengupdate status agent_active untuk room tertentu."""
        logger.info(f"Setting agent_active status for room {room_id} to {status}")
        try:
            update_result = await self.db.execute(
                update(RoomConversation)
                .where(RoomConversation.id == room_id)
                .values(agent_active=status)
            )
            await self.db.commit()
            if update_result.rowcount > 0:
                logger.info(f"Agent status for room {room_id} updated to {status}.")
            else:
                logger.warning(f"Room {room_id} not found for agent status update.")
        except SQLAlchemyError as e:
            logger.error(f"Error updating agent status for room {room_id}: {e}", exc_info=True)
            await self.db.rollback()
            raise


    # ... (Metode set_admin_room_association dan remove_admin_room_association tetap sama) ...
    async def set_admin_room_association(self, admin_user_id: uuid.UUID, room_id: uuid.UUID):
         logger.info(f"Admin {admin_user_id} joining room {room_id}")
         self.admin_room_associations[admin_user_id] = room_id

    async def remove_admin_room_association(self, admin_user_id: uuid.UUID):
         if admin_user_id in self.admin_room_associations:
             room_id = self.admin_room_associations.pop(admin_user_id)
             logger.info(f"Admin {admin_user_id} leaving room {room_id}")


    # ... (Metode get_room_history tetap sama) ...
    async def get_room_history(self, room_id: uuid.UUID, limit: int = 50) -> List[Dict[str, Any]]:
         logger.debug(f"Fetching chat history for room {room_id} (limit: {limit})")
         try:
             results = await self.db.execute(
                 select(Chat)
                 .where(Chat.room_conversation_id == room_id)
                 .order_by(Chat.timestamp)
                 .limit(limit)
             )
             chats = results.scalars().all()

             history_list = []
             for chat in chats:
                 history_list.append({
                     "sender_id": str(chat.sender_id),
                     "message": chat.message,
                     "timestamp": chat.timestamp.isoformat() if chat.timestamp else None,
                 })
             logger.debug(f"Fetched {len(history_list)} chat history items for room {room_id}.")
             return history_list

         except SQLAlchemyError as e:
             logger.error(f"Error fetching chat history for room {room_id}: {e}", exc_info=True)
             return []


    # --- Modifikasi handle_user_message untuk Mengecek Status Agen ---

    async def handle_user_message(self, websocket: WebSocket, data: dict, user_id: uuid.UUID, room_id: uuid.UUID, start_time: float):
        type_data = data.get("type")
        print(f"Handling user message of type: {type_data}")
        file_loc = []
        
        if type_data != "message":
            file_name = data.get("file_name")
            file_type = data.get("file_type")
            file_size = data.get("file_size")
            file_data_base64 = data.get("file_data")

            print(f"Pesan file dari user {user_id} di room {room_id}: {file_name} ({file_type}, {file_size} bytes)")

            if not all([file_name, file_type, file_data_base64]):
                await websocket.send_json({"success": False, "error": "Data file tidak lengkap"})
                return

            # 1. Dekode Base64 ke biner
            file_bytes = base64.b64decode(file_data_base64)

            # 2. Tentukan path penyimpanan
            # Pastikan direktori ini ada atau buat jika belum ada
            upload_dir = "./resources/uploaded_files"
            os.makedirs(upload_dir, exist_ok=True)

            # Buat nama file unik untuk menghindari tabrakan
            unique_filename = f"{uuid.uuid4()}_{file_name}"
            file_path = os.path.join(upload_dir, unique_filename)
            valid_file_path = file_path + ".pdf"
            # 3. Simpan file ke disk
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            
            file_url = f"http://localhost:8001/static/{unique_filename}" 

            logger.info(f"File '{file_name}' saved to {file_path} with URL {file_url}")
            
            file_loc = [File(filepath=valid_file_path)]
            
            return file_loc
        
        message = data.get("message")
        
        print(f"Pesan dari user {user_id} di room {room_id}: {message}")

        if not message or message == None:
            await websocket.send_json({"success": False, "error": "Pesan diperlukan"})
            return

        try:
            # --- Cek Status Agen di Room ---
            room_result = await self.db.execute(
                select(RoomConversation.agent_active)
                .where(RoomConversation.id == room_id)
                .limit(1)
            )
            is_agent_active = room_result.scalar_one_or_none()

            # Simpan pesan user ke history (ini selalu dilakukan)
            await self.save_chat_history(
                 room_conversation_id=room_id,
                 sender_id=user_id,
                 message=message,
                 agent_response_category=None,
                 agent_response_latency=None,
                 agent_total_tokens=None,
                 agent_input_tokens=None,
                 agent_output_tokens=None,
                 agent_other_metrics=None,
                 agent_tools_call=None,
                 role="user" 
            )
            logger.info("User message saved.")
            # Kirim pesan user kembali ke user itu sendiri untuk konfirmasi UI
            # await websocket.send_json({"success": True, "data": question, "from": "user", "room_id": str(room_id)})


            if is_agent_active is False:
                # Agen tidak aktif, kirim notifikasi ke admin yang melihat room dan keluar
                logger.info(f"Agent is inactive for room {room_id}. Skipping agent call for user {user_id}.")
                # Opsional: Kirim pesan otomatis ke user "Admin sedang membantu Anda"
                # await websocket.send_json({"type": "info", "room_id": str(room_id), "message": "Seorang admin sedang membantu Anda."})

                # Kirim pesan user ke admin yang sedang melihat room ini
                await self._send_message_to_associated_admins(
                     room_id,
                     {"sender_id": str(user_id), "message": message, "role": "user", "room_id": str(room_id)}
                )
                return # Penting: Keluar dari metode, jangan panggil agen

            # --- Jika Agen Aktif, Lanjutkan Proses Pemanggilan Agen ---
            logger.info(f"Agent is active for room {room_id}. Calling agent for user {user_id}'s message.")
            # Cari ID chatbot untuk room ini dari DB
            chatbot_result = await self.db.execute(
                 select(Member.user_id).where(Member.room_conversation_id == room_id, Member.role == "chatbot")
            )
            chatbot_id = chatbot_result.scalar_one_or_none()

            if not chatbot_id:
                 logger.error(f"Chatbot member not found for room {room_id}")
                 await websocket.send_json({"success": False, "error": "Chatbot tidak ditemukan di room ini."})
                 # Tetap kirim pesan user ke admin meskipun chatbot tidak ada? Tergantung kebutuhan.
                 await self._send_message_to_associated_admins(
                      room_id,
                      {"sender_id": str(user_id), "message": message, "role": "user", "room_id": str(room_id)}
                 )
                 return # Keluar jika tidak ada chatbot untuk memproses

            # pdf_path = "/Users/cghuv/Documents/Project/AGENT-PROD/app/resources/uploaded_files/document_product_asrisyariah.pdf"
            
            # Panggil agent (asumsi agent.run sync)
            agent = call_customer_service_agent(str(chatbot_id), str(user_id), str(user_id))
            # agent_response = agent.run(message)
            print(f"file_loc", file_loc)
            agent_response = agent.run(message, files=file_loc)
            
            input_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'input_tokens', None)
            output_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'output_tokens', None)
            total_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'total_tokens', None)
            tools_call = getattr(agent_response, 'formatted_tool_calls', None)
            content = getattr(agent_response, 'content', None)
            print(f"Agent response content: {content}")
            
            if not content:
                category = ""
            else:
                category = self.classify_zero_shot(content)

            latency_seconds = time.time() - start_time
            latency=timedelta(seconds=latency_seconds)

            
            saved_response_message = await self.save_chat_history(
                room_conversation_id=room_id,
                sender_id=chatbot_id,
                message=content,
                agent_response_category=category,
                agent_response_latency=latency,
                agent_total_tokens=total_token,
                agent_input_tokens=input_token,
                agent_output_tokens=output_token,
                agent_other_metrics=None,
                agent_tools_call=tools_call,
                role="chatbot" 
            )
            logger.info("Chatbot response saved.")
            
            await websocket.send_json({"success": True, "data": saved_response_message, "from": "chatbot", "room_id": str(room_id)})
            # Kirim pesan user dan chatbot ke admin yang sedang melihat room ini
            await self._send_message_to_associated_admins(
                 room_id,
                 {"sender_id": str(user_id), "message": message, "role": "user", "room_id": str(room_id)}
            )
            await self._send_message_to_associated_admins(
                 room_id,
                 {"sender_id": str(chatbot_id), "message": content, "role": "chatbot", "room_id": str(room_id)}
            )
            
            #update room_conversation updated_at
            updated_at_room = (
                update(RoomConversation)
                .where(RoomConversation.id == room_id)
                .values(updated_at=datetime.utcnow())  # update eksplisit
            )
            await self.db.execute(updated_at_room)
            await self.db.commit()


            # Broadcast notifikasi umum ke SEMUA admin online (jika masih perlu dan berbeda dari stream)
            # await self._notify_all_online_admins_of_new_message(room_id, user_id, question, content)


        except Exception as e:
            logger.exception(f"Error handling user message (agent active path) for user {user_id} in room {room_id}:")
            # Di sini juga penting untuk mengirim pesan user ke admin jika terjadi error agent
            # await self._send_message_to_associated_admins(
            #      room_id,
            #      {"sender_id": str(user_id), "message": question, "role": "user", "room_id": str(room_id)}
            # )
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan saat memproses pesan: {e}"})


    async def handle_chatbot_message(self, websocket: WebSocket, data: dict, sender_id: uuid.UUID, room_id: uuid.UUID):
        # ... (Logika handler pesan dari chatbot (klien terpisah) tetap sama) ...
        message = data.get("message")
        if not message:
            await websocket.send_json({"error": "Pesan dari chatbot tidak valid."})
            return

        await self.save_chat_history(
            room_conversation_id=room_id,
            sender_id=sender_id,
            message=message,
            agent_response_category=None,
            agent_response_latency=None,
            agent_total_tokens=None,
            agent_input_tokens=None,
            agent_output_tokens=None,
            agent_other_metrics=None,
            agent_tools_call=None,
            role="chatbot" 
        )
        logger.info(f"Chatbot message saved for room: {room_id}, sender: {sender_id}")

        try:
            user_members_result = await self.db.execute(
                 select(Member).where(Member.room_conversation_id == room_id, Member.role == "user", Member.is_online == True)
            )
            user_members = user_members_result.scalars().all()

            for member in user_members:
                user_websocket = await self.get_active_websocket(member.user_id)
                if user_websocket:
                    try:
                        await user_websocket.send_json({"success": True, "data": message, "from": "chatbot", "room_id": str(room_id)})
                        logger.info(f"Pesan chatbot dikirim ke user {member.user_id} di room {room_id}")
                    except Exception as e:
                        logger.error(f"Gagal mengirim pesan chatbot ke user {member.user_id} di room {room_id}: {e}", exc_info=True)

            # Kirim pesan chatbot ke admin yang sedang melihat room ini
            await self._send_message_to_associated_admins(
                 room_id,
                 {"sender_id": str(sender_id), "message": message, "role": "chatbot", "room_id": str(room_id)}
            )


        except SQLAlchemyError as e:
             logger.error(f"Error fetching members in handle_chatbot_message for room {room_id}: {e}", exc_info=True)


    async def handle_admin_message(self, websocket: WebSocket, data: dict, sender_id: uuid.UUID, room_id: uuid.UUID):
        
        admin_message = data.get("message")

        try:
            # Periksa apakah target user adalah anggota room yang online
            target_member_result = await self.db.execute(
                select(Member).where(
                    Member.room_conversation_id == room_id,
                    # Member.user_id == target_user_id,
                    Member.role == "user",
                    Member.is_online == True
                )
            )
            target_member = target_member_result.scalar_one_or_none()
            print("target_member", target_member)

            if not target_member:
                await websocket.send_json({"success": False, "error": "User tidak ditemukan atau tidak aktif dalam room ini"})
                return

            target_conn = await self.get_active_websocket(target_member.user_id)
            print("target_conn", target_conn)
            if target_conn:
                # Simpan pesan admin
                await self.save_chat_history(
                    room_conversation_id=room_id,
                    sender_id=sender_id,
                    message=admin_message,
                    agent_response_category=None,
                    agent_response_latency=None,
                    agent_total_tokens=None,
                    agent_input_tokens=None,
                    agent_output_tokens=None,
                    agent_other_metrics=None,
                    agent_tools_call=None,
                    role="admin",
                )
                # Kirim pesan ke user target
                await target_conn.send_json({"success": True, "data": admin_message, "from": "admin", "room_id": str(room_id)})
                # Kirim konfirmasi atau pesan yang sama kembali ke admin yang mengirim
                # await websocket.send_json({"success": True, "message_sent": admin_message, "target_user_id": target_user_id_str, "room_id": str(room_id)})
                await websocket.send_json({"success": True, "message_sent": admin_message, "room_id": str(room_id)})
                logger.info(f"Pesan admin dari {sender_id} ke room {room_id} berhasil dikirim.")

                # Kirim pesan admin ke admin lain yang sedang melihat room ini
                await self._send_message_to_associated_admins(
                     room_id,
                     {"sender_id": str(sender_id), "message": admin_message, "role": "admin", "room_id": str(room_id)},
                     exclude_admin_id=sender_id
                )


            else:
                await websocket.send_json({"success": False, "error": "WebSocket target user tidak aktif"})

        except SQLAlchemyError as e:
            logger.error(f"Error in handle_admin_message for room {room_id}: {e}", exc_info=True)
            await self.db.rollback()
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan database: {e}"})
        except Exception as e:
            logger.error(f"Error in handle_admin_message for room {room_id}: {e}", exc_info=True)
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan: {e}"})
            
    async def handle_user_file(self, websocket: WebSocket, data: dict, user_id: uuid.UUID, room_id: uuid.UUID, start_time: float):
        
        file_loc = []
        
        file_name = data.get("file_name")
        file_type = data.get("file_type")
        file_size = data.get("file_size")
        file_data_base64 = data.get("file_data")

        print(f"Pesan file dari user {user_id} di room {room_id}: {file_name} ({file_type}, {file_size} bytes)")

        if not all([file_name, file_type, file_data_base64]):
            await websocket.send_json({"success": False, "error": "Data file tidak lengkap"})
            return

        # 1. Dekode Base64 ke biner
        file_bytes = base64.b64decode(file_data_base64)

        # 2. Tentukan path penyimpanan
        # Pastikan direktori ini ada atau buat jika belum ada
        upload_dir = "./resources/uploaded_files"
        os.makedirs(upload_dir, exist_ok=True)

        # Buat nama file unik untuk menghindari tabrakan
        unique_filename = f"{uuid.uuid4()}_{file_name}"
        file_path = os.path.join(upload_dir, unique_filename)
        valid_file_path = file_path
        # 3. Simpan file ke disk
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        file_url = f"http://localhost:8001/static/{unique_filename}" 

        logger.info(f"File '{file_name}' saved to {file_path} with URL {file_url}")
        
        file_loc = [File(filepath=valid_file_path)]

        try:
            # --- Cek Status Agen di Room ---
            room_result = await self.db.execute(
                select(RoomConversation.agent_active)
                .where(RoomConversation.id == room_id)
                .limit(1)
            )
            is_agent_active = room_result.scalar_one_or_none()

            # Simpan pesan user ke history (ini selalu dilakukan)
            await self.save_chat_history(
                 room_conversation_id=room_id,
                 sender_id=user_id,
                 message="file",
                 agent_response_category=None,
                 agent_response_latency=None,
                 agent_total_tokens=None,
                 agent_input_tokens=None,
                 agent_output_tokens=None,
                 agent_other_metrics=None,
                 agent_tools_call=None,
                 role="user" 
            )
            logger.info("User message saved.")
            # Kirim pesan user kembali ke user itu sendiri untuk konfirmasi UI
            # await websocket.send_json({"success": True, "data": question, "from": "user", "room_id": str(room_id)})


            if is_agent_active is False:
                # Agen tidak aktif, kirim notifikasi ke admin yang melihat room dan keluar
                logger.info(f"Agent is inactive for room {room_id}. Skipping agent call for user {user_id}.")
                # Opsional: Kirim pesan otomatis ke user "Admin sedang membantu Anda"
                # await websocket.send_json({"type": "info", "room_id": str(room_id), "message": "Seorang admin sedang membantu Anda."})

                # Kirim pesan user ke admin yang sedang melihat room ini
                await self._send_message_to_associated_admins(
                     room_id,
                     {"sender_id": str(user_id), "message": "file", "role": "user", "room_id": str(room_id)}
                )
                return # Penting: Keluar dari metode, jangan panggil agen

            # --- Jika Agen Aktif, Lanjutkan Proses Pemanggilan Agen ---
            logger.info(f"Agent is active for room {room_id}. Calling agent for user {user_id}'s message.")
            # Cari ID chatbot untuk room ini dari DB
            chatbot_result = await self.db.execute(
                 select(Member.user_id).where(Member.room_conversation_id == room_id, Member.role == "chatbot")
            )
            chatbot_id = chatbot_result.scalar_one_or_none()

            if not chatbot_id:
                 logger.error(f"Chatbot member not found for room {room_id}")
                 await websocket.send_json({"success": False, "error": "Chatbot tidak ditemukan di room ini."})
                 # Tetap kirim pesan user ke admin meskipun chatbot tidak ada? Tergantung kebutuhan.
                 await self._send_message_to_associated_admins(
                      room_id,
                      {"sender_id": str(user_id), "message": "file", "role": "user", "room_id": str(room_id)}
                 )
                 return # Keluar jika tidak ada chatbot untuk memproses

            # pdf_path = "/Users/cghuv/Documents/Project/AGENT-PROD/app/resources/uploaded_files/document_product_asrisyariah.pdf"
            
            # Panggil agent (asumsi agent.run sync)
            agent = call_customer_service_agent(str(chatbot_id), str(user_id), str(user_id))
            # agent_response = agent.run(message)
            print(f"file_loc", file_loc)
            agent_response = agent.run("Berikan kesimpulan dari document ini.", files=file_loc)
            
            input_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'input_tokens', None)
            output_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'output_tokens', None)
            total_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'total_tokens', None)
            tools_call = getattr(agent_response, 'formatted_tool_calls', None)
            content = getattr(agent_response, 'content', None)
            print(f"Agent response content: {content}")
            
            if not content:
                category = ""
            else:
                category = self.classify_zero_shot(content)

            latency_seconds = time.time() - start_time
            latency=timedelta(seconds=latency_seconds)

            
            saved_response_message = await self.save_chat_history(
                room_conversation_id=room_id,
                sender_id=chatbot_id,
                message=content,
                agent_response_category=category,
                agent_response_latency=latency,
                agent_total_tokens=total_token,
                agent_input_tokens=input_token,
                agent_output_tokens=output_token,
                agent_other_metrics=None,
                agent_tools_call=tools_call,
                role="chatbot" 
            )
            logger.info("Chatbot response saved.")
            
            await websocket.send_json({"success": True, "data": saved_response_message, "from": "chatbot", "room_id": str(room_id)})
            # Kirim pesan user dan chatbot ke admin yang sedang melihat room ini
            await self._send_message_to_associated_admins(
                 room_id,
                 {"sender_id": str(user_id), "message": "file", "role": "user", "room_id": str(room_id)}
            )
            await self._send_message_to_associated_admins(
                 room_id,
                 {"sender_id": str(chatbot_id), "message": content, "role": "chatbot", "room_id": str(room_id)}
            )
            
            #update room_conversation updated_at
            updated_at_room = (
                update(RoomConversation)
                .where(RoomConversation.id == room_id)
                .values(updated_at=datetime.utcnow())  # update eksplisit
            )
            await self.db.execute(updated_at_room)
            await self.db.commit()


            # Broadcast notifikasi umum ke SEMUA admin online (jika masih perlu dan berbeda dari stream)
            # await self._notify_all_online_admins_of_new_message(room_id, user_id, question, content)


        except Exception as e:
            logger.exception(f"Error handling user message (agent active path) for user {user_id} in room {room_id}:")
            # Di sini juga penting untuk mengirim pesan user ke admin jika terjadi error agent
            # await self._send_message_to_associated_admins(
            #      room_id,
            #      {"sender_id": str(user_id), "message": question, "role": "user", "room_id": str(room_id)}
            # )
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan saat memproses pesan: {e}"})

    # ... (handle_disconnect tetap sama) ...
    async def handle_disconnect(self, user_id: uuid.UUID, role: str, room_id: Optional[uuid.UUID]):
        logger.info(f"{role.capitalize()} {user_id} terputus.")
        if role == "admin":
             await self.remove_admin_room_association(user_id)

        if room_id:
            try:
                update_result = await self.db.execute(
                    update(Member)
                    .where(Member.user_id == user_id, Member.room_conversation_id == room_id)
                    .values(is_online=False)
                )
                await self.db.commit()

                if update_result.rowcount > 0:
                    logger.info(f"Status online member {user_id} di room {room_id} diperbarui menjadi False.")
                else:
                     logger.warning(f"Member {user_id} tidak ditemukan di room {room_id} dalam database saat disconnect.")

            except SQLAlchemyError as e:
                logger.error(f"Error in handle_disconnect for user {user_id} in room {room_id}: {e}", exc_info=True)
                await self.db.rollback()
        else:
            logger.info(f"User {user_id} disconnected without an associated room_id.")

    # ... (_send_message_to_associated_admins tetap sama) ...
    async def _send_message_to_associated_admins(self, room_id: uuid.UUID, message_data: Dict[str, Any], exclude_admin_id: Optional[uuid.UUID] = None):
        """Mengirim pesan baru ke semua admin yang saat ini diasosiasikan dengan room_id ini."""
        logger.debug(f"Sending new message from room {room_id} to associated admins.")
        try:
            for admin_user_id, associated_room_id in self.admin_room_associations.items():
                if associated_room_id == room_id:
                    if exclude_admin_id and admin_user_id == exclude_admin_id:
                         logger.debug(f"Skipping admin {admin_user_id} as they are the sender.")
                         continue

                    admin_websocket = await self.get_active_websocket(admin_user_id)
                    if admin_websocket:
                        try:
                            message_data_to_send = message_data.copy()
                            message_data_to_send["type"] = "room_message" # Tipe pesan untuk stream di admin UI
                            await admin_websocket.send_json(message_data_to_send)
                            logger.debug(f"Sent message from room {room_id} to associated admin {admin_user_id}.")
                        except Exception as e:
                            logger.error(f"Gagal mengirim pesan ke admin {admin_user_id} yang diasosiasikan dengan room {room_id}: {e}", exc_info=True)
                    else:
                        logger.warning(f"Admin {admin_user_id} diasosiasikan dengan room {room_id}, tetapi websocket tidak aktif.")

        except Exception as e:
            logger.error(f"Error sending message to associated admins for room {room_id}: {e}", exc_info=True)

    # ... (_notify_all_online_admins_of_new_message tetap sama) ...
    async def _notify_all_online_admins_of_new_message(self, room_id: uuid.UUID, user_id: uuid.UUID, question: str, answer: str):
        logger.info(f"Attempting to broadcast message notification from {user_id} in room {room_id} to ALL online admins.")
        try:
            online_admins_result = await self.db.execute(
                select(Member).where(Member.role == "admin", Member.is_online == True)
            )
            online_admins = online_admins_result.scalars().all()

            logger.debug(f"Found {len(online_admins)} online admins for notification.")

            for admin_member in online_admins:
                admin_user_id = admin_member.user_id
                admin_websocket = await self.get_active_websocket(admin_user_id)

                if admin_websocket:
                    try:
                        await admin_websocket.send_json({
                            "type": "message_notification",
                            "room_id": str(room_id),
                            "user_id": str(user_id),
                            "question": question,
                            "answer": answer,
                            "timestamp": time.time()
                        })
                        logger.info(f"Pesan notifikasi dari room {room_id} di-broadcast ke admin {admin_user_id}.")
                    except Exception as e:
                        logger.error(f"Gagal mengirim broadcast notifikasi ke admin {admin_user_id}: {e}", exc_info=True)
                else:
                    logger.warning(f"WebSocket untuk admin {admin_user_id} ditemukan online di DB, tetapi tidak aktif di state aplikasi.")
        except SQLAlchemyError as e:
            logger.error(f"Error fetching online admins for notification broadcast: {e}", exc_info=True)

    # ... (broadcast_active_rooms tetap sama) ...
    async def broadcast_active_rooms(self):
         logger.info("Attempting to broadcast active rooms to online admins.")
         try:
             online_members_count_query = select(
                 Member.room_conversation_id,
                 sqlalchemy.func.count().label('online_members_count')
             ).where(Member.is_online == True).group_by(Member.room_conversation_id).subquery()


             room_data_results = await self.db.execute(
                 select(RoomConversation.id, RoomConversation.status, online_members_count_query.c.online_members_count, RoomConversation.agent_active) # <-- Select agent_active juga
                 .outerjoin(online_members_count_query, RoomConversation.id == online_members_count_query.c.room_conversation_id)
                 .where(RoomConversation.status != "closed")
             )
             # Gunakan .all() atau .scalars().all() sesuai kebutuhan; .all() akan memberikan tuple (id, status, count, agent_active)
             room_data_list = room_data_results.all()


             active_rooms_data = []
             for room_id, status, online_count, agent_active_status in room_data_list: # <-- Ambil status agent
                  num_members_online = online_count if online_count is not None else 0

                  active_rooms_data.append({
                     "room_id": str(room_id),
                     "status": status,
                     "online_members": num_members_online,
                     "agent_active": agent_active_status, # <-- Kirim status agent
                  })

             online_admins_result = await self.db.execute(
                 select(Member).where(Member.role == "admin", Member.is_online == True)
             )
             online_admins = online_admins_result.scalars().all()

             logger.debug(f"Found {len(online_admins)} online admins for active rooms broadcast.")

             for admin_member in online_admins:
                 admin_user_id = admin_member.user_id
                 admin_websocket = await self.get_active_websocket(admin_user_id)

                 if admin_websocket:
                     try:
                         await admin_websocket.send_json({
                             "type": "active_rooms_update",
                             "rooms": active_rooms_data
                         })
                         logger.debug(f"✅ Berhasil kirim active_rooms_update ke admin {admin_user_id}")
                     except Exception as e:
                         logger.error(f"❌ Gagal kirim active_rooms_update ke admin {admin_user_id}: {e}", exc_info=True)
                 else:
                     logger.warning(f"WebSocket untuk admin {admin_user_id} ditemukan online di DB, tetapi tidak aktif di state aplikasi.")

         except SQLAlchemyError as e:
             logger.error(f"❌ Error broadcasting active rooms: {e}", exc_info=True)