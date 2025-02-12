from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.upload_file_model import FileModel

router = APIRouter()

# Endpoint Get All Files
@router.get("/files", response_model=list[dict])
def get_all_files(db: Session = Depends(config_db)):
    files = db.query(FileModel).all()
    return [{"uuid_file": file.uuid_file, "filename": file.filename} for file in files]
