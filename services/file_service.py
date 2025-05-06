# app/services/file_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database.models.upload_file_model import FileModel

class FileService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_all_files(self):
        """Mengambil seluruh file yang telah diunggah dari database."""
        files = self.db.query(FileModel).all()
        return [{"uuid_file": file.uuid_file, "filename": file.filename} for file in files]

    def delete_file(self, uuid_file: str):
        # Mencari file dengan UUID yang diberikan
        file_to_delete = self.db.query(FileModel).filter(FileModel.uuid_file == uuid_file).first()

        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            # Hapus file dari database dan commit perubahan
            self.db.delete(file_to_delete)
            self.db.commit()
            return {"message": "File deleted successfully"}
        except Exception as e:
            # Tangani error jika terjadi masalah saat penghapusan
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")