from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.prompt_controller import fetch_all_prompts

router = APIRouter()

@router.get("/prompts", response_model=list[dict])
def get_prompts(db: Session = Depends(config_db)):
    try:
        return fetch_all_prompts(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prompts: {str(e)}")
