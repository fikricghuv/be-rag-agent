# app/services/prompt_service.py
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from fastapi import HTTPException, status, Depends # Import FastAPI components needed
# Asumsi model Prompt diimpor dari database.models.prompt_model
from database.models.prompt_model import Prompt
from schemas.prompt_schema import PromptUpdate
from typing import List
# Asumsi config_db diimpor dari core.config_db
from core.config_db import config_db


# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptService:
    """
    Service class untuk mengelola operasi terkait prompt di database.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi PromptService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    def fetch_all_prompts(self) -> List[Prompt]:
        """
        Mengambil seluruh prompt dari database.

        Returns:
            List of Prompt objects.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Fetching all prompts from database.")
            # Menggunakan self.db untuk query
            prompts = self.db.query(Prompt).all()
            logger.info(f"Successfully fetched {len(prompts)} prompts.")
            # Mengembalikan objek SQLAlchemy secara langsung
            return prompts
        except SQLAlchemyError as e:
            # Log error detail di sini, tapi biarkan exception propagate
            logger.error(f"SQLAlchemy Error fetching all prompts: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError
        
    def fetch_customer_service_prompt(self) -> List[Prompt]:
        """
        Mengambil prompt dengan name='Customer Service Agent' dari database.

        Returns:
            List of Prompt objects yang memiliki name 'Customer Service Agent'.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Fetching 'Customer Service Agent' prompt from database.")
            prompts = self.db.query(Prompt).filter(Prompt.name == "Customer Service Agent").all()
            logger.info(f"Successfully fetched {len(prompts)} prompts with name 'Customer Service Agent'.")
            return prompts
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching 'Customer Service Agent' prompt: {e}", exc_info=True)
            raise e



    def update_prompt(self, name: str, prompt_update: PromptUpdate) -> Prompt:
        """
        Memperbarui prompt berdasarkan nama.

        Args:
            name: Nama prompt yang akan diperbarui.
            prompt_update: Data pembaruan prompt (Pydantic model PromptUpdate).

        Returns:
            Prompt: Objek Prompt yang telah diperbarui.
        Raises:
            HTTPException: 404 Not Found jika prompt tidak ditemukan.
            HTTPException: 500 Internal Server Error jika terjadi kesalahan database saat memperbarui.
            Exception: Untuk error tak terduga lainnya.
        """
        try:
            logger.info(f"Attempting to update prompt with name: {name}")
            # Mencari prompt berdasarkan nama
            prompt = self.db.query(Prompt).filter(Prompt.name == name).first()

            if not prompt:
                logger.warning(f"Prompt with name {name} not found for update.")
                # Melempar HTTPException 404 jika prompt tidak ditemukan
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

            # Memperbarui konten prompt
            prompt.content = prompt_update.content

            # Commit perubahan ke database
            self.db.commit()
            self.db.refresh(prompt) # Refresh untuk mendapatkan data terbaru

            logger.info(f"Prompt with name {name} updated successfully.")
            # Mengembalikan objek Prompt yang telah diperbarui
            return prompt

        except HTTPException:
            # Jika exception adalah HTTPException (misalnya 404 dari "not found"), re-raise
            self.db.rollback() # Tetap rollback jika ada HTTPException setelah query
            raise
        except SQLAlchemyError as e:
            # Tangani error database secara spesifik
            self.db.rollback() # Rollback transaksi jika ada error database
            logger.error(f"SQLAlchemy Error updating prompt with name {name}: {e}", exc_info=True)
            # Melempar HTTPException 500 untuk error database
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating prompt in database")
        except Exception as e:
            # Tangani error tak terduga lainnya
            self.db.rollback() # Rollback transaksi jika ada error
            logger.error(f"Unexpected Error updating prompt with name {name}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


# Dependency function untuk menyediakan instance PromptService
def get_prompt_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance PromptService dengan sesi database.
    """
    return PromptService(db)

