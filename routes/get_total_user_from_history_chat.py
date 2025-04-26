from fastapi import APIRouter, HTTPException, Depends
from controllers.chat_history_controller import get_total_unique_users
from config.config_db import config_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/get-total-user-from-history-chat", response_model=dict)
def get_total_unique_users_from_history(db: Session = Depends(config_db)):
    try:
        total_users = get_total_unique_users(db)
        return {"total_users": total_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
