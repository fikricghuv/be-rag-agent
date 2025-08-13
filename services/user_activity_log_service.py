import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, func, cast, String
from fastapi import Depends
from typing import List, Optional
from uuid import UUID
import json
from core.config_db import config_db
from database.models.user_activity_log_model import UserActivityLog
from exceptions.custom_exceptions import DatabaseException

logger = logging.getLogger(__name__)

class UserActivityLogService:
    """
    Service class untuk mengelola operasi log aktivitas pengguna.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_all_logs(self, offset: int, limit: int, client_id: UUID, search: Optional[str] = None) -> List[UserActivityLog]:
        """
        Mengambil semua log aktivitas pengguna berdasarkan client_id dengan pagination dan pencarian opsional.
        """
        try:
            logger.info(f"[SERVICE][ACTIVITY_LOG] Fetching logs (offset={offset}, limit={limit}, search={search}, client_id={client_id})")

            query = self.db.query(UserActivityLog).filter(UserActivityLog.client_id == client_id)

            if search:
                pattern = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(cast(UserActivityLog.endpoint, String)).like(pattern),
                        func.lower(cast(UserActivityLog.method, String)).like(pattern),
                        cast(UserActivityLog.user_id, String).ilike(pattern)
                    )
                )

            logs = (
                query.order_by(UserActivityLog.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            logger.info(f"[SERVICE][ACTIVITY_LOG] Fetched {len(logs)} logs.")
            return logs

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][ACTIVITY_LOG] SQLAlchemy Error: {e}", exc_info=True)
            raise DatabaseException("Failed to fetch user activity logs from the database.", "GET_ALL_USER_ACTIVITY")

    def get_logs_by_user_id(self, user_id: UUID, client_id: UUID, offset: int = 0, limit: int = 10) -> List[UserActivityLog]:
        """
        Mengambil log aktivitas berdasarkan user_id dan client_id,
        hanya mengambil metode POST, PUT, DELETE dan mengecualikan endpoint tertentu.
        """
        try:
            logger.info(f"[SERVICE][ACTIVITY_LOG] Fetching logs for user {user_id} under client {client_id}")

            excluded_endpoints = [
                '/auth/refresh',
                '/auth/login',
                '/fcm-token',
                '/notification/token',
                '/auth/generate_user_id'
            ]
            
            logs = (
                self.db.query(UserActivityLog)
                .filter(
                    UserActivityLog.client_id == client_id,
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.method.in_(["POST", "DELETE", "PUT"]),
                    ~UserActivityLog.endpoint.in_(excluded_endpoints)
                )
                .order_by(UserActivityLog.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            for log in logs:
                if isinstance(log.request_data, str):
                    try:
                        log.request_data = json.loads(log.request_data)
                    except json.JSONDecodeError:
                        log.request_data = None

                if isinstance(log.response_data, str):
                    try:
                        log.response_data = json.loads(log.response_data)
                    except json.JSONDecodeError:
                        log.response_data = None

            logger.info(f"[SERVICE][ACTIVITY_LOG] Retrieved {len(logs)} logs for user {user_id}.")
            return logs

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][ACTIVITY_LOG] Failed to fetch logs for user {user_id}: {e}", exc_info=True)
            raise DatabaseException("Failed to fetch user activity logs from the database.", "GET_USER_ACTIVITY_BY_ID")

def get_user_activity_log_service(db: Session = Depends(config_db)) -> UserActivityLogService:
    return UserActivityLogService(db)
