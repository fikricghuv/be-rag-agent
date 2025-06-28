# app/api/endpoints/prompt_endpoint.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path # Import status, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
# Mengimpor dependency service dan API Key
from services.prompt_service import PromptService, get_prompt_service # Menggunakan service class dan dependency
from middleware.verify_api_key_header import api_key_auth # Asumsi dependency api_key_header diimpor dari services.verify_api_key_header
# Mengimpor Pydantic model respons dan update
from schemas.prompt_schema import PromptResponse, PromptUpdate
from typing import List

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    tags=["prompts"], # Tag untuk dokumentasi Swagger UI
)

# --- Routes ---

# Endpoint untuk mengambil semua prompt
# Menerapkan API Key Authentication
@router.get("/prompts", response_model=List[PromptResponse], dependencies=[Depends(api_key_auth)])
async def get_prompts_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Endpoint untuk mendapatkan semua prompt.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request to get all prompts.")
        # Memanggil metode instance dari service
        # Jika service.fetch_all_prompts() mendukung pagination, teruskan offset/limit di sini
        # prompts = prompt_service.fetch_all_prompts()
        prompts =prompt_service.fetch_customer_service_prompt()
        logger.info(f"Returning {len(prompts)} prompts.")
        # Pydantic dengan orm_mode=True akan otomatis mengonversi List[Prompt] menjadi List[PromptResponse]
        return prompts
    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_prompts_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching prompts."
        )
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in get_prompts_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


# Endpoint untuk memperbarui prompt berdasarkan nama
# Menerapkan API Key Authentication
@router.put("/prompts/{name}", response_model=PromptResponse, dependencies=[Depends(api_key_auth)])
async def update_prompt_endpoint(
    prompt_update: PromptUpdate,
    name: str = Path(..., description="Name of the prompt to update"),
    prompt_service: PromptService = Depends(get_prompt_service),
):


    """
    Endpoint untuk memperbarui prompt berdasarkan nama.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        name: Nama prompt yang akan diperbarui.
        prompt_update: Data pembaruan prompt (hanya konten).
    """
    try:
        logger.info(f"Received request to update prompt with name: {name}")
        # Memanggil metode instance dari service
        # Service method akan melempar HTTPException (404 atau 500) jika terjadi error
        updated_prompt = prompt_service.update_prompt(name, prompt_update)

        # Jika service method berhasil dan tidak melempar exception, kembalikan hasilnya
        logger.info(f"Prompt with name {name} updated successfully.")
        # Pydantic dengan orm_mode=True akan otomatis mengonversi Prompt menjadi PromptResponse
        return updated_prompt

    # Menangkap HTTPException yang mungkin dilempar oleh service (404, 500)
    except HTTPException as e:
        logger.warning(f"HTTPException raised during prompt update for name {name}: {e.detail}", exc_info=True)
        # Re-raise HTTPException agar ditangani oleh FastAPI
        raise e
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in update_prompt_endpoint for name {name}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# --- Anda bisa menambahkan endpoint lain terkait prompt di sini (misalnya, POST untuk membuat prompt baru) ---

