import logging 
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy import func, or_, String, cast
from fastapi import Depends 
from typing import List, Optional
from core.config_db import config_db
from database.models.chat_model import Chat
from database.models.room_conversation_model import RoomConversation
from schemas.room_conversation_schema import RoomConversationResponse
from exceptions.custom_exceptions import DatabaseException

logger = logging.getLogger(__name__)

class RoomService:
    """
    Service class untuk mengelola operasi terkait room conversations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_all_rooms(self, offset: int, limit: int) -> List[RoomConversation]:
        try:
            logger.info(f"[SERVICE][ROOM] Fetching all rooms (offset={offset}, limit={limit})")
            rooms = self.db.query(RoomConversation)\
                .offset(offset)\
                .limit(limit)\
                .all() 
            logger.info(f"[SERVICE][ROOM] Successfully fetched {len(rooms)} rooms.")
            return rooms
        
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][ROOM] SQLAlchemy Error on get_all_rooms: {e}", exc_info=True)
            raise DatabaseException("Failed to fetch rooms from the database")

    def get_active_rooms(self, offset: int, limit: int, search: Optional[str] = None) -> List[RoomConversationResponse]:
        try:
            logger.info(f"[SERVICE][ROOM] Fetching active rooms (offset={offset}, limit={limit}, search={search})")

            latest_chat_subquery = (
                self.db.query(
                    Chat.room_conversation_id,
                    func.max(Chat.created_at).label("latest_chat")
                )
                .group_by(Chat.room_conversation_id)
                .subquery()
            )

            latest_message_subquery = (
                self.db.query(
                    Chat.room_conversation_id,
                    Chat.message,
                    Chat.created_at
                )
                .join(
                    latest_chat_subquery,
                    (Chat.room_conversation_id == latest_chat_subquery.c.room_conversation_id) &
                    (Chat.created_at == latest_chat_subquery.c.latest_chat)
                )
                .subquery()
            )

            query = (
                self.db.query(
                    RoomConversation,
                    latest_message_subquery.c.message.label("last_message"),
                    latest_message_subquery.c.created_at.label("last_time_message")
                )
                .join(latest_message_subquery, RoomConversation.id == latest_message_subquery.c.room_conversation_id)
                .filter(RoomConversation.status == 'open')
            )

            if search:
                search_pattern = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(cast(RoomConversation.id, String)).like(search_pattern),
                        func.lower(RoomConversation.name).like(search_pattern),
                        func.lower(latest_message_subquery.c.message).like(search_pattern)
                    )
                )

            query = query.order_by(latest_message_subquery.c.created_at.desc())\
                         .offset(offset)\
                         .limit(limit)

            results = query.all()

            response = [
                RoomConversationResponse(
                    id=room.id,
                    name=room.name,
                    description=room.description,
                    status=room.status,
                    created_at=room.created_at,
                    updated_at=room.updated_at,
                    agent_active=room.agent_active,
                    lastMessage=last_msg,
                    lastTimeMessage=last_time
                )
                for room, last_msg, last_time in results
            ]

            logger.info(f"[SERVICE][ROOM] Fetched {len(response)} active rooms.")
            return response

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][ROOM] SQLAlchemy Error (active rooms): {e}", exc_info=True)
            raise DatabaseException("Failed to fetch active rooms from the database")

def get_room_service(db: Session = Depends(config_db)) -> RoomService:
    return RoomService(db)
