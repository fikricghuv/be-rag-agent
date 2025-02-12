from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.upload_file_model import FileModel
import uuid

router = APIRouter()

# Endpoint Upload File
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(config_db)):
    try:
        file_uuid = str(uuid.uuid4())
        file_content = await file.read()
        content_type = file.content_type
        new_file = FileModel(
            uuid_file= file_uuid,
            filename= file.filename,
            content_type= content_type,
            content= file_content,
            size= file.size,
            uploaded_at= func.now(),
        )
        
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        return {"message": "File uploaded successfully", "uuid_file": file_uuid, "filename": file.filename}
    except Exception as e:
        print("error: ", e)
        raise HTTPException(status_code=500, detail=str(e))