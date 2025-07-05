# app/services/room_service.py
import logging 
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy import func
from fastapi import Depends 
from typing import List, Optional
from database.models import RoomConversation
from core.config_db import config_db
from database.models.chat_model import Chat
from database.models.room_conversation_model import RoomConversation
from schemas.room_conversation_schema import RoomConversationResponse

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

class RoomService:
    """
    Service class untuk mengelola operasi terkait room conversations.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi RoomService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    def get_all_rooms(self, offset: int, limit: int) -> Optional[List[RoomConversation]]:
        """
        Mengambil semua data RoomConversation dengan pagination.
        Cocok untuk tampilan admin.

        Args:
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of RoomConversation objects.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching all rooms with offset={offset}, limit={limit}.")
            
            rooms = self.db.query(RoomConversation)\
                .offset(offset)\
                .limit(limit)\
                .all() 
            logger.info(f"Successfully fetched {len(rooms)} room entries.")
            return rooms
        
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching all rooms: {e}", exc_info=True)
            raise e 

    # def get_active_rooms(self, offset: int, limit: int) -> List[RoomConversation]:
    #     """
    #     Mengambil data RoomConversation yang aktif dengan pagination.

    #     Args:
    #         offset: Jumlah item yang akan dilewati.
    #         limit: Jumlah item per halaman.

    #     Returns:
    #         List of RoomConversation objects dengan status 'active'.
    #     Raises:
    #         SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
    #     """
    #     try:
    #         logger.info(f"Fetching active rooms with offset={offset}, limit={limit}.")
            
    #         active_rooms = self.db.query(RoomConversation)\
    #             .filter(RoomConversation.status == 'open')\
    #             .order_by(RoomConversation.updated_at.asc())\
    #             .offset(offset)\
    #             .limit(limit)\
    #             .all()
            
    #         logger.info(f"Successfully fetched {len(active_rooms)} active room entries.")
    #         return active_rooms
    #     except SQLAlchemyError as e:
    #         logger.error(f"SQLAlchemy Error fetching active rooms: {e}", exc_info=True)
    #         raise e 
    
    def get_active_rooms(self, offset: int, limit: int) -> List[RoomConversationResponse]:
        try:
            logger.info(f"Fetching active rooms ordered by latest chat...")

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

            results = (
                self.db.query(
                    RoomConversation,
                    latest_message_subquery.c.message.label("last_message"),
                    latest_message_subquery.c.created_at.label("last_time_message")
                )
                .join(latest_message_subquery, RoomConversation.id == latest_message_subquery.c.room_conversation_id)
                .filter(RoomConversation.status == 'open')
                .order_by(latest_message_subquery.c.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Build response
            response_list = []
            for room, last_msg, last_time in results:
                response_list.append(RoomConversationResponse(
                    id=room.id,
                    name=room.name,
                    description=room.description,
                    status=room.status,
                    created_at=room.created_at,
                    updated_at=room.updated_at,
                    agent_active=room.agent_active,
                    lastMessage=last_msg,
                    lastTimeMessage=last_time
                ))

            return response_list

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching active rooms by latest chat: {e}", exc_info=True)
            raise e


def get_room_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance RoomService dengan sesi database.
    """
    return RoomService(db)

