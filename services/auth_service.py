# app/services/auth_service.py
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from database.models.chat_ids_model import ChatIds, UserRole  # Import model dan enum
from core.config_db import config_db

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def generate_chat_id(self, role: str) -> str:
        """
        Menghasilkan dan menyimpan chat_id berdasarkan peran.
        """
        if role.lower() == 'user':
            db_role = UserRole.user
        elif role.lower() == 'admin':
            db_role = UserRole.admin
        else:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'.")

        chat_id = str(uuid.uuid4())
        db_chat_id = ChatIds(chat_id=chat_id, role=db_role)
        self.db.add(db_chat_id)
        self.db.commit()
        self.db.refresh(db_chat_id)
        return chat_id

    def get_chat_id_data(self, chat_id: str) -> dict | None:
        """
        Mendapatkan data chat berdasarkan chat_id.
        """
        chat_data = self.db.query(ChatIds).filter(ChatIds.chat_id == chat_id).first()
        if chat_data:
            return {
                "chat_id": chat_data.chat_id,
                "role": chat_data.role,
                "created_at": chat_data.created_at,
            }
        return None
    
def get_auth_service(db: Session = Depends(config_db)):
    return AuthService(db)