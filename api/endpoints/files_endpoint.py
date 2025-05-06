from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.config_db import config_db
from services.file_service import FileService
from typing import List
from pydantic import BaseModel

router = APIRouter()

class FileInfo(BaseModel):
    uuid_file: str
    filename: str

def get_file_service(db: Session = Depends(config_db)):
    return FileService(db)

@router.get("/files", response_model=List[FileInfo])
def get_all_files_endpoint(file_service: FileService = Depends(get_file_service)):
    return file_service.fetch_all_files()

@router.delete("/files/{uuid_file}")
async def delete_file_endpoint(uuid_file: str, file_service: FileService = Depends(get_file_service)):
    return file_service.delete_file(uuid_file)