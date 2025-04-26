from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config.config_db import config_db
from models.chat_history_by_name_schema import ChatHistoryByNameResponse
from controllers.chat_history_controller import fetch_chat_history_by_user

router = APIRouter()

@router.get("/get-chat-from-history-chat/{user_name}", response_model=List[ChatHistoryByNameResponse])
def get_chat_history(user_name: str, db: Session = Depends(config_db)):
    try:
        return fetch_chat_history_by_user(user_name, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
