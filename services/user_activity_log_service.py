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

    def get_all_logs(self, offset: int, limit: int, search: Optional[str] = None) -> List[UserActivityLog]:
        try:
            logger.info(f"[SERVICE][ACTIVITY_LOG] Fetching logs (offset={offset}, limit={limit}, search={search})")

            query = self.db.query(UserActivityLog)

            if search:
                pattern = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(cast(UserActivityLog.endpoint, String)).like(pattern),
                        func.lower(cast(UserActivityLog.method, String)).like(pattern),
                        func.cast(UserActivityLog.user_id, String).ilike(pattern)
                    )
                )

            logs = query.order_by(UserActivityLog.timestamp.desc())\
                        .offset(offset)\
                        .limit(limit)\
                        .all()

            logger.info(f"[SERVICE][ACTIVITY_LOG] Fetched {len(logs)} logs.")
            return logs

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][ACTIVITY_LOG] SQLAlchemy Error: {e}", exc_info=True)
            raise DatabaseException("Failed to fetch user activity logs from the database")
        
    def get_logs_by_user_id(self, user_id: UUID, offset: int = 0, limit: int = 10) -> List[UserActivityLog]:
        try:
            logger.info(f"[SERVICE][ACTIVITY_LOG] Fetching logs for user {user_id}")
            logs = (
                self.db.query(UserActivityLog)
                .filter(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.method.in_(["POST", "PUT", "PATCH", "DELETE"])
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
                    except Exception:
                        log.request_data = None

                if isinstance(log.response_data, str):
                    try:
                        log.response_data = json.loads(log.response_data)
                    except Exception:
                        log.response_data = None

            return logs
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][ACTIVITY_LOG] Failed to fetch logs for user {user_id}", exc_info=True)
            raise DatabaseException("Failed to fetch user activity logs")

def get_user_activity_log_service(db: Session = Depends(config_db)) -> UserActivityLogService:
    return UserActivityLogService(db)
