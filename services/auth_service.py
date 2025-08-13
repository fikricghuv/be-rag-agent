import uuid
import logging
from fastapi import Depends
from jose import jwt
from sqlalchemy.orm import Session
from core.config_db import config_db
from core.settings import ALGORITHM, SECRET_KEY_ADMIN
from database.models.user_ids_model import UserIds
from database.models.user_model import User
from schemas.user_id_schema import GenerateUserIdRequest, UserIdResponse
from schemas.user_schema import CreateUserRequest, UserResponse
from utils.security_utils import hash_password, verify_password
from exceptions.custom_exceptions import ServiceException, DatabaseException
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
from uuid import UUID

WIB = ZoneInfo("Asia/Jakarta")

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def generate_user_id(self, role: GenerateUserIdRequest, client_id) -> UserIdResponse:
        try:
            logger.info(f"[SERVICE][AUTH] Generating user ID for role={role}")
            
            user_id = str(uuid.uuid4())
            db_user_id = UserIds(user_id=user_id, role=role, client_id=client_id)
            self.db.add(db_user_id)
            self.db.commit()
            self.db.refresh(db_user_id)

            return UserIdResponse(
                user_id=db_user_id.user_id,
                role=db_user_id.role,
                created_at=db_user_id.created_at
            )
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Failed to generate user ID: {e}", exc_info=True)
            raise DatabaseException("Failed to generate user ID", "FAILED_TO_GENERATE_USER_ID")

    def generate_access_token(self, user_id: str) -> dict:
        try:
            logger.info(f"[SERVICE][AUTH] Generating access token for user_id={user_id}")
            
            now_wib = datetime.now(WIB)
            expire_at_wib = datetime.combine(
                now_wib.date(),
                time(23, 58)
            ).replace(tzinfo=WIB)

            if now_wib >= expire_at_wib:
                expire_at_wib += timedelta(days=1)

            expire_time_utc = expire_at_wib.astimezone(timezone.utc)
            exp_timestamp = int(expire_time_utc.timestamp())

            to_encode = {
                "sub": str(user_id),
                "exp": exp_timestamp
            }
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ADMIN, algorithm=ALGORITHM)
            
            exp_utc = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            exp_wib = exp_utc.astimezone(WIB)
            exp_formated = exp_wib.strftime("%Y-%m-%d %H:%M:%S %Z")
            
            logger.info(f"[SERVICE][AUTH] exp access token at: {exp_formated}")

            return {
                "access_token": encoded_jwt,
                "expires_at": exp_timestamp
            }
            
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Failed to generate access token: {e}", exc_info=True)
            raise ServiceException("Failed to generate access token", 401, "ACCESS_TOKEN_ERROR")

    def generate_refresh_token(self, user_id: str, expires_delta: timedelta = timedelta(days=30)) -> str:
        try:
            logger.info(f"[SERVICE][AUTH] Generating refresh token for user_id={user_id}")
            to_encode = {
                "sub": str(user_id),
                "exp": datetime.utcnow() + expires_delta
            }
            return jwt.encode(to_encode, SECRET_KEY_ADMIN, algorithm=ALGORITHM)
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Failed to generate refresh token: {e}", exc_info=True)
            raise ServiceException("Failed to generate refresh token", 401, "REFRESH_TOKEN_ERROR")

    def login_user(self, email: str, password: str) -> dict:
        try:
            logger.info(f"[SERVICE][AUTH] Attempt login for email={email}")
            user = self.db.query(User).filter(User.email == email).first()

            if not user:
                logger.warning(f"[SERVICE][AUTH] Email not found: {email}")
                raise ServiceException("INVALID_EMAIL_OR_PASSWORD", 401, "Invalid email or password")

            if not verify_password(password, user.password):
                logger.warning(f"[SERVICE][AUTH] Invalid password for email: {email}")
                raise ServiceException(code="INVALID_EMAIL_OR_PASSWORD", status_code=401, message="Invalid email or password")

            access_data = self.generate_access_token(user.id)
            refresh_token = self.generate_refresh_token(user.id)

            return {
                "access_token": access_data["access_token"],
                "expires_at": access_data["expires_at"],
                "refresh_token": refresh_token
            }
        except ServiceException as e:
            raise e
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Login failed: {e}", exc_info=True)
            raise ServiceException(
                message="Unexpected error during login",
                status_code=500,
                code="LOGIN_ERROR"
            )

def get_auth_service(db: Session = Depends(config_db)):
    return AuthService(db)
