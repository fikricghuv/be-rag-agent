from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, select, text
from config.config_db import config_db

router = APIRouter()

@router.get("/get-total-conversations", response_model=dict)
def get_total_conversations(db: Session = Depends(config_db)):
    try:
        # Query untuk menghitung total jumlah percakapan
        query = select(func.count(text("*"))).select_from(text("ai.chat_history"))
        result = db.execute(query).scalar()  # Mengambil nilai scalar dari hasil query
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
   
    return {"total_conversations": result}