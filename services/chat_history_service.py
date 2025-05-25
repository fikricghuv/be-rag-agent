# app/services/chat_history_service.py
import uuid
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func, distinct, desc
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from fastapi import Depends # Diperlukan untuk Depends di dependency function
from typing import List, Dict, Any
from collections import defaultdict
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
        
    def get_total_tokens_used(self) -> float:
        """
        Menghitung total jumlah token yang digunakan di seluruh riwayat chat.
        Menjumlahkan kolom 'agent_total_tokens' dari tabel Chat.

        Returns:
            Total jumlah token sebagai integer. Mengembalikan 0 jika tidak ada token atau terjadi kesalahan.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Calculating total tokens used across all chat history.")
            # Menggunakan func.sum() untuk menjumlahkan kolom agent_total_tokens
            # .scalar() akan mengambil hasil tunggal dari query (jumlah total)
            total_tokens = self.db.query(func.sum(Chat.agent_total_tokens)).scalar()
            
            # Jika tidak ada chat atau agent_total_tokens adalah NULL, sum akan mengembalikan None
            # Kita mengembalikan 0 dalam kasus tersebut.
            result = total_tokens if total_tokens is not None else 0
            logger.info(f"Total tokens used: {result}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error calculating total tokens used: {e}", exc_info=True)
            raise e

    def get_total_conversations(self) -> int:
        """
        Menghitung total jumlah percakapan berdasarkan room_conversation_id di tabel Chat.

        Returns:
            Total count of unique conversations.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Counting total unique conversations.")
            # Menggunakan distinct untuk menghitung room_conversation_id yang unik
            total_conversations = self.db.query(func.count(distinct(Chat.id))).scalar()
            logger.info(f"Total unique conversations: {total_conversations}")
            return total_conversations if total_conversations is not None else 0
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting total conversations: {e}", exc_info=True)
            raise e
        
    def get_monthly_conversations(self) -> Dict[str, int]:
        """
        Mengambil total percakapan per bulan.
        Percakapan dihitung berdasarkan room_conversation_id unik dari tabel Chat.
        Mengembalikan dictionary dengan format: {'YYYY-MM': count}
        Jika bulan tidak ada data, akan diisi dengan 0.
        """
        try:
            logger.info("Getting monthly total conversations.")
            monthly_conversation_counts_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                func.count(distinct(Chat.id)).label('count')
            ).group_by('month').order_by('month').all()

            # Inisialisasi dictionary dengan semua bulan dari Januari hingga bulan saat ini
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(int)

            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0 # Default ke 0

            # Isi data dari database
            for month, count in monthly_conversation_counts_raw:
                if month in monthly_data: # Hanya tambahkan jika bulan ada di rentang tahun ini
                    monthly_data[month] = count

            # Urutkan berdasarkan kunci bulan
            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly total conversations: {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly total conversations: {e}", exc_info=True)
            raise e
        
    def get_daily_average_latency_seconds(self):
        """
        Mengambil latensi rata-rata harian dalam detik (float).
        Mengembalikan dictionary dengan format: {'YYYY-MM-DD': avg_latency_seconds}
        Jika hari tidak ada data, akan diisi dengan 0.0.
        """
        try:
            logger.info("Getting daily average latency in seconds (float).")
            # Query untuk menghitung rata-rata latensi harian dalam detik
            daily_latency_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM-DD').label('day'),
                func.avg(func.extract('epoch', Chat.agent_response_latency)).label('avg_latency_seconds')
            ).filter(Chat.agent_response_latency.isnot(None)).group_by('day').order_by('day').all()

            current_date = datetime.now().date()
            daily_data = defaultdict(float) # Gunakan float untuk rata-rata

            # Loop untuk menginisialisasi semua hari dalam bulan berjalan
            for i in range(1, current_date.day + 1):
                day_str = f"{current_date.year}-{current_date.month:02d}-{i:02d}"
                daily_data[day_str] = 0.0 # Default ke 0.0

            for day, avg_latency_seconds in daily_latency_raw:
                if day in daily_data:
                    daily_data[day] = round(avg_latency_seconds, 2) # Bulatkan 2 desimal

            sorted_result = dict(sorted(daily_data.items()))
            logger.info(f"Daily average latency (seconds): {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting daily average latency in seconds: {e}", exc_info=True)
            raise e

    def get_monthly_average_latency_seconds(self):
        """
        Mengambil latensi rata-rata bulanan dalam detik (float).
        Mengembalikan dictionary dengan format: {'YYYY-MM': avg_latency_seconds}
        Jika bulan tidak ada data, akan diisi dengan 0.0.
        """
        try:
            logger.info("Getting monthly average latency in seconds (float).")
            monthly_latency_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                func.avg(func.extract('epoch', Chat.agent_response_latency)).label('avg_latency_seconds')
            ).filter(Chat.agent_response_latency.isnot(None)).group_by('month').order_by('month').all()

            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(float)

            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0.0

            for month, avg_latency_seconds in monthly_latency_raw:
                if month in monthly_data:
                    monthly_data[month] = round(avg_latency_seconds, 2)

            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly average latency (seconds): {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly average latency in seconds: {e}", exc_info=True)
            raise e


# Dependency function untuk menyediakan instance ChatHistoryService
def get_chat_history_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance ChatHistoryService dengan sesi database.
    """
    return ChatHistoryService(db)
