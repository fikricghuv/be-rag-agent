# app/api/endpoints/upload_endpoint.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from core.config_db import config_db
from services.upload_service import UploadService
router = APIRouter()

def get_upload_service(db: Session = Depends(config_db)):
    return UploadService(db)

# Endpoint Upload File
@router.post("/upload")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service)
):
    try:
        # Simpan file ke database melalui service
        file_uuid = await upload_service.save_file(file)

        return {"message": "File uploaded successfully", "uuid_file": file_uuid, "filename": file.filename}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")