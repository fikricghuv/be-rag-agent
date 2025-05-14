# app/services/file_service.py
import logging # Import logging
import uuid # Import uuid for UUID type hinting
from fastapi import HTTPException, status, Depends, UploadFile # Import FastAPI components needed
from sqlalchemy.orm import Session
from sqlalchemy import select, func # Import select and func
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError for specific error handling
# Asumsi model FileModel diimpor dari database.models.upload_file_model
from database.models.upload_file_model import FileModel
# Asumsi config_db diimpor dari core.config_db
from core.config_db import config_db
from typing import List, Dict, Any # Diperlukan untuk type hinting
# Asumsi utility dan agent tool diimpor dengan benar
from utils.save_file_from_postgres import save_pdfs_locally
from agents.tools.knowledge_base_tools import knowledge_base
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig
from utils.get_knowledge_base_param import get_knowledge_base_config

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
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

    # --- Metode untuk Mengambil Semua File ---
    # Mengembalikan List[FileModel] agar Pydantic ORM mode di route bisa mengonversi ke List[FileInfo]
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
            # Menggunakan self.db untuk query
            files = self.db.query(FileModel).all()
            logger.info(f"Successfully fetched {len(files)} files.")
            # Mengembalikan objek SQLAlchemy secara langsung
            return files
        except SQLAlchemyError as e:
            # Log error detail di sini, tapi biarkan exception propagate
            logger.error(f"SQLAlchemy Error fetching all files: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError

    # --- Metode untuk Menyimpan File (Upload) ---
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

            # Membaca konten file
            file_content = await file.read()

            # Membuat UUID baru
            file_uuid = uuid.uuid4()

            # Membuat instance model database
            new_file = FileModel(
                uuid_file=file_uuid, # Menggunakan objek UUID langsung
                filename=file.filename,
                content_type=file.content_type,
                content=file_content,
                size=file.size,
                # uploaded_at akan menggunakan server_default=func.now()
            )

            # Menambahkan dan menyimpan ke database
            self.db.add(new_file)
            self.db.commit()
            self.db.refresh(new_file) # Refresh untuk mendapatkan nilai default seperti uploaded_at

            logger.info(f"File saved successfully with UUID: {file_uuid}")
            return new_file # Mengembalikan objek model SQLAlchemy

        except SQLAlchemyError as e:
            # Tangani error database secara spesifik
            self.db.rollback() # Rollback transaksi jika ada error database
            logger.error(f"SQLAlchemy Error saving file {file.filename}: {e}", exc_info=True)
            # Melempar HTTPException 500 untuk error database
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error saving file to database")
        except Exception as e:
            # Tangani error tak terduga lainnya
            self.db.rollback() # Rollback transaksi jika ada error
            logger.error(f"Unexpected Error saving file {file.filename}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

    # --- Metode untuk Menghapus File ---
    # Mengubah nama metode menjadi delete_file_from_db sesuai route
    # Mengubah tipe parameter uuid_file menjadi uuid.UUID sesuai route
    # Mengembalikan Dict[str, str] sesuai respons sukses
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
            # Mencari file dengan UUID yang diberikan
            # Menggunakan .filter(FileModel.uuid_file == uuid_file)
            # Asumsi kolom DB uuid_file adalah UUID type atau SQLAlchemy menangani perbandingan UUID/string
            file_to_delete = self.db.query(FileModel).filter(FileModel.uuid_file == uuid_file).first()

            if not file_to_delete:
                logger.warning(f"File with UUID {uuid_file} not found.")
                # Melempar HTTPException 404 jika file tidak ditemukan
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            # Hapus file dari database dan commit perubahan
            self.db.delete(file_to_delete)
            self.db.commit()
            logger.info(f"File with UUID {uuid_file} deleted successfully.")
            # Mengembalikan pesan sukses sesuai respons model FileDeletedResponse
            return {"message": "File deleted successfully"}

        except HTTPException:
            # Jika exception adalah HTTPException (misalnya 404 dari "not found"), re-raise
            self.db.rollback() # Tetap rollback jika ada HTTPException setelah query
            raise
        except SQLAlchemyError as e:
            # Tangani error database secara spesifik
            self.db.rollback() # Rollback transaksi jika ada error database
            logger.error(f"SQLAlchemy Error deleting file with UUID {uuid_file}: {e}", exc_info=True)
            # Melempar HTTPException 500 untuk error database
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting file from database")
        except Exception as e:
            # Tangani error tak terduga lainnya
            self.db.rollback() # Rollback transaksi jika ada error
            logger.error(f"Unexpected Error deleting file with UUID {uuid_file}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

    # --- Metode untuk Pemrosesan Embedding ---
    # Menambahkan parameter file_uuid sesuai dengan route
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
            
            # --- Existing Logic (Processes all local PDFs) ---
            # This part might need refactoring to process file_data.content instead
            save_pdfs_locally() # Saves ALL PDFs from DB locally - potentially not just the requested one
            logger.info("PDFs saved locally (service).")

            db_config = get_knowledge_base_config()
            kb_config = KnowledgeBaseConfig(**db_config)
            logger.info(f"Knowledge Base Config: {kb_config}")

            kb = knowledge_base(
                chunk_size=kb_config.chunk_size,
                overlap=kb_config.overlap,
                num_documents=kb_config.num_documents,
            )

            kb.load(recreate=True, upsert=True) # Processes the locally saved PDFs
            logger.info("Knowledge base loaded (service).")
            # --- End Existing Logic ---


            # Prepare result based on expected EmbeddingProcessResponse schema
            processed_result = {
                "message": "Embedding processing initiated (check logs for details).", # More accurate message
                "status": "processing_logic_executed", # Indicates the logic ran
            }

            logger.info(f"Embedding processing logic executed.")
            return processed_result

        except HTTPException:
            # If exception is HTTPException (e.g., 404 from "not found"), re-raise
            raise
        except Exception as e:
            # Tangani error selama pemrosesan embedding
            logger.error(f"Error processing embedding.: {e}", exc_info=True)
            # Melempar HTTPException 500 untuk error pemrosesan
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing embedding: {str(e)}")


# Dependency function untuk menyediakan instance FileService
# Pastikan config_db diimpor dengan benar di bagian atas file
def get_file_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance FileService dengan sesi database.
    """
    return FileService(db)
