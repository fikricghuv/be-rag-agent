import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, distinct
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends, HTTPException, status
from database.models import UserIds, Member
from core.config_db import config_db
from datetime import datetime
from typing import Optional
from database.models.user_model import User
import bcrypt
from pydantic import EmailStr
from database.enums.user_role_enum import UserRole
from exceptions.custom_exceptions import DatabaseException
from uuid import UUID

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_monthly_user_additions(self, client_id: UUID) -> dict[str, int]:
        """
        Mengambil jumlah user baru per bulan (khusus role 'user') berdasarkan client_id.
        """
        try:
            logger.info(f"[SERVICE][USER] Getting monthly user additions for client {client_id}")

            monthly_counts = (
                self.db.query(
                    func.to_char(UserIds.created_at, 'YYYY-MM').label('month'),
                    func.count(UserIds.id).label('count')
                )
                .filter(UserIds.role == "user", UserIds.client_id == client_id)
                .group_by('month')
                .order_by('month')
                .all()
            )

            now = datetime.now()
            monthly_data = {f"{now.year}-{i:02d}": 0 for i in range(1, now.month + 1)}

            for month, count in monthly_counts:
                if month in monthly_data:
                    monthly_data[month] = count

            logger.info(f"[SERVICE][USER] Monthly user additions: {monthly_data}")
            return dict(sorted(monthly_data.items()))

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][USER] SQLAlchemy Error (monthly additions): {e}", exc_info=True)
            raise DatabaseException("Failed to fetch monthly user additions")

    def get_total_users(self, client_id: UUID) -> int:
        """
        Menghitung total unique user berdasarkan client_id.
        """
        try:
            logger.info(f"[SERVICE][USER] Counting total unique users for client {client_id}")
            total = self.db.query(func.count(distinct(Member.user_id)))\
                           .filter(Member.client_id == client_id)\
                           .scalar()
            logger.info(f"[SERVICE][USER] Total users: {total}")
            return total or 0
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][USER] SQLAlchemy Error (total users): {e}", exc_info=True)
            raise DatabaseException("Failed to count total users")

    def get_user_by_id(self, user_id: UUID, client_id: UUID) -> Optional[User]:
        """
        Mengambil user berdasarkan ID dan client_id.
        """
        try:
            logger.info(f"[SERVICE][USER] Fetching user by ID: {user_id}")
            user = self.db.query(User).filter(User.id == user_id, User.client_id == client_id).first()
            if user:
                logger.info(f"[SERVICE][USER] Found user: {user.email}")
            else:
                logger.warning(f"[SERVICE][USER] User with ID {user_id} not found")
            return user
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][USER] SQLAlchemy Error (get_user_by_id): {e}", exc_info=True)
            raise DatabaseException("Failed to fetch user from the database")

    def get_user_by_email(self, email: str, client_id: UUID) -> Optional[User]:
        """
        Mengambil user berdasarkan email dan client_id.
        """
        try:
            logger.info(f"[SERVICE][USER] Fetching user by email: {email}")
            user = self.db.query(User).filter(User.email == email, User.client_id == client_id).first()
            if user:
                logger.info(f"[SERVICE][USER] Found user: {user.full_name or user.email}")
            else:
                logger.warning(f"[SERVICE][USER] User with email {email} not found")
            return user
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][USER] SQLAlchemy Error (get_user_by_email): {e}", exc_info=True)
            raise DatabaseException("Failed to fetch user by email")

    def update_user_profile(self, user_id: UUID, updates: dict, client_id: UUID) -> Optional[User]:
        """
        Memperbarui profil user berdasarkan user_id dan client_id.
        """
        try:
            logger.info(f"[SERVICE][USER] Updating profile for user ID: {user_id}")
            user = self.db.query(User).filter(User.id == user_id, User.client_id == client_id).first()
            if not user:
                logger.warning(f"[SERVICE][USER] User with ID {user_id} not found")
                return None

            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    logger.warning(f"[SERVICE][USER] Invalid field '{key}' ignored")

            self.db.commit()
            self.db.refresh(user)
            logger.info(f"[SERVICE][USER] User profile updated for ID: {user_id}")
            return user

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][USER] SQLAlchemy Error (update_user_profile): {e}", exc_info=True)
            raise DatabaseException("Failed to update user profile")

    def create_user(self, client_id: UUID, email: EmailStr, password: str, full_name: Optional[str] = None, role: UserRole = UserRole.USER) -> User:
        """
        Membuat user baru dengan validasi email unik pada client_id tertentu.
        """
        logger.info(f"[SERVICE][USER] Creating new user: {email}, role: {role.value}")
        try:
            existing_user = self.db.query(User).filter(User.email == email, User.client_id == client_id).scalar_one_or_none()
            if existing_user:
                logger.warning(f"[SERVICE][USER] User with email {email} already exists")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email sudah terdaftar."
                )

            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            new_user = User(
                client_id=client_id,
                email=email,
                password=hashed_pw,
                full_name=full_name,
                role=role
            )

            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            logger.info(f"[SERVICE][USER] New user created with ID: {new_user.id}")
            return new_user

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][USER] SQLAlchemy Error (create_user): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Terjadi kesalahan saat menyimpan pengguna baru ke database."
            )

def get_user_service(db: Session = Depends(config_db)) -> UserService:
    return UserService(db)
