import uuid
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
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

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def generate_user_id(self, role: GenerateUserIdRequest) -> UserIdResponse:
        try:
            logger.info(f"[SERVICE][AUTH] Generating user ID for role={role}")
            user_id = str(uuid.uuid4())
            db_user_id = UserIds(user_id=user_id, role=role)
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
            raise DatabaseException("FAILED_TO_GENERATE_USER_ID", "Failed to generate user ID")

    def generate_access_token(self, user_id: str, expires_delta: timedelta = timedelta(minutes=30)) -> dict:
        try:
            logger.info(f"[SERVICE][AUTH] Generating access token for user_id={user_id}")
            expire_time = datetime.utcnow() + expires_delta
            to_encode = {
                "sub": str(user_id),
                "exp": expire_time
            }
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ADMIN, algorithm=ALGORITHM)

            return {
                "access_token": encoded_jwt,
                "expires_at": int(expire_time.timestamp())
            }
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Failed to generate access token: {e}", exc_info=True)
            raise ServiceException("ACCESS_TOKEN_ERROR", "Failed to generate access token")

    def generate_refresh_token(self, user_id: str, expires_delta: timedelta = timedelta(days=7)) -> str:
        try:
            logger.info(f"[SERVICE][AUTH] Generating refresh token for user_id={user_id}")
            to_encode = {
                "sub": str(user_id),
                "exp": datetime.utcnow() + expires_delta
            }
            return jwt.encode(to_encode, SECRET_KEY_ADMIN, algorithm=ALGORITHM)
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Failed to generate refresh token: {e}", exc_info=True)
            raise ServiceException("REFRESH_TOKEN_ERROR", "Failed to generate refresh token")

    def login_user(self, email: str, password: str) -> dict:
        try:
            logger.info(f"[SERVICE][AUTH] Attempt login for email={email}")
            user = self.db.query(User).filter(User.email == email).first()

            if not user:
                logger.warning(f"[SERVICE][AUTH] Email not found: {email}")
                raise ServiceException("INVALID_EMAIL", "Invalid email or password", status_code=401)

            if not verify_password(password, user.password):
                logger.warning(f"[SERVICE][AUTH] Invalid password for email: {email}")
                raise ServiceException("INVALID_PASSWORD", "Invalid email or password", status_code=401)

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
            raise ServiceException("LOGIN_ERROR", "Unexpected error during login")

    def create_user(self, request: CreateUserRequest) -> UserResponse:
        try:
            logger.info(f"[SERVICE][AUTH] Creating user with email={request.email}")
            existing_user = self.db.query(User).filter(User.email == request.email).first()
            if existing_user:
                raise ServiceException("EMAIL_EXISTS", "Email already registered", status_code=400)

            new_user = User(
                email=request.email,
                password=hash_password(request.password),
                full_name=request.full_name,
                role=request.role
            )
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            return UserResponse(
                id=new_user.id,
                email=new_user.email,
                full_name=new_user.full_name,
                is_active=new_user.is_active,
                created_at=new_user.created_at
            )
        except ServiceException as e:
            raise e
        except Exception as e:
            logger.error(f"[SERVICE][AUTH] Failed to create user: {e}", exc_info=True)
            raise DatabaseException("CREATE_USER_FAILED", "Failed to create user")
    
def get_auth_service(db: Session = Depends(config_db)):
    return AuthService(db)
