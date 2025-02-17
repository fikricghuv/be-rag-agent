from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from config.config_db import config_db
from models.chat_history_model import ChatHistory
from models.chat_history_schema import ChatHistoryResponse

router = APIRouter()

@router.get("/chat-history", response_model=list[ChatHistoryResponse])
def get_chat_history(
    db: Session = Depends(config_db),
    ):
    try:

        chat_history_data = db.execute(select(ChatHistory).order_by(desc(ChatHistory.start_time))).scalars().all()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
    return chat_history_data