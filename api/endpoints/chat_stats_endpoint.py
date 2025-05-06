# app/api/endpoints/chat_stats_endpoint.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.config_db import config_db
from services.chat_history_service import ChatHistoryService
from models.chat_stats_model import TotalUniqueUsersResponse

router = APIRouter()

def get_chat_history_service(db: Session = Depends(config_db)):
    return ChatHistoryService(db)

@router.get("/get-total-user-from-history-chat", response_model=TotalUniqueUsersResponse)
def get_total_unique_users_from_history_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    try:
        total_users = chat_history_service.get_total_unique_users()
        return {"total_users": total_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")