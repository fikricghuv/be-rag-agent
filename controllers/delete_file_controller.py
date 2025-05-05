from sqlalchemy.orm import Session
from models.upload_file_model import FileModel
from fastapi import HTTPException

def delete_file_from_db(uuid_file: str, db: Session):
    # Mencari file dengan UUID yang diberikan
    file_to_delete = db.query(FileModel).filter(FileModel.uuid_file == uuid_file).first()

    if not file_to_delete:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Hapus file dari database dan commit perubahan
        db.delete(file_to_delete)
        db.commit()
        return {"message": "File deleted successfully"}
    except Exception as e:
        # Tangani error jika terjadi masalah saat penghapusan
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
