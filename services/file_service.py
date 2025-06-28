# app/services/file_service.py
import logging
import uuid
from fastapi import HTTPException, status, Depends, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select, func 
from sqlalchemy.exc import SQLAlchemyError 
from database.models.upload_file_model import FileModel
from core.config_db import config_db
from typing import List, Dict, Any 
from utils.save_file_from_postgres_utils import save_pdfs_locally
from agents.tools.knowledge_base_tools import knowledge_base
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig
from utils.get_knowledge_base_param_utils import get_knowledge_base_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileService:
    """
    Service class untuk mengelola semua operasi terkait file di database,
    termasuk upload, mengambil data, dan menghapus, serta operasi terkait lainnya.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi FileService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    def fetch_all_files(self) -> List[FileModel]:
        """
        Mengambil seluruh file yang telah diunggah dari database.

        Returns:
            List of FileModel objects.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Fetching all files from database.")
            
            files = self.db.query(FileModel).all()
            logger.info(f"Successfully fetched {len(files)} files.")
            
            return files
        
        except SQLAlchemyError as e:
            
            logger.error(f"SQLAlchemy Error fetching all files: {e}", exc_info=True)
            raise e 

    async def save_file(self, file: UploadFile) -> FileModel:
        """
        Menyimpan file yang diunggah ke database.

        Args:
            file: Objek UploadFile dari FastAPI.

        Returns:
            FileModel: Objek FileModel yang baru dibuat.
        Raises:
            HTTPException: 500 Internal Server Error jika terjadi kesalahan database.
            Exception: Untuk error tak terduga lainnya.
        """
        try:
            logger.info(f"Attempting to save file: {file.filename}, size: {file.size}")

            file_content = await file.read()
            
            if file.content_type not in ["application/pdf", "text/plain"]:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            if file.size and file.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

            file_uuid = uuid.uuid4()

            new_file = FileModel(
                uuid_file=file_uuid, 
                filename=file.filename,
                content_type=file.content_type,
                content=file_content,
                size=file.size,
            )

            self.db.add(new_file)
            self.db.commit()
            self.db.refresh(new_file) 

            logger.info(f"File saved successfully with UUID: {file_uuid}")
            return new_file 

        except SQLAlchemyError as e:
            
            self.db.rollback() 
            logger.error(f"SQLAlchemy Error saving file {file.filename}: {e}", exc_info=True)
            
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error saving file to database")
        
        except Exception as e:
            self.db.rollback() 
            logger.error(f"Unexpected Error saving file {file.filename}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

    def delete_file_from_db(self, uuid_file: uuid.UUID) -> Dict[str, str]:
        """
        Menghapus file dari database berdasarkan UUID.

        Args:
            uuid_file: UUID dari file yang akan dihapus.

        Returns:
            dict: Pesan sukses jika file berhasil dihapus.
        Raises:
            HTTPException: 404 Not Found jika file tidak ditemukan.
            HTTPException: 500 Internal Server Error jika terjadi kesalahan database saat menghapus.
            Exception: Untuk error tak terduga lainnya.
        """
        try:
            logger.info(f"Attempting to delete file with UUID: {uuid_file}")
            
            file_to_delete = self.db.query(FileModel).filter(FileModel.uuid_file == uuid_file).first()

            if not file_to_delete:
                logger.warning(f"File with UUID {uuid_file} not found.")
                
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            self.db.delete(file_to_delete)
            self.db.commit()
            logger.info(f"File with UUID {uuid_file} deleted successfully.")
            
            return {"message": "File deleted successfully"}

        except HTTPException:
            
            self.db.rollback() 
            
            raise
        
        except SQLAlchemyError as e:
            
            self.db.rollback() 
            logger.error(f"SQLAlchemy Error deleting file with UUID {uuid_file}: {e}", exc_info=True)
            
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting file from database")
        
        except Exception as e:
            
            self.db.rollback()
            logger.error(f"Unexpected Error deleting file with UUID {uuid_file}: {e}", exc_info=True)
            
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

    async def process_embedding(self) -> Dict[str, Any]:
        """
        Memproses embedding dari file berdasarkan UUID.

        Args:
            file_uuid: UUID dari file yang akan diproses.

        Returns:
            Dict[str, Any]: Hasil pemrosesan embedding.
        Raises:
            HTTPException: 404 jika file tidak ditemukan.
            HTTPException: 500 untuk error selama pemrosesan embedding.
            Exception: Untuk error tak terduga lainnya.
        """
        try:
            
            save_pdfs_locally() 
            logger.info("PDFs saved locally (service).")

            db_config = get_knowledge_base_config()
            kb_config = KnowledgeBaseConfig(**db_config)
            logger.info(f"Knowledge Base Config: {kb_config}")

            kb = knowledge_base(
                chunk_size=kb_config.chunk_size,
                overlap=kb_config.overlap,
                num_documents=kb_config.num_documents,
            )

            kb.load(recreate=True, upsert=True)
            logger.info("Knowledge base loaded (service).")
            
            processed_result = {
                "message": "Embedding processing initiated (check logs for details).", # More accurate message
                "status": "processing_logic_executed", 
            }

            logger.info(f"Embedding processing logic executed.")
            return processed_result

        except HTTPException:
            raise
        
        except Exception as e:

            logger.error(f"Error processing embedding.: {e}", exc_info=True)
            
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing embedding: {str(e)}")

def get_file_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance FileService dengan sesi database.
    """
    return FileService(db)
