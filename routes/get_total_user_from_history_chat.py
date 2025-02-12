from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from sqlalchemy import text
from config.config_db import config_db 

router = APIRouter()

@router.get("/get-total-user-from-history-chat", response_model=dict)
def get_total_unique_names(db: Session = Depends(config_db)):
    try:
        # Query untuk menghitung total nama unik
        query = (
            select(func.count(func.distinct(text("name"))).label("total_user"))
            .select_from(text("ai.chat_history"))
        )
        result = db.execute(query)
        total_user = result.scalar()  # Mendapatkan nilai tunggal dari hasil query
        
        return {"total_users": total_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

