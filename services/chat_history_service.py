# app/services/chat_history_service.py
import uuid
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func, distinct, desc
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from fastapi import Depends # Diperlukan untuk Depends di dependency function
from typing import List, Dict, Any
# Asumsi model Chat, RoomConversation, Member diimpor dari database.models
from database.models import Chat, RoomConversation, Member
# Asumsi config_db diimpor dari core.config_db
from core.config_db import config_db

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryService:
    """
    Service class untuk mengelola operasi terkait riwayat chat dan statistik.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi ChatHistoryService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    # Metode untuk mengambil riwayat chat dengan pagination (sudah direfactor sebelumnya)
    def get_all_chat_history(self, offset: int = 0, limit: int = 100) -> List[Chat]:
        """
        Mengambil data Chat dengan pagination.

        Args:
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of Chat objects.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching all chat history from database with offset={offset}, limit={limit}.")
            chat_history = self.db.query(Chat)\
                .order_by(Chat.created_at)\
                .offset(offset)\
                .limit(limit)\
                .all()
            logger.info(f"Successfully fetched {len(chat_history)} chat entries.")
            return chat_history
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching all chat history with pagination: {e}", exc_info=True)
            raise e

    # Metode untuk menghitung total percakapan (sudah instance method)
    def get_total_conversations(self) -> int:
        """
        Menghitung total jumlah RoomConversation. Cocok untuk dashboard.

        Returns:
            Total count of RoomConversation.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Counting total conversations.")
            total_conversations = self.db.query(RoomConversation).count()
            logger.info(f"Total conversations: {total_conversations}")
            return total_conversations if total_conversations is not None else 0
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting total conversations: {e}", exc_info=True)
            raise e

    # Metode untuk menghitung total user unik (sudah instance method)
    def get_total_users(self) -> int:
        """
        Menghitung total jumlah user unik berdasarkan user_id di tabel Member.
        Cocok untuk dashboard.

        Args:
            db: SQLAlchemy Session object.

        Returns:
            Total count of unique users.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Counting total unique users.")
            # Menggunakan distinct untuk menghitung user_id yang unik
            total_users = self.db.query(func.count(distinct(Member.user_id))).scalar()
            logger.info(f"Total unique users: {total_users}")
            return total_users if total_users is not None else 0
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting total users: {e}", exc_info=True)
            raise e

    # Metode untuk menghitung frekuensi kategori (sudah instance method)
    def get_categories_by_frequency(self) -> List[Dict[str, Any]]:
        """
        Mengambil kategori respons agent dan menghitung frekuensinya,
        diurutkan dari yang terbanyak. Cocok untuk dashboard.

        Returns:
            List of dictionaries, each containing 'category' and 'count'.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Getting categories by frequency.")
            # Query untuk menghitung frekuensi setiap kategori
            # Mengabaikan entri dengan kategori None atau kosong
            category_counts = self.db.query(
                Chat.agent_response_category,
                func.count(Chat.agent_response_category).label('count')
            ).filter(
                Chat.agent_response_category.isnot(None),
                Chat.agent_response_category != ''
            ).group_by(
                Chat.agent_response_category
            ).order_by(
                desc('count') # Urutkan dari yang terbanyak
            ).all()

            # Format hasil menjadi list of dictionaries
            result = [{"category": cat, "count": count} for cat, count in category_counts]
            logger.info(f"Fetched {len(result)} categories.")
            return result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting categories by frequency: {e}", exc_info=True)
            raise e

    # --- Metode Baru: Mengambil riwayat chat untuk user spesifik ---
    def get_user_chat_history_by_user_id(self, user_id: uuid.UUID, offset: int = 0, limit: int = 100) -> List[Chat]:
        """
        Mengambil riwayat chat untuk user spesifik berdasarkan user_id, dengan pagination.

        Args:
            user_id: UUID dari user.
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of Chat objects terkait user_id. Mengembalikan list kosong jika user_id tidak ditemukan
            atau tidak memiliki riwayat chat.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching chat history for room {user_id} with offset={offset}, limit={limit}.")

            # Query untuk mengambil chat history berdasarkan sender_id (atau kolom yang relevan)
            # Asumsi Chat.sender_id adalah kolom yang menyimpan user_id yang mengirim pesan
            # Jika user_id di RoomConversation atau Member yang relevan, join tabel tersebut.
            # Contoh query berdasarkan sender_id di tabel Chat:
            # 1. Ambil semua room_conversation_id dari chat yang dikirim oleh user_id
            subquery = (
                self.db.query(Chat.room_conversation_id)
                .filter(Chat.sender_id == user_id)
                .distinct()
                .subquery()
            )

            # 2. Ambil semua chat berdasarkan room_conversation_id tersebut
            user_history = (
                self.db.query(Chat)
                .filter(Chat.room_conversation_id.in_(subquery))
                .order_by(Chat.created_at)
                .offset(offset)
                .limit(limit)
                .all()
            )

            logger.info(f"Successfully fetched {len(user_history)} chat entries for room {user_id}.")
            return user_history # Mengembalikan list objek SQLAlchemy

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching chat history for room {user_id}: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError
        except Exception as e:
            logger.error(f"Unexpected Error fetching chat history for room {user_id}: {e}", exc_info=True)
            # Re-raise sebagai SQLAlchemyError atau tangani secara spesifik jika bukan DB error
            raise SQLAlchemyError(f"Unexpected error: {e}")
        
    def get_user_chat_history_by_room_id(self, room_id: uuid.UUID, offset: int = 0, limit: int = 100) -> List[Chat]:
        """
        Mengambil riwayat chat untuk user spesifik berdasarkan room_id, dengan pagination.

        Args:
            room_id: UUID dari user.
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of Chat objects terkait room_id. Mengembalikan list kosong jika room_id tidak ditemukan
            atau tidak memiliki riwayat chat.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching chat history for room {room_id} with offset={offset}, limit={limit}.")

            # Query untuk mengambil chat history berdasarkan sender_id (atau kolom yang relevan)
            # Asumsi Chat.sender_id adalah kolom yang menyimpan room_id yang mengirim pesan
            # Jika room_id di RoomConversation atau Member yang relevan, join tabel tersebut.
            # Contoh query berdasarkan sender_id di tabel Chat:
            # Step 1: Ambil user_id dari Member yang memiliki role='user'
            user_member = self.db.query(Member.user_id)\
                .filter(
                    Member.room_conversation_id == room_id,
                    Member.role == 'user'
                )\
                .first()

            if not user_member:
                logger.warning(f"Tidak ditemukan member dengan role='user' di room {room_id}")
                return None

            user_id = user_member.user_id

            # Step 2: Ambil chat history
            history = self.db.query(Chat)\
                .filter(Chat.room_conversation_id == room_id)\
                .order_by(Chat.created_at)\
                .offset(offset)\
                .limit(limit)\
                .all()

            logger.info(f"Successfully fetched {len(history)} chat entries for room {room_id}.")

            return dict(
                user_id=user_id,
                history=history
            )
        # Mengembalikan list objek SQLAlchemy

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching chat history for room {room_id}: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError
        except Exception as e:
            logger.error(f"Unexpected Error fetching chat history for room {room_id}: {e}", exc_info=True)
            # Re-raise sebagai SQLAlchemyError atau tangani secara spesifik jika bukan DB error
            raise SQLAlchemyError(f"Unexpected error: {e}")



# Dependency function untuk menyediakan instance ChatHistoryService
def get_chat_history_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance ChatHistoryService dengan sesi database.
    """
    return ChatHistoryService(db)
