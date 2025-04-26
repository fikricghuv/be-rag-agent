from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.files_controller import delete_file_from_db

router = APIRouter()

@router.delete("/files/{uuid_file}")
async def delete_file(uuid_file: str, db: Session = Depends(config_db)):
    try:
        # Memanggil service untuk menghapus file
        return delete_file_from_db(uuid_file, db)
    except HTTPException as e:
        # Jika ada error, tangani dengan memberikan respons HTTPException
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
