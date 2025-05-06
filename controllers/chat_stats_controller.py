from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from database.models.chat_history_model import ChatHistory  # Pastikan model ini sudah sesuai

def get_total_conversations_count(db: Session) -> int:
    try:
        total = db.query(func.count()).select_from(ChatHistory).scalar()
        return total
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
