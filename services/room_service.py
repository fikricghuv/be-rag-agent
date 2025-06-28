# app/services/room_service.py
import logging 
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError 
from fastapi import Depends 
from typing import List
from database.models import RoomConversation
from core.config_db import config_db
from typing import Optional

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

    def get_active_rooms(self, offset: int, limit: int) -> List[RoomConversation]:
        """
        Mengambil data RoomConversation yang aktif dengan pagination.

        Args:
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of RoomConversation objects dengan status 'active'.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching active rooms with offset={offset}, limit={limit}.")
            
            active_rooms = self.db.query(RoomConversation)\
                .filter(RoomConversation.status == 'open')\
                .order_by(RoomConversation.updated_at.asc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            logger.info(f"Successfully fetched {len(active_rooms)} active room entries.")
            return active_rooms
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching active rooms: {e}", exc_info=True)
            raise e 

def get_room_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance RoomService dengan sesi database.
    """
    return RoomService(db)

