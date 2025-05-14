# app/services/knowledge_base_service.py
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from fastapi import HTTPException, status, Depends # Import FastAPI components needed
from database.models.knowledge_base_config_model import KnowledgeBaseConfigModel # Asumsi model ini ada
# Asumsi schema KnowledgeBaseConfig diimpor dari schemas.knowledge_base_config_schema
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig
# Asumsi config_db diimpor dari core.config_db
from core.config_db import config_db
# Asumsi utility get_knowledge_base_config dan agent tool knowledge_base ada dan diimpor
# CATATAN: Logika pemanggilan knowledge_base() mungkin perlu dipindahkan atau disesuaikan
# tergantung kapan knowledge base sebenarnya dibuat/dimuat.
from utils.get_knowledge_base_param import get_knowledge_base_config # Utility untuk mengambil config saat ini
from agents.tools.knowledge_base_tools import knowledge_base # Agent tool

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """
    Service class untuk mengelola konfigurasi knowledge base di database.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi KnowledgeBaseService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    # Menghapus _get_db_connection karena sudah menggunakan SQLAlchemy Session

    def get_knowledge_base_config_from_db(self) -> KnowledgeBaseConfigModel:
        """
        Mengambil konfigurasi knowledge base dari database (asumsi ID = 1).

        Returns:
            KnowledgeBaseConfigModel: Objek model konfigurasi.
        Raises:
            HTTPException: 404 Not Found jika konfigurasi tidak ditemukan.
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Fetching knowledge base config from database.")
            # Mengambil konfigurasi dengan ID 1 (asumsi hanya ada satu baris konfigurasi)
            config_model = self.db.query(KnowledgeBaseConfigModel).filter(KnowledgeBaseConfigModel.id == 1).first()

            if not config_model:
                logger.warning("Knowledge base config with ID 1 not found.")
                # Melempar HTTPException 404 jika konfigurasi tidak ditemukan
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base config not found")

            logger.info("Successfully fetched knowledge base config.")
            return config_model
        except HTTPException:
             # Re-raise HTTPException (misalnya 404)
             raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching knowledge base config: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching knowledge base config from database")
        except Exception as e:
            logger.error(f"Unexpected Error fetching knowledge base config: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


    def update_knowledge_base_config(self, new_config: KnowledgeBaseConfig) -> KnowledgeBaseConfigModel:
        """
        Memperbarui konfigurasi knowledge base di database (asumsi ID = 1).

        Args:
            new_config: Data konfigurasi baru (Pydantic model KnowledgeBaseConfig).

        Returns:
            KnowledgeBaseConfigModel: Objek model konfigurasi yang telah diperbarui.
        Raises:
            HTTPException: 400 Bad Request jika parameter tidak valid.
            HTTPException: 404 Not Found jika konfigurasi tidak ditemukan.
            HTTPException: 500 Internal Server Error jika terjadi kesalahan database saat memperbarui.
            Exception: Untuk error tak terduga lainnya.
        """
        # Validasi parameter (tetap di service layer)
        if new_config.chunk_size < 100 or new_config.overlap < 0 or new_config.num_documents < 1: # Menyesuaikan validasi
            logger.warning(f"Invalid parameters for knowledge base config update: {new_config}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parameters for knowledge base config: chunk_size >= 100, overlap >= 0, num_documents >= 1")

        try:
            logger.info(f"Attempting to update knowledge base config with: {new_config}")
            # Mengambil konfigurasi yang ada
            config_model = self.db.query(KnowledgeBaseConfigModel).filter(KnowledgeBaseConfigModel.id == 1).first()

            if not config_model:
                logger.warning("Knowledge base config with ID 1 not found for update.")
                # Melempar HTTPException 404 jika konfigurasi tidak ditemukan
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base config not found for update")

            # Memperbarui nilai
            config_model.chunk_size = new_config.chunk_size
            config_model.overlap = new_config.overlap
            config_model.num_documents = new_config.num_documents

            # Commit perubahan
            self.db.commit()
            self.db.refresh(config_model) # Refresh untuk mendapatkan data terbaru

            logger.info("Knowledge base config updated successfully.")
            return config_model

        except HTTPException:
             # Re-raise HTTPException (misalnya 404, 400)
             self.db.rollback() # Tetap rollback jika ada HTTPException setelah query/validasi
             raise
        except SQLAlchemyError as e:
            self.db.rollback() # Rollback transaksi jika ada error database
            logger.error(f"SQLAlchemy Error updating knowledge base config: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating knowledge base config in database")
        except Exception as e:
            self.db.rollback() # Rollback transaksi jika ada error
            logger.error(f"Unexpected Error updating knowledge base config: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

def get_knowledge_base_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance KnowledgeBaseService dengan sesi database.
    """
    return KnowledgeBaseService(db)
