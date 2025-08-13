# app/api/endpoints/knowledge_base_routes.py
import logging
from fastapi import APIRouter, Depends
from services.knowledge_base_service import KnowledgeBaseService, get_knowledge_base_service
from middleware.token_dependency import verify_access_token_and_get_client_id
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig
from utils.exception_handler import handle_exceptions 
from uuid import UUID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge-base"])

@router.get("/knowledge-base/config", response_model=KnowledgeBaseConfig)
@handle_exceptions(tag="[KNOWLEDGE-BASE]")
async def get_knowledge_base_config_endpoint(
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info("[KNOWLEDGE-BASE] Fetching knowledge base config from DB.")
    return knowledge_base_service.get_knowledge_base_config_from_db(client_id=client_id)

@router.put("/knowledge-base/update-config", response_model=KnowledgeBaseConfig)
@handle_exceptions(tag="[KNOWLEDGE-BASE]")
async def update_knowledge_base_config_endpoint(
    new_config: KnowledgeBaseConfig,
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[KNOWLEDGE-BASE] Updating knowledge base config with: {new_config}")
    return knowledge_base_service.update_knowledge_base_config(new_config, client_id=client_id)
