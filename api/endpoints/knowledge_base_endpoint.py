# app/api/endpoints/knowledge_base_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status 
from services.knowledge_base_service import KnowledgeBaseService, get_knowledge_base_service
from middleware.verify_api_key_header import api_key_auth 
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["knowledge-base"], 
)

@router.get("/knowledge-base/config", response_model=KnowledgeBaseConfig, dependencies=[Depends(api_key_auth)])
async def get_knowledge_base_config_endpoint(
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """
    Endpoint untuk mendapatkan konfigurasi knowledge base dari database.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request to get knowledge base config.")
        
        config_model = knowledge_base_service.get_knowledge_base_config_from_db()
        logger.info("Successfully retrieved knowledge base config.")
        
        return config_model
    
    except HTTPException as e:
        logger.warning(f"HTTPException raised during get knowledge base config: {e.detail}", exc_info=True)
        
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error in get_knowledge_base_config_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.put("/knowledge-base/update-config", response_model=KnowledgeBaseConfig, dependencies=[Depends(api_key_auth)]) 
async def update_knowledge_base_config_endpoint(
    new_config: KnowledgeBaseConfig,
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """
    Endpoint untuk memperbarui konfigurasi knowledge base di database.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        new_config: Data konfigurasi baru.
    """
    try:
        logger.info(f"Received request to update knowledge base config with: {new_config}")
        updated_config_model = knowledge_base_service.update_knowledge_base_config(new_config)

        logger.info("Knowledge base config updated successfully via endpoint.")
        
        return updated_config_model

    except HTTPException as e:
        logger.warning(f"HTTPException raised during update knowledge base config: {e.detail}", exc_info=True)
        
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error in update_knowledge_base_config_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
