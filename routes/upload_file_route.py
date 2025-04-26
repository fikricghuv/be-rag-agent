from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.upload_controller import save_file_to_db


router = APIRouter()

# Endpoint Upload File
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(config_db)):
    try:
        # Simpan file ke database melalui controller
        file_uuid = await save_file_to_db(file, db)
        
        return {"message": "File uploaded successfully", "uuid_file": file_uuid, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")