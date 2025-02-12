from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from sqlalchemy import text
from config.config_db import config_db 
from models.unique_name_response_schema import UniqueNameResponse

router = APIRouter()

@router.get("/get-name-from-history-chat", response_model=list[UniqueNameResponse])
def get_unique_names(db: Session = Depends(config_db)):
    try:
        # Query untuk mendapatkan nama unik dan last_update terbaru, diurutkan berdasarkan last_update
        query = (
            select(
                text("name"),
                func.max(text("start_time")).label("last_update")
            )
            .select_from(text("ai.chat_history"))
            .group_by(text("name"))  # Hanya GROUP BY name
            .order_by(func.max(text("start_time")).desc())  # Mengurutkan berdasarkan last_update
        )
        result = db.execute(query)
        unique_names = [{"name": row[0], "last_update": row[1]} for row in result.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
    return unique_names

