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
from sqlalchemy import update, and_
from openai import OpenAI
from datetime import datetime
from agno.media import File
import base64
import os
import subprocess
import tempfile
import os
import json
from agno.media import Audio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agents.classification_agent.classification_message_agent import classify_chat_agent
from agents.audio_handler_agent.audio_agent import speech_to_text
from services.notification_service import NotificationService
from database.models.user_model import UserFCM, User
from services.fcm_service import FCMService
from exceptions.custom_exceptions import ServiceException, DatabaseException
from sqlalchemy.orm import selectinload

client = OpenAI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession, redis, 
                 active_admin_websockets: Dict[uuid.UUID, Dict[uuid.UUID, WebSocket]],
                active_user_websockets: Dict[uuid.UUID, Dict[uuid.UUID, WebSocket]]
                ):
        self.active_admin_websockets = active_admin_websockets
        self.active_user_websockets = active_user_websockets
        self.redis = redis
        self.classify_chat_agent = classify_chat_agent
        self.speech_to_text = speech_to_text
        self.notification_service = NotificationService(db, redis)
        self.fcm_service = FCMService(db)
    
    async def get_active_admin_ws(self, client_id: uuid.UUID, admin_id: uuid.UUID) -> Optional[WebSocket]:
        return self.active_admin_websockets.get(client_id, {}).get(admin_id)

    async def get_active_user_ws(self, client_id: uuid.UUID, user_id: uuid.UUID) -> Optional[WebSocket]:
        return self.active_user_websockets.get(client_id, {}).get(user_id)

    async def find_or_create_room_and_add_member(self, db: AsyncSession, user_id: uuid.UUID, role: str, client_id: UUID) -> uuid.UUID:
        
        try:
            result = await db.execute(
                select(RoomConversation.id)
                .join(Member, Member.room_conversation_id == RoomConversation.id)
                .where(
                    Member.user_id == user_id,
                    RoomConversation.status != "closed",
                    RoomConversation.client_id == client_id
                )
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

                new_room = RoomConversation(
                    id=room_uuid, 
                    client_id=client_id,
                    status="open", 
                    agent_active=True
                )
                db.add(new_room)

                user_member_id = uuid.uuid4()
                user_member = Member(
                    id=user_member_id,
                    client_id=client_id,
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
                    client_id=client_id,
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
            raise DatabaseException("FIND_OR_CREATE_ROOM", "Error in find_or_create_room_and_add_member.")

    async def save_chat_history(
       self,
       db: AsyncSession,
       room_conversation_id: uuid.UUID,
       sender_id: uuid.UUID,
       message: str,
       client_id: UUID,
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
            role=role,
            client_id=client_id
        )
        db.add(chat_history)
        try:
            await db.commit()
            logger.info("Chat history saved successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error saving chat history: {e}", exc_info=True)
            await db.rollback()
            raise DatabaseException("SAVE_CHAT_HISTORY", "Error saving chat history.")
        
        return message

    async def handle_user_message(self, db: AsyncSession, websocket: WebSocket, data: dict, user_id: uuid.UUID, room_id: uuid.UUID, start_time: float, client_id: UUID):
        message = data.get("message")
        logger.info(f"User {user_id} sent message in room {room_id}: {message}")

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
                role="user",
                client_id=client_id
            )
            logger.info("User message saved.")

            await self._send_message_to_associated_admins(
                client_id,
                room_id,
                {"user_id": str(user_id), "message": message, "role": "user", "room_id": str(room_id)}
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

            agent = call_customer_service_agent(str(chatbot_id), str(user_id), str(user_id), client_id)
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
                role="chatbot",
                client_id=client_id
            )
            logger.info("Chatbot response saved.")

            await websocket.send_json({
                "success": True,
                "message": saved_response_message,
                "sender": "chatbot",
                "room_id": str(room_id),
                "sender_id": str(chatbot_id),
                "type": "message"
            })

            await self._send_message_to_associated_admins(
                client_id,
                room_id,
                {"user_id": str(chatbot_id), "message": content, "role": "chatbot", "room_id": str(room_id)}
            )

            await db.execute(
                update(RoomConversation)
                .where(and_(
                    RoomConversation.id == room_id,
                    RoomConversation.client_id == client_id
                ))
                .values(updated_at=datetime.utcnow())
            )
            await db.commit()
            
            admin_fcm_tokens = await self.get_all_admin_fcm_tokens(db, client_id)

            for user_id, fcm_token in admin_fcm_tokens:
                logger.info(f"Broadcasting message to user_id={user_id} with token={fcm_token}")

                await self.fcm_service.send_message(
                    fcm_token,
                    title="Pesan Baru di Chat",
                    body=f"User mengirim pesan di Room {room_id}"
                )

                await self.notification_service.create_notification(
                    receiver_id=user_id,
                    client_id=client_id,
                    message=f"User mengirim pesan di Room {room_id}",
                    notif_type="chat",
                    is_broadcast=True
                )

        except Exception as e:
            logger.exception(f"Error handling user message in room {room_id}: {e}")
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan saat memproses pesan: {str(e)}"})

    async def handle_chatbot_message(self, db : AsyncSession, websocket: WebSocket, data: dict, sender_id: uuid.UUID, room_id: uuid.UUID, client_id: UUID):
        
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
            role="chatbot",
            client_id=client_id 
        )
        logger.info(f"Chatbot message saved for room: {room_id}, sender: {sender_id}")

        try:
            user_members_result = await db.execute(
                select(Member)
                .where(
                    and_(
                        Member.room_conversation_id == room_id,
                        Member.role == "user",
                        Member.is_online == True,
                        Member.client_id == client_id
                    )
                )
            )
            user_members = user_members_result.scalars().all()

            for member in user_members:
                user_websocket = await self.get_active_user_ws(client_id, member.user_id)
                if user_websocket:
                    try:
                        await user_websocket.send_json({
                        "success": True,
                        "message": message,
                        "sender": "chatbot",
                        "room_id": str(room_id),
                        "sender_id": str(sender_id),
                        "type": "message"
                    })
                        logger.info(f"Pesan chatbot dikirim ke user {member.user_id} di room {room_id}")
                    except Exception as e:
                        logger.error(f"Gagal mengirim pesan chatbot ke user {member.user_id} di room {room_id}: {e}", exc_info=True)

            await self._send_message_to_associated_admins(
                client_id,
                room_id,
                {"sender_id": str(sender_id), "message": message, "role": "chatbot", "room_id": str(room_id)}
            )

        except SQLAlchemyError as e:
            logger.error(f"Error fetching members in handle_chatbot_message for room {room_id}: {e}", exc_info=True)
            raise DatabaseException("FETCH_MEMBER", "Error fetching members in handle_chatbot_message.")

    async def handle_admin_message(
        self,
        db: AsyncSession,
        websocket: WebSocket,
        data: dict,
        sender_id: uuid.UUID,
        room_id: uuid.UUID,
        client_id: uuid.UUID
    ):
        admin_message = data.get("message")
        logger.info(f"[CHAT_SERVICE] Admin {sender_id} mengirim pesan di room {room_id}: {admin_message}")

        try:
            # Ambil member dengan preloading user relasi agar tidak lazy-load di luar session
            target_member_result = await db.execute(
                select(Member).where(
                    Member.room_conversation_id == room_id,
                    Member.role == "user",
                    Member.client_id == client_id
                )
            )
            target_member = target_member_result.scalar_one_or_none()

            if not target_member:
                await websocket.send_json({"success": False, "error": "User tidak ditemukan dalam room ini"})
                return

            # Ambil user_id dengan aman
            target_user_id = getattr(target_member, "user_id", None)
            logger.info(f"[CHAT_SERVICE] Target member user_id: {target_user_id}")

            if not target_user_id:
                await websocket.send_json({"success": False, "error": "Target user tidak memiliki user_id"})
                return

            # Cek online users di Redis
            online_users = await self.get_all_online("user", client_id)
            logger.info(f"[CHAT_SERVICE] Online users in Redis: {online_users}")

            if target_user_id not in online_users:
                logger.info(f"[REDIS][CHECK] User {target_user_id} tidak online")
                await self.save_chat_history(
                    db,
                    room_conversation_id=room_id,
                    sender_id=sender_id,
                    message=admin_message,
                    role="admin",
                    client_id=client_id
                )
                await websocket.send_json({"success": False, "error": "User tidak aktif"})
                return

            # Refresh TTL Redis
            await self.refresh_online_ttl(target_user_id, "user", client_id, ttl_seconds=30)
            logger.info(f"[REDIS][REFRESH] TTL untuk user {target_user_id} diperbarui")

            # Simpan chat history
            await self.save_chat_history(
                db,
                room_conversation_id=room_id,
                sender_id=sender_id,
                message=admin_message,
                role="admin",
                client_id=client_id
            )

            # channel = f"chat_user:{target_user_id}"
            # event = {
            #     "message": admin_message,
            #     "from": str(sender_id),
            #     "target_user_id": str(target_user_id)
            # }
            # await self.redis.publish(channel, json.dumps(event))
            # logger.debug(f"[REDIS] Published message to {channel}")

            # Kirim konfirmasi ke websocket
            # await websocket.send_json({
            #     "success": True,
            #     "message_sent": admin_message,
            #     "room_id": str(room_id)
            # })
            
            user_websocket = await self.get_active_user_ws(client_id, target_user_id)
            
            if user_websocket:
                try:
                    await user_websocket.send_json({
                        "success": True,
                        "message": admin_message,
                        "sender": "admin",
                        "room_id": str(room_id),
                        "sender_id": str(sender_id),
                        "type": "message"
                    })

                    logger.info(f"Pesan admin {sender_id} dikirim ke user {target_user_id} di room {room_id}")
                except Exception as e:
                    logger.error(f"Gagal mengirim pesan admin ke user {target_user_id} di room {room_id}: {e}", exc_info=True)
            else:
                logger.info(f"Websocket untuk user {target_user_id} tidak ditemukan atau tidak aktif dan isi pesan admin {admin_message}.")
            
        except SQLAlchemyError as e:
            logger.error(f"Error in handle_admin_message for room {room_id}: {e}", exc_info=True)
            await db.rollback()
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan database: {e}"})
            raise DatabaseException("ADMIN_MESSAGE", "Error in handle_admin_message.")

        except Exception as e:
            logger.error(f"Error in handle_admin_message for room {room_id}: {e}", exc_info=True)
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan: {e}"})
            raise ServiceException("ADMIN_MESSAGE", 400, "Error in handle admin message")

    async def handle_disconnect(self, db: AsyncSession, user_id: uuid.UUID, role: str, room_id: Optional[uuid.UUID], client_id: UUID):
        logger.info(f"{role.capitalize()} {user_id} terputus untuk client {client_id}.")

        await self.mark_offline(user_id, role, client_id)

        if room_id:
            try:
                
                update_result = await db.execute(
                    update(Member)
                    .where(
                        and_(
                            Member.user_id == user_id,
                            Member.room_conversation_id == room_id,
                            Member.client_id == client_id 
                        )
                    )
                    .values(is_online=False)
                )
                await db.commit()

                if update_result.rowcount > 0:
                    logger.info(f"✅ Status online member {user_id} di room {room_id} (client {client_id}) diperbarui menjadi False.")
                else:
                    logger.warning(f"⚠️ Member {user_id} tidak ditemukan di room {room_id} untuk client {client_id}.")

            except SQLAlchemyError as e:
                logger.error(f"❌ Error in handle_disconnect for user {user_id} in room {room_id}, client {client_id}: {e}", exc_info=True)
                await db.rollback()
                raise DatabaseException("HANDLE_DISCONNECT", "Error in handle_disconnect")
        else:
            logger.info(f"User {user_id} disconnected without an associated room_id (client {client_id}).")

    async def mark_online(self, user_id: uuid.UUID, role: str, client_id: UUID, ttl_seconds: int = 30):
        key = f"online:{client_id}:{role}s"
        await self.redis.sadd(key, str(user_id))
        # await self.redis.expire(key, ttl_seconds)  
        logger.debug(f"[REDIS][SET] Mark {role} {user_id} online, TTL={ttl_seconds}s")

    async def refresh_online_ttl(self, user_id: uuid.UUID, role: str, client_id: UUID, ttl_seconds: int = 30):
        key = f"online:{client_id}:{role}s"
        exists = await self.redis.sismember(key, str(user_id))
        if exists:
            # await self.redis.expire(key, ttl_seconds)
            logger.debug(f"[REDIS][REFRESH] Refreshed TTL for {role} {user_id} to {ttl_seconds}s")

    async def mark_offline(self, user_id: uuid.UUID, role: str, client_id: UUID):
        key = f"online:{client_id}:{role}s"
        await self.redis.srem(key, str(user_id))
        logger.debug(f"[REDIS][DEL] Mark {role} {user_id} offline")

    async def get_all_online(self, role: str, client_id: UUID) -> List[uuid.UUID]:
        key = f"online:{client_id}:{role}s"
        members = await self.redis.smembers(key)
        return [uuid.UUID(m.decode() if isinstance(m, bytes) else m) for m in members]
    
    async def is_online(self, user_id: uuid.UUID, role: str, client_id: UUID) -> bool:
        key = f"online:{client_id}:{role}s"
        exists = await self.redis.sismember(key, str(user_id))
        logger.debug(f"[REDIS][CHECK] Is {role} {user_id} online? {exists}")
        return bool(exists)

    async def set_user_room_mapping(self, user_id: UUID, client_id: UUID, role: str, room_id: Optional[UUID] = None, ttl: int = 3600):
        key = f"{role}_room:{user_id}:{client_id}"
        value = {
            "room": str(room_id) if room_id else None,
            "client": str(client_id)
        }
        logger.debug(f"[REDIS][SET] Menyimpan mapping {key} -> {value}")
        await self.redis.set(key, json.dumps(value), ex=ttl)
        
    async def delete_user_room_mapping(self, user_id: UUID, client_id: UUID, role: str):
        key = f"{role}_room:{user_id}:{client_id}"
        logger.debug(f"[REDIS][DEL] Menghapus mapping {key}")
        await self.redis.delete(key)

    async def _send_message_to_associated_admins(
        self,
        client_id: UUID,
        room_id: UUID,
        message_data: Dict[str, Any],
        exclude_admin_id: Optional[UUID] = None,
    ):
        log_prefix = f"[client={client_id} room={room_id}]"
        logger.info(f"{log_prefix} Preparing to send message to associated admins.")

        admins = self.active_admin_websockets.get(client_id, {})
        logger.info(f"{log_prefix} Found {len(admins)} active admin websockets.")

        if not admins:
            return

        for admin_user_id, ws_conn in admins.items():
            if exclude_admin_id and admin_user_id == exclude_admin_id:
                logger.debug(f"{log_prefix} Skipping excluded admin {admin_user_id}.")
                continue

            try:
                payload = {**message_data, "type": "message"}
                await ws_conn.send_json(payload)
                logger.info(f"{log_prefix} Sent message to admin {admin_user_id}.")
            except Exception as e:
                logger.error(f"{log_prefix} Failed to send to admin {admin_user_id}: {e}", exc_info=True)

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
    
    # async def get_all_admin_fcm_tokens(self, db: AsyncSession) -> list[tuple[UUID, str]]:
    #     stmt = select(User.id, UserFCM.token).join(UserFCM).where(UserFCM.token.isnot(None))
    #     result = await db.execute(stmt)
    #     return result.fetchall()
    async def get_all_admin_fcm_tokens(
        self, db: AsyncSession, client_id: UUID
    ) -> list[tuple[UUID, str]]:
        stmt = (
            select(User.id, UserFCM.token)
            .join(UserFCM, User.id == UserFCM.user_id)
            .where(
                UserFCM.token.isnot(None),
                User.client_id == client_id,   # filter by client
                User.is_active.is_(True)       # optional: hanya user aktif
            )
        )
        result = await db.execute(stmt)
        return result.fetchall()

    async def subscribe_user_events(self, user_id: uuid.UUID):
        pubsub = self.redis.pubsub()
        channel = f"chat_user:{user_id}"
        await pubsub.subscribe(channel)
        logger.info(f"[REDIS][SUBSCRIBE] Listening on {channel}")

        try:
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue
                try:
                    data = json.loads(msg["data"])
                except Exception as e:
                    logger.error(f"[REDIS] Invalid JSON: {e}")
                    continue

                ws = self.active_websockets.get(user_id)
                if ws:
                    await ws.send_json({
                        "success": True,
                        "data": data["message"],
                        "from": data["from"]
                    })
                else:
                    logger.debug(f"[WS] User {user_id} offline di instance ini.")
        finally:
            await pubsub.unsubscribe(channel)



