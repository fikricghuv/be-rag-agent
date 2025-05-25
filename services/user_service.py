# app/services/chat_history_service.py

import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func, distinct, desc
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends
from database.models import UserIds, Member # Pastikan UserRole diimpor
from core.config_db import config_db
from datetime import datetime
from collections import defaultdict

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserService:
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

    def get_monthly_user_additions(self) -> dict[str, int]:
        """
        Mengambil total penambahan user per bulan dengan filter role="user".
        Mengembalikan dictionary dengan format: {'YYYY-MM': count}
        Jika bulan tidak ada data, akan diisi dengan 0.
        """
        try:
            logger.info("Getting monthly user additions for role 'user'.")
            monthly_counts_raw = self.db.query(
                func.to_char(UserIds.created_at, 'YYYY-MM').label('month'),
                func.count(UserIds.id).label('count')
            ).filter(UserIds.role == "user").group_by('month').order_by('month').all()

            # Inisialisasi dictionary dengan semua bulan dari Januari hingga bulan saat ini
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(int)

            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0 # Default ke 0

            # Isi data dari database
            for month, count in monthly_counts_raw:
                if month in monthly_data: # Hanya tambahkan jika bulan ada di rentang tahun ini
                    monthly_data[month] = count

            # Urutkan berdasarkan kunci bulan
            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly user additions (role 'user'): {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly user additions for role 'user': {e}", exc_info=True)
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

# Dependency function untuk menyediakan instance ChatHistoryService
def get_user_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance ChatHistoryService dengan sesi database.
    """
    return UserService(db)