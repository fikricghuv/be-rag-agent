# app/services/auth_service.py
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from database.models.user_ids_model import UserIds, UserRole  # Import model dan enum
from core.config_db import config_db
from schemas.user_id_schema import GenerateUserIdRequest, UserIdResponse

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
    
def get_auth_service(db: Session = Depends(config_db)):
    return AuthService(db)