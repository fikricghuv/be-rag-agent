from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.upload_file_model import FileModel

router = APIRouter()

# Endpoint Upload File
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(config_db)):
    try:
        file_content = await file.read()
        new_file = FileModel(filename=file.filename, content=file_content)
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        return {"message": "File uploaded successfully", "file_id": new_file.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))