# app/services/room_service.py
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import select # Keep select for potential future use, though query is used now
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError for specific error handling
from fastapi import Depends # Import Depends for dependency function
from typing import List, Dict, Any # Diperlukan untuk type hinting
# Asumsi model RoomConversation diimpor dari database.models
from database.models import RoomConversation
# Asumsi config_db diimpor dari core.config_db
from core.config_db import config_db

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
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

    # Metode untuk mengambil semua room dengan pagination
    def get_all_rooms(self, offset: int, limit: int) -> List[RoomConversation]:
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
            # Menggunakan self.db dan menerapkan pagination
            rooms = self.db.query(RoomConversation)\
                .offset(offset)\
                .limit(limit)\
                .all() # Menggunakan .all() setelah limit/offset
            logger.info(f"Successfully fetched {len(rooms)} room entries.")
            return rooms
        except SQLAlchemyError as e:
            # Log error detail di sini, tapi biarkan exception propagate
            logger.error(f"SQLAlchemy Error fetching all rooms: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError

    # --- Metode Baru: Mengambil hanya active room dengan pagination ---
    # Asumsi ada kolom 'status' di model RoomConversation dan nilai 'active' menandakan room aktif
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
            # Menggunakan self.db, memfilter berdasarkan status='active', dan menerapkan pagination
            active_rooms = self.db.query(RoomConversation)\
                .filter(RoomConversation.status == 'open')\
                .order_by(RoomConversation.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            logger.info(f"Successfully fetched {len(active_rooms)} active room entries.")
            return active_rooms
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching active rooms: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError


# Dependency function untuk menyediakan instance RoomService
def get_room_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance RoomService dengan sesi database.
    """
    return RoomService(db)

