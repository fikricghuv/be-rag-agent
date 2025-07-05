# app/services/user_service.py
import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, distinct
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends, HTTPException, status
from database.models import UserIds, Member 
from core.config_db import config_db
from datetime import datetime
from collections import defaultdict
from typing import Optional
from database.models.user_model import User
import bcrypt
from pydantic import BaseModel, EmailStr, Field
from database.enums.user_role_enum import UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserService:
    """
    Service class untuk mengelola operasi terkait user dan statistik.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi UserService dengan sesi database.

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

            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(int)

            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0 

            for month, count in monthly_counts_raw:
                if month in monthly_data: 
                    monthly_data[month] = count

            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly user additions (role 'user'): {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly user additions for role 'user': {e}", exc_info=True)
            return {}

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
            
            total_users = self.db.query(func.count(distinct(Member.user_id))).scalar()
            logger.info(f"Total unique users: {total_users}")
            return total_users if total_users is not None else 0
        
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting total users: {e}", exc_info=True)
            return {}
        
    def get_user_by_id(self, user_id: str) -> Optional['User']:
        """
        Mengambil data pengguna berdasarkan ID.
        Cocok untuk menampilkan profil pengguna tertentu.

        Args:
            user_id: ID unik pengguna (UUID string).

        Returns:
            Objek User jika ditemukan, None jika tidak.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching user with ID: {user_id}.")
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                logger.info(f"Successfully fetched user: {user.email}.")
            else:
                logger.warning(f"User with ID: {user_id} not found.")
            return user
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching user by ID {user_id}: {e}", exc_info=True)
            raise e

    def get_user_by_email(self, email: str) -> Optional['User']:
        """
        Mengambil data pengguna berdasarkan alamat email.
        Berguna untuk autentikasi atau pencarian profil.

        Args:
            email: Alamat email pengguna.

        Returns:
            Objek User jika ditemukan, None jika tidak.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching user with email: {email}.")
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                logger.info(f"Successfully fetched user: {user.full_name or user.email}.")
            else:
                logger.warning(f"User with email: {email} not found.")
            return user
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching user by email {email}: {e}", exc_info=True)
            raise e

    def update_user_profile(self, user_id: str, updates: dict) -> Optional['User']:
        """
        Memperbarui informasi profil pengguna berdasarkan ID.

        Args:
            user_id: ID unik pengguna (UUID string).
            updates: Dictionary berisi kolom-kolom yang akan diperbarui dan nilai barunya.
                     Contoh: {"full_name": "New Name", "is_active": False}

        Returns:
            Objek User yang telah diperbarui jika berhasil, None jika pengguna tidak ditemukan.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Updating profile for user ID: {user_id} with updates: {updates}.")
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User with ID: {user_id} not found for update.")
                return None

            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    logger.warning(f"Attempted to update non-existent field '{key}' for user ID {user_id}.")

            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Successfully updated user profile for ID: {user_id}.")
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error updating user profile for ID {user_id}: {e}", exc_info=True)
            raise e
    
    def create_user(self, email: EmailStr, password: str, full_name: Optional[str] = None, role: UserRole = UserRole.USER) -> User:
        """
        Membuat user baru dengan password yang di-hash.
        """
        logger.info(f"Attempting to create new user with email: {email}, role: {role.value}")

        # Periksa apakah email sudah ada
        existing_user = self.db.execute(
            self.db.query(User).filter(User.email == email)
        )
        if existing_user.scalar_one_or_none():
            logger.warning(f"User with email {email} already exists.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email sudah terdaftar."
            )

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Buat objek User baru
        new_user = User(
            email=email,
            password=hashed_password, # Simpan password yang sudah di-hash
            full_name=full_name,
            role=role 
        )

        self.db.add(new_user)
        try:
            self.db.commit()
            self.db.refresh(new_user)
            logger.info(f"Successfully created new user with ID: {new_user.id}")
            return new_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user {email}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Terjadi kesalahan saat menyimpan pengguna baru ke database."
            )

def get_user_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance ChatHistoryService dengan sesi database.
    """
    return UserService(db)