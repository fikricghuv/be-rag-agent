# services/chat_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from agents.customer_service_agent.customer_service_agent import call_customer_service_agent
from fastapi import WebSocket
import time
from database.models import RoomConversation, Member, Chat
from typing import Dict, Optional, List, Any
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
import uuid
import logging
from datetime import timedelta
from sqlalchemy.future import select
from sqlalchemy import update
import sqlalchemy
from openai import OpenAI
from datetime import datetime
from agno.media import File
import base64
import os
import subprocess
import tempfile
import os
from agno.media import Audio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agents.classification_agent.classification_message_agent import classify_chat_agent
from agents.audio_handler_agent.audio_agent import speech_to_text
from services.notification_service import NotificationService
from database.models.user_model import UserFCM, User
from services.fcm_service import FCMService

client = OpenAI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession, redis, active_websockets: Dict[uuid.UUID, WebSocket]):
        # self.db: AsyncSession = db
        self.active_websockets = active_websockets
        self.redis = redis
        self.classify_chat_agent = classify_chat_agent
        self.speech_to_text = speech_to_text
        self.notification_service = NotificationService(db, redis)
        self.fcm_service = FCMService(db)
        
    async def get_active_websocket(self, user_id: uuid.UUID) -> Optional[WebSocket]:
        logger.debug(f"🔍 Mencari websocket aktif untuk user_id: {user_id}")
        return self.active_websockets.get(user_id)

    async def find_or_create_room_and_add_member(self, db: AsyncSession, user_id: uuid.UUID, role: str) -> uuid.UUID:
        
        try:
            result = await db.execute(
                select(RoomConversation.id)
                .join(Member, Member.room_conversation_id == RoomConversation.id)
                .where(Member.user_id == user_id, RoomConversation.status != "closed")
                .limit(1)
            )
            existing_room_id = result.scalar_one_or_none()

            if existing_room_id:
                room_uuid = existing_room_id
                logger.info(f"Found existing room {room_uuid} for user {user_id}.")

                member_result = await db.execute(
                    select(Member).where(Member.room_conversation_id == room_uuid, Member.user_id == user_id)
                )
                member = member_result.scalar_one_or_none()
                if member:
                    if not member.is_online:
                         await db.execute(
                             update(Member)
                             .where(Member.id == member.id)
                             .values(is_online=True)
                         )
                         await db.commit()
                         logger.info(f"Updated user {user_id} online status in room {room_uuid}.")
                else:
                    new_member = Member(
                        id=uuid.uuid4(),
                        room_conversation_id=room_uuid,
                        user_id=user_id,
                        role=role,
                        is_online=True,
                    )
                    db.add(new_member)
                    await db.commit()
                    logger.warning(f"User {user_id} not found in existing room {room_uuid} database entry, added new member.")

            else:
                room_uuid = uuid.uuid4()
                logger.info(f"Creating new room: {room_uuid} for user: {user_id}")

                new_room = RoomConversation(id=room_uuid, status="open", agent_active=True) 
                db.add(new_room)

                user_member_id = uuid.uuid4()
                user_member = Member(
                    id=user_member_id,
                    room_conversation_id=room_uuid,
                    user_id=user_id,
                    role=role,
                    is_online=True,
                )
                db.add(user_member)
                logger.info(f"Added user member {user_member_id} to new room {room_uuid}.")

                chatbot_member_user_id = uuid.uuid4()
                chatbot_member_id = uuid.uuid4()
                chatbot_member = Member(
                    id=chatbot_member_id,
                    room_conversation_id=room_uuid,
                    user_id=chatbot_member_user_id,
                    role="chatbot",
                    is_online=False,
                )
                db.add(chatbot_member)
                logger.info(f"Added chatbot member {chatbot_member_id} ({chatbot_member_user_id}) to new room {room_uuid}.")


                await db.commit()

            return room_uuid

        except SQLAlchemyError as e:
            logger.error(f"Error in find_or_create_room_and_add_member: {e}", exc_info=True)
            await db.rollback()
            raise

    async def save_chat_history(
       self,
       db: AsyncSession,
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
        db.add(chat_history)
        try:
            await db.commit()
            logger.info("Chat history saved successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error saving chat history: {e}", exc_info=True)
            await db.rollback()
            raise
        return message

    async def handle_user_message(self, db: AsyncSession, websocket: WebSocket, data: dict, user_id: uuid.UUID, room_id: uuid.UUID, start_time: float):
        message = data.get("message")
        logger.debug(f"User {user_id} sent message in room {room_id}: {message}")

        if not message:
            await websocket.send_json({"success": False, "error": "Message is required"})
            return

        try:
            room_result = await db.execute(
                select(RoomConversation.agent_active).where(RoomConversation.id == room_id).limit(1)
            )
            is_agent_active = room_result.scalar_one_or_none()

            await self.save_chat_history(
                db,
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

            await self._send_message_to_associated_admins(
                room_id,
                {"sender_id": str(user_id), "message": message, "role": "user", "room_id": str(room_id)}
            )

            if not is_agent_active:
                logger.info(f"Agent is inactive in room {room_id}")
                return

            chatbot_result = await db.execute(
                select(Member.user_id).where(
                    Member.room_conversation_id == room_id,
                    Member.role == "chatbot"
                )
            )
            chatbot_id = chatbot_result.scalar_one_or_none()

            if not chatbot_id:
                logger.error(f"Chatbot not found in room {room_id}")
                await websocket.send_json({"success": False, "error": "Chatbot not found in this room."})
                return

            agent = call_customer_service_agent(str(chatbot_id), str(user_id), str(user_id))
            logger.debug(f"Running agent for message: {message}")
            agent_response = agent.run(message)

            input_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'input_tokens', None)
            output_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'output_tokens', None)
            total_token = getattr(getattr(agent_response.messages[-1], 'metrics', None), 'total_tokens', None)
            tools_call = getattr(agent_response, 'formatted_tool_calls', None)
            content = getattr(agent_response, 'content', None)

            category = self.classify_chat_agent(content) if content else ""
            latency = timedelta(seconds=(time.time() - start_time))

            saved_response_message = await self.save_chat_history(
                db,
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

            await websocket.send_json({
                "success": True,
                "data": saved_response_message,
                "from": "chatbot",
                "room_id": str(room_id)
            })

            await self._send_message_to_associated_admins(
                room_id,
                {"sender_id": str(chatbot_id), "message": content, "role": "chatbot", "room_id": str(room_id)}
            )

            await db.execute(
                update(RoomConversation)
                .where(RoomConversation.id == room_id)
                .values(updated_at=datetime.utcnow())
            )
            await db.commit()
            
            # admin_fcm_tokens = await self.get_all_admin_fcm_tokens(db)

            # for fcm_token in admin_fcm_tokens:
            #     logger.info(f"Broadcasting message to {fcm_token} admins.")
            #     # sebelumnya:
            #     await self.fcm_service.send_message(
            #         fcm_token,
            #         title="Pesan Baru di Chat",
            #         body=f"User mengirim pesan di Room {room_id}"
            #     )

            #     await self.notification_service.create_notification(
            #         receiver_id=None, 
            #         message=f"User mengirim pesan di Room {room_id}",
            #         notif_type="chat",
            #         is_broadcast=True
            #     )
            
            admin_fcm_tokens = await self.get_all_admin_fcm_tokens(db)

            for user_id, fcm_token in admin_fcm_tokens:
                logger.info(f"Broadcasting message to user_id={user_id} with token={fcm_token}")

                await self.fcm_service.send_message(
                    fcm_token,
                    title="Pesan Baru di Chat",
                    body=f"User mengirim pesan di Room {room_id}"
                )

                await self.notification_service.create_notification(
                    receiver_id=user_id,
                    message=f"User mengirim pesan di Room {room_id}",
                    notif_type="chat",
                    is_broadcast=True
                )


        except Exception as e:
            logger.exception(f"Error handling user message in room {room_id}: {e}")
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan saat memproses pesan: {str(e)}"})

    async def handle_chatbot_message(self, db : AsyncSession, websocket: WebSocket, data: dict, sender_id: uuid.UUID, room_id: uuid.UUID):
        
        message = data.get("message")
        if not message:
            await websocket.send_json({"error": "Pesan dari chatbot tidak valid."})
            return

        await self.save_chat_history(
            db,
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
            user_members_result = await db.execute(
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

            await self._send_message_to_associated_admins(
                 room_id,
                 {"sender_id": str(sender_id), "message": message, "role": "chatbot", "room_id": str(room_id)}
            )

        except SQLAlchemyError as e:
             logger.error(f"Error fetching members in handle_chatbot_message for room {room_id}: {e}", exc_info=True)

    async def handle_admin_message(self, db : AsyncSession, websocket: WebSocket, data: dict, sender_id: uuid.UUID, room_id: uuid.UUID):
        
        admin_message = data.get("message")

        try:
            target_member_result = await db.execute(
                select(Member).where(
                    Member.room_conversation_id == room_id,
                    Member.role == "user",
                    Member.is_online == True
                )
            )
            target_member = target_member_result.scalar_one_or_none()

            if not target_member:
                await websocket.send_json({"success": False, "error": "User tidak ditemukan atau tidak aktif dalam room ini"})
                return

            target_conn = await self.get_active_websocket(target_member.user_id)
            if target_conn:
                
                await self.save_chat_history(
                    db,
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
                
                await target_conn.send_json({"success": True, "data": admin_message, "from": "admin", "room_id": str(room_id)})
                
                await websocket.send_json({"success": True, "message_sent": admin_message, "room_id": str(room_id)})
                logger.info(f"Pesan admin dari {sender_id} ke room {room_id} berhasil dikirim.")

                await self._send_message_to_associated_admins(
                     room_id,
                     {"sender_id": str(sender_id), "message": admin_message, "role": "admin", "room_id": str(room_id)},
                     exclude_admin_id=sender_id
                )

            else:
                await websocket.send_json({"success": False, "error": "WebSocket target user tidak aktif"})

        except SQLAlchemyError as e:
            logger.error(f"Error in handle_admin_message for room {room_id}: {e}", exc_info=True)
            await db.rollback()
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan database: {e}"})
        except Exception as e:
            logger.error(f"Error in handle_admin_message for room {room_id}: {e}", exc_info=True)
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan: {e}"})
            
    async def handle_user_file(self, db: AsyncSession, websocket: WebSocket, data: dict, user_id: uuid.UUID, room_id: uuid.UUID, start_time: float):
        try:
            
            file_name = data.get("file_name")
            file_type = data.get("file_type")
            file_size = data.get("file_size")
            file_data_base64 = data.get("file_data")

            if not all([file_name, file_type, file_data_base64]):
                await websocket.send_json({"success": False, "error": "Data file tidak lengkap"})
                return

            logger.debug(f"User {user_id} mengirim file '{file_name}' ({file_type}, {file_size} bytes) di room {room_id}")

            try:
                file_bytes = base64.b64decode(file_data_base64)
            except Exception as decode_err:
                logger.exception("Gagal mendekode file base64." + decode_err)
                await websocket.send_json({"success": False, "error": "Gagal membaca file. Format base64 tidak valid."})
                return

            upload_dir = "./resources/uploaded_files"
            os.makedirs(upload_dir, exist_ok=True)
            unique_filename = f"{uuid.uuid4()}_{file_name}"
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            file_url = f"http://localhost:8001/static/{unique_filename}"
            logger.info(f"File disimpan di {file_path}, tersedia di {file_url}")

            await self.save_chat_history(
                db,
                room_conversation_id=room_id,
                sender_id=user_id,
                message="upload file | "+ unique_filename,
                agent_response_category=None,
                agent_response_latency=None,
                agent_total_tokens=None,
                agent_input_tokens=None,
                agent_output_tokens=None,
                agent_other_metrics=None,
                agent_tools_call=None,
                role="user"
            )

            await self._send_message_to_associated_admins(
                room_id,
                {"sender_id": str(user_id), "message": "upload file | "+ unique_filename, "urlFile":file_url, "role": "user", "room_id": str(room_id)}
            )

            result = await db.execute(
                select(RoomConversation.agent_active).where(RoomConversation.id == room_id).limit(1)
            )
            is_agent_active = result.scalar_one_or_none()

            if not is_agent_active:
                logger.info(f"Agent tidak aktif di room {room_id}, tidak memanggil agent.")
                return

            file_loc = [File(filepath=file_path)]
            chatbot_result = await db.execute(
                select(Member.user_id).where(Member.room_conversation_id == room_id, Member.role == "chatbot")
            )
            chatbot_id = chatbot_result.scalar_one_or_none()

            if not chatbot_id:
                logger.warning(f"Chatbot tidak ditemukan di room {room_id}")
                await websocket.send_json({"success": False, "error": "Chatbot tidak ditemukan di room ini."})
                return

            agent = call_customer_service_agent(str(chatbot_id), str(user_id), str(user_id))
            agent_response = agent.run("""berikan 1 kalimat inti dari dokumen tersebut dan 
                                       tanyakan kepada user apa yang ingin diketahui dari dokumen ini.""", files=file_loc)

            metrics = getattr(agent_response.messages[-1], 'metrics', None)
            content = getattr(agent_response, 'content', '')

            latency_seconds = time.time() - start_time
            category = self.classify_chat_agent(content) if content else ""

            await self.save_chat_history(
                db,
                room_conversation_id=room_id,
                sender_id=chatbot_id,
                message=content,
                agent_response_category=category,
                agent_response_latency=timedelta(seconds=latency_seconds),
                agent_total_tokens=getattr(metrics, 'total_tokens', None),
                agent_input_tokens=getattr(metrics, 'input_tokens', None),
                agent_output_tokens=getattr(metrics, 'output_tokens', None),
                agent_other_metrics=None,
                agent_tools_call=getattr(agent_response, 'formatted_tool_calls', None),
                role="chatbot"
            )

            await websocket.send_json({
                "success": True,
                "from": "chatbot",
                "room_id": str(room_id),
                "message_type": "message",
                "data": content
            })

            await self._send_message_to_associated_admins(
                room_id,
                {"sender_id": str(chatbot_id), "message": content, "role": "chatbot", "room_id": str(room_id)}
            )

            await db.execute(
                update(RoomConversation)
                .where(RoomConversation.id == room_id)
                .values(updated_at=datetime.utcnow())
            )
            await db.commit()

        except Exception as e:
            logger.exception(f"Gagal menangani file dari user {user_id} di room {room_id}")
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan saat memproses file: {e}"})
            
    async def handle_user_audio(self, db: AsyncSession, websocket: WebSocket, data: dict, user_id: uuid.UUID, room_id: uuid.UUID, start_time: float):

        file_name = data.get("file_name")
        mime_type = data.get("mime_type") 
        duration = data.get("duration")
        file_data_base64 = data.get("file_data")

        logger.debug(f"Voice note from user {user_id} in room {room_id}: {file_name}, type={mime_type}, duration={duration}")

        if not all([file_name, mime_type, file_data_base64]):
            await websocket.send_json({"success": False, "error": "Data voice note tidak lengkap"})
            return

        file_bytes = base64.b64decode(file_data_base64)

        upload_dir = "./resources/uploaded_files"
        os.makedirs(upload_dir, exist_ok=True)
        unique_filename = f"{uuid.uuid4()}_{file_name}"
        original_file_path = os.path.join(upload_dir, unique_filename)

        with open(original_file_path, "wb") as f:
            f.write(file_bytes)

        file_url = f"http://localhost:8001/static/{unique_filename}"
        logger.info(f"Voice note saved to {original_file_path}, URL: {file_url}")

        try:
            audio_format = self.detect_audio_format(mime_type)

            if audio_format == "webm":
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_in:
                    tmp_in.write(file_bytes)
                    tmp_in.flush()
                    webm_path = tmp_in.name

                wav_path = webm_path.replace(".webm", ".wav")

                subprocess.run(
                    ["ffmpeg", "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )

                with open(wav_path, "rb") as f:
                    file_bytes = f.read()

                audio_format = "wav"

                os.remove(webm_path)
                os.remove(wav_path)

        except Exception as conv_err:
            logger.exception("Failed to convert webm to wav:")
            await websocket.send_json({"success": False, "error": f"Gagal mengonversi audio: {conv_err}"})
            return

        try:
            chatbot_result = await db.execute(
                select(Member.user_id).where(Member.room_conversation_id == room_id, Member.role == "chatbot")
            )
            chatbot_id = chatbot_result.scalar_one_or_none()

            if not chatbot_id:
                logger.error(f"Chatbot not found for room {room_id}")
                await websocket.send_json({"success": False, "error": "Chatbot tidak ditemukan di room ini."})
                return

            transcribe = speech_to_text(file_bytes)

            content_translate = getattr(transcribe, 'content', '')
            logger.info("content_translate : " + content_translate)
            
            if not content_translate:
                await websocket.send_json({"success": False, "error": "Tidak dapat mengekstrak isi voice note."})
                return
            
            await self.save_chat_history(
                db,
                room_conversation_id=room_id,
                sender_id=user_id,
                message="voice note | "+ content_translate,
                agent_response_category=None,
                agent_response_latency=None,
                agent_total_tokens=None,
                agent_input_tokens=None,
                agent_output_tokens=None,
                agent_other_metrics=None,
                agent_tools_call=None,
                role="user"
            )
            
            await self._send_message_to_associated_admins(
                room_id,
                {"sender_id": str(user_id), "message": "voice note | "+ content_translate, "urlFile":file_url, "role": "user", "room_id": str(room_id)}
            )
            
            agent = call_customer_service_agent(str(chatbot_id), str(user_id), str(user_id))
            
            agent_response = agent.run(content_translate)
            
            content = getattr(agent_response, 'content', '')

            latency_seconds = time.time() - start_time
            latency = timedelta(seconds=latency_seconds)

            await self.save_chat_history(
                db,
                room_conversation_id=room_id,
                sender_id=chatbot_id,
                message=content,
                role="chatbot",
                agent_response_latency=latency,
                agent_response_category=self.classify_chat_agent(content),
                agent_input_tokens=getattr(getattr(agent_response.messages[-1], 'metrics', None), 'input_tokens', None),
                agent_output_tokens=getattr(getattr(agent_response.messages[-1], 'metrics', None), 'output_tokens', None),
                agent_total_tokens=getattr(getattr(agent_response.messages[-1], 'metrics', None), 'total_tokens', None),
                agent_tools_call=getattr(agent_response, 'formatted_tool_calls', None)
            )

            await websocket.send_json({"success": True, "data": content, "from": "chatbot", "room_id": str(room_id)})

        except Exception as e:
            logger.exception("Error processing voice note:")
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan saat memproses voice note: {e}"})

    def detect_audio_format(self, mime_type: str) -> str:
        """Convert MIME type to agno.Audio format string."""
        if "webm" in mime_type:
            return "webm"
        elif "wav" in mime_type:
            return "wav"
        elif "mp3" in mime_type:
            return "mp3"
        else:
            return "wav"

    async def handle_disconnect(self, db: AsyncSession, user_id: uuid.UUID, role: str, room_id: Optional[uuid.UUID]):
        logger.info(f"{role.capitalize()} {user_id} terputus.")
        
        await self.mark_offline(user_id, role)

        if room_id:
            try:
                update_result = await db.execute(
                    update(Member)
                    .where(Member.user_id == user_id or Member.room_conversation_id == room_id)
                    .values(is_online=False)
                )
                await db.commit()

                if update_result.rowcount > 0:
                    logger.info(f"Status online member {user_id} di room {room_id} diperbarui menjadi False.")
                else:
                     logger.warning(f"Member {user_id} tidak ditemukan di room {room_id} dalam database saat disconnect.")

            except SQLAlchemyError as e:
                logger.error(f"Error in handle_disconnect for user {user_id} in room {room_id}: {e}", exc_info=True)
                await db.rollback()
        else:
            logger.info(f"User {user_id} disconnected without an associated room_id.")
    
    async def mark_online(self, user_id: uuid.UUID, role: str):
        key = f"online_{role}s" 
        logger.debug(f"Marking {role} {user_id} as online in Redis.")
        await self.redis.sadd(key, str(user_id))

    async def mark_offline(self, user_id: uuid.UUID, role: str):
        key = f"online_{role}s"
        logger.debug(f"Marking {role} {user_id} as offline in Redis.")
        await self.redis.srem(key, str(user_id))

    async def get_all_online(self, role: str) -> List[uuid.UUID]:
        key = f"online_{role}s"
        members = await self.redis.smembers(key)
        logger.debug(f"Found {len(members)} online {role}s in Redis.")
        return [uuid.UUID(m.decode() if isinstance(m, bytes) else m) for m in members]

    async def _send_message_to_associated_admins(self, room_id: uuid.UUID, message_data: Dict[str, Any], exclude_admin_id: Optional[uuid.UUID] = None):
        logger.debug(f"Sending new message from room {room_id} to associated admins.")
        try:
            for admin_user_id in self.active_websockets.keys():
                if exclude_admin_id and admin_user_id == exclude_admin_id:
                    continue

                room_in_redis = await self.redis.get(f"admin_room:{str(admin_user_id)}")
                if room_in_redis != str(room_id):
                    continue

                admin_ws = await self.get_active_websocket(admin_user_id)
                if admin_ws:
                    try:
                        message_data_to_send = message_data.copy()
                        message_data_to_send["type"] = "room_message"
                        await admin_ws.send_json(message_data_to_send)
                        logger.debug(f"Sent message from room {room_id} to associated admin {admin_user_id}.")
                    except Exception as e:
                        logger.error(f"Gagal mengirim pesan ke admin {admin_user_id} yang diasosiasikan dengan room {room_id}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error sending message to associated admins for room {room_id}: {e}", exc_info=True)

    async def broadcast_active_rooms(self, db: AsyncSession):
        logger.info("Attempting to broadcast active rooms to online admins.")
        try:
           
            online_members_count_query = select(
                Member.room_conversation_id,
                sqlalchemy.func.count().label('online_members_count')
            ).where(Member.is_online == True).group_by(Member.room_conversation_id).subquery()

            room_data_results = await db.execute(
                select(
                    RoomConversation.id,
                    RoomConversation.status,
                    online_members_count_query.c.online_members_count,
                    RoomConversation.agent_active 
                )
                .outerjoin(online_members_count_query, RoomConversation.id == online_members_count_query.c.room_conversation_id)
                .where(RoomConversation.status != "closed")
            )
            
            room_data_list = room_data_results.all()

            active_rooms_data = []
            for room_id, status, online_count, agent_active_status in room_data_list:
                num_members_online = online_count if online_count is not None else 0
                active_rooms_data.append({
                    "room_id": str(room_id),
                    "status": status,
                    "online_members": num_members_online,
                    "agent_active": agent_active_status,
                })

            online_admin_uuids = await self.get_all_online("admin")
            logger.debug(f"Found {len(online_admin_uuids)} online admins from Redis for active rooms broadcast.")

            for admin_user_id in online_admin_uuids:
                
                admin_websocket = self.active_websockets.get(admin_user_id) 

                if admin_websocket:
                    try:
                        await admin_websocket.send_json({
                            "type": "active_rooms_update",
                            "rooms": active_rooms_data
                        })
                        logger.debug(f"✅ Successfully sent active_rooms_update to admin {admin_user_id}")
                    except Exception as e:
                        
                        logger.error(f"❌ Failed to send active_rooms_update to admin {admin_user_id}: {e}", exc_info=True)
                else:
                    
                    logger.warning(f"WebSocket for admin {admin_user_id} found online in Redis, but not active in this application state.")

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during broadcast_active_rooms: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ General error during broadcast_active_rooms: {e}", exc_info=True)
    
    async def get_admin_ids_in_room(self, db: AsyncSession, room_id: UUID) -> List[UUID]:
        result = await db.execute(
            select(Member.user_id)
            .where(Member.room_conversation_id == room_id, Member.role == "admin")
        )
        return [row[0] for row in result.all()]
    
    async def get_fcm_token(self, db: AsyncSession, user_id: UUID) -> Optional[str]:
        logger.info(f"admin {user_id} menerima notifikasi.")
        result = await db.execute(
            select(UserFCM.token).where(UserFCM.user_id == user_id)
        )
        token = result.scalar_one_or_none()
        logger.info(f"admin {user_id} dengan fcm {token} menerima notifikasi.")
        return token
        
    # async def get_all_admin_fcm_tokens(self, db: AsyncSession) -> list[str]:
    #     stmt = select(UserFCM.token).join(User)
    #     result = await db.execute(stmt)
    #     return [row[0] for row in result.fetchall()]
    
    async def get_all_admin_fcm_tokens(self, db: AsyncSession) -> list[tuple[UUID, str]]:
        stmt = select(User.id, UserFCM.token).join(UserFCM).where(UserFCM.token.isnot(None))
        result = await db.execute(stmt)
        return result.fetchall()



