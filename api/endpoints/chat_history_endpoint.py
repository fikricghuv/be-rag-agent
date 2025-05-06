from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.config_db import config_db
from schemas.chat_history_by_name_schema import ChatHistoryByNameResponse
from services.chat_history_service import ChatHistoryService
from schemas.chat_history_schema import ChatHistoryResponse
from models.unique_name_response_model import UniqueNameResponse
from models.chat_history_model import TotalConversationsResponse

router = APIRouter()

def get_chat_history_service(db: Session = Depends(config_db)):
    return ChatHistoryService(db)

@router.get("/chat-history", response_model=List[ChatHistoryResponse])
def get_chat_history_endpoint(chat_history_service: ChatHistoryService = Depends(get_chat_history_service)):
    try:
        return chat_history_service.fetch_chat_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
@router.get("/get-name-from-history-chat", response_model=List[UniqueNameResponse])
def get_unique_names_endpoint(chat_history_service: ChatHistoryService = Depends(get_chat_history_service)):
    try:
        return chat_history_service.fetch_unique_names_from_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@router.get("/get-chat-from-history-chat/{user_name}", response_model=List[ChatHistoryByNameResponse])
def get_chat_history_endpoint(
    user_name: str,
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    try:
        return chat_history_service.fetch_chat_history_by_user(user_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
@router.get("/get-total-conversations", response_model=TotalConversationsResponse)
def get_total_conversations_endpoint(chat_history_service: ChatHistoryService = Depends(get_chat_history_service)):
    try:
        total = chat_history_service.get_total_conversations()
        return {"total_conversations": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")