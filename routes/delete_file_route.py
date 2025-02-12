from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.upload_file_model import FileModel

router = APIRouter()

@router.delete("/files/{uuid_file}")
async def delete_file(uuid_file: str, db: Session = Depends(config_db)):
    try:
        # Query file berdasarkan ID
        file_to_delete = db.query(FileModel).filter(FileModel.uuid_file == uuid_file).first()
        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Hapus file dari database
        db.delete(file_to_delete)
        db.commit()
        return {"message": "File deleted successfully"}
    except Exception as e:
        print("error", e)
        raise HTTPException(status_code=500, detail=str(e))