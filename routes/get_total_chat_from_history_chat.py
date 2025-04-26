from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.chat_stats_controller import get_total_conversations_count

router = APIRouter()

@router.get("/get-total-conversations", response_model=dict)
def get_total_conversations(db: Session = Depends(config_db)):
    try:
        total = get_total_conversations_count(db)
        return {"total_conversations": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
