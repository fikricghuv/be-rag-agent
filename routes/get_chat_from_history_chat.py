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
        
        # Jika tidak ada data, kembalikan error 404
        if not result:
            print(f"No chat history found for user '{user_name}'")
            raise HTTPException(status_code=404, detail=f"No chat history found for user '{user_name}'")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
