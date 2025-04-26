from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.files_controller import fetch_all_files

router = APIRouter()

@router.get("/files", response_model=list[dict])
def get_all_files(db: Session = Depends(config_db)):
    return fetch_all_files(db)
