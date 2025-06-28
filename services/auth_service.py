# app/services/auth_service.py
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from database.models.user_ids_model import UserIds, UserRole  # Import model dan enum
from core.config_db import config_db
from schemas.user_id_schema import GenerateUserIdRequest, UserIdResponse
from core.settings import ALGORITHM, SECRET_KEY_REFRESH_ADMIN
from datetime import datetime, timedelta
from jose import jwt
from database.models.user_model import User
from utils.security_utils import hash_password
from schemas.user_schema import CreateUserRequest, UserResponse

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def generate_user_id(self, role: GenerateUserIdRequest) -> UserIdResponse:
        """
        Menghasilkan dan menyimpan user_id berdasarkan peran.
        """
        user_id = str(uuid.uuid4())
        db_user_id = UserIds(user_id=user_id, role=role)
        self.db.add(db_user_id)
        self.db.commit()
        self.db.refresh(db_user_id)
        
        # Mengembalikan instance UserIdResponse
        return UserIdResponse(
            user_id=db_user_id.user_id,
            role=db_user_id.role,
            created_at=db_user_id.created_at
        )

    def generate_access_token(self, user_id: str, expires_delta: timedelta = timedelta(minutes=30)) -> str:
        """
        Membuat JWT access token berdasarkan user_id.
        """
        to_encode = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + expires_delta
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY_REFRESH_ADMIN, algorithm=ALGORITHM)
        return encoded_jwt

    def login_user(self, email: str, password: str) -> str:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email")

        # if not verify_password(password, user.hashed_password):
        #     raise HTTPException(status_code=401, detail="Invalid password")

        token = self.generate_access_token(user_id=user.id)
        return token

    def create_user(self, request: CreateUserRequest) -> UserResponse:
        existing_user = self.db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            email=request.email,
            hashed_password=hash_password(request.password)
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
    
def get_auth_service(db: Session = Depends(config_db)):
    return AuthService(db)