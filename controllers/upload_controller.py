# controllers/upload_controller.py

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from database.models.upload_file_model import FileModel
import uuid
from sqlalchemy import func
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def save_file_to_db(file: UploadFile, db: Session) -> str:
    try:
        file_uuid = str(uuid.uuid4())
        file_content = await file.read()
        content_type = file.content_type
        new_file = FileModel(
            uuid_file=file_uuid,
            filename=file.filename,
            content_type=content_type,
            content=file_content,
            size=file.size,
            uploaded_at=func.now(),
        )

        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        return file_uuid
    except Exception as e:
        logger.error(f"Error saving file to DB: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file to database")
