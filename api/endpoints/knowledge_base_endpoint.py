# app/api/endpoints/knowledge_base_routes.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status 
from services.knowledge_base_service import KnowledgeBaseService, get_knowledge_base_service # Menggunakan service class dan dependency
from services.verify_api_key_header import api_key_auth 
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    tags=["knowledge-base"], # Tag untuk dokumentasi Swagger UI
)

# --- Routes ---

@router.get("/knowledge-base/config", response_model=KnowledgeBaseConfig, dependencies=[Depends(api_key_auth)])
async def get_knowledge_base_config_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mendapatkan konfigurasi knowledge base dari database.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request to get knowledge base config.")
        # Memanggil metode service untuk mengambil config dari DB
        config_model = knowledge_base_service.get_knowledge_base_config_from_db()
        logger.info("Successfully retrieved knowledge base config.")
        # Pydantic dengan ORM mode akan mengonversi KnowledgeBaseConfigModel menjadi KnowledgeBaseConfig
        return config_model
    # Menangkap HTTPException yang mungkin dilempar oleh service (misalnya 404, 500)
    except HTTPException as e:
        logger.warning(f"HTTPException raised during get knowledge base config: {e.detail}", exc_info=True)
        # Re-raise HTTPException agar ditangani oleh FastAPI
        raise e
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in get_knowledge_base_config_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.put("/knowledge-base/update-config", response_model=KnowledgeBaseConfig, dependencies=[Depends(api_key_auth)]) # Mengembalikan model config yang diperbarui
async def update_knowledge_base_config_endpoint( # Mengubah nama fungsi untuk kejelasan
    # Menerima data konfigurasi baru di request body
    new_config: KnowledgeBaseConfig,
    # Menggunakan dependency untuk mendapatkan instance service
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk memperbarui konfigurasi knowledge base di database.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        new_config: Data konfigurasi baru.
    """
    try:
        logger.info(f"Received request to update knowledge base config with: {new_config}")
        # Memanggil metode service untuk memperbarui config
        # Service method akan melempar HTTPException (400, 404, atau 500) jika terjadi error
        updated_config_model = knowledge_base_service.update_knowledge_base_config(new_config)

        # Jika service method berhasil dan tidak melempar exception, kembalikan objek model
        logger.info("Knowledge base config updated successfully via endpoint.")
        # Pydantic dengan ORM mode akan mengonversi KnowledgeBaseConfigModel menjadi KnowledgeBaseConfig
        return updated_config_model

    # Menangkap HTTPException yang mungkin dilempar oleh service (400, 404, 500)
    except HTTPException as e:
        logger.warning(f"HTTPException raised during update knowledge base config: {e.detail}", exc_info=True)
        # Re-raise HTTPException agar ditangani oleh FastAPI
        raise e
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in update_knowledge_base_config_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
