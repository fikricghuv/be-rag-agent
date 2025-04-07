from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from config.config_db import config_db  # Fungsi untuk mendapatkan session database
from models.chat_history_model import ChatHistory
from models.chat_history_schema import ChatHistoryResponse
from models.chat_history_by_name_schema import ChatHistoryByNameResponse

router = APIRouter()

# Endpoint untuk mendapatkan chat history berdasarkan pengguna
@router.get("/get-chat-from-history-chat/{user_name}", response_model=List[ChatHistoryByNameResponse])
def get_chat_history(
    user_name: str,
    db: Session = Depends(config_db)
):
    try:
        # Query untuk mengambil chat history berdasarkan name
        query = select(ChatHistory).where(ChatHistory.name == user_name)
        result = db.execute(query).scalars().all()
        print("result", result)
        
        # Tidak perlu raise error kalau kosong, cukup return []
        if not result:
            print(f"No chat history found for user '{user_name}'")
            return []  # <== penting, biar tidak 500
        
        return result
    except Exception as e:
        print("error get chat from history chat", e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

