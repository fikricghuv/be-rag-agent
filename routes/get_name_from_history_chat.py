from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.chat_history_controller import fetch_unique_names_from_history
from models.unique_name_response_schema import UniqueNameResponse

router = APIRouter()

@router.get("/get-name-from-history-chat", response_model=list[UniqueNameResponse])
def get_unique_names(db: Session = Depends(config_db)):
    try:
        return fetch_unique_names_from_history(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
