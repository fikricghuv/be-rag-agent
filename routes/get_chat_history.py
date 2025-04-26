from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.chat_history_schema import ChatHistoryResponse
from controllers.chat_history_controller import fetch_chat_history

router = APIRouter()

@router.get("/chat-history", response_model=list[ChatHistoryResponse])
def get_chat_history(db: Session = Depends(config_db)):
    try:
        return fetch_chat_history(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
