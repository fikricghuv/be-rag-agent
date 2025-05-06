from fastapi import APIRouter, HTTPException, Depends
from services.knowledge_base_service import KnowledgeBaseService
from models.knowledge_base_config_model import KnowledgeBaseConfig

router = APIRouter()

def get_knowledge_base_service() -> KnowledgeBaseService:
    return KnowledgeBaseService()

@router.get("/get-knowledge-base-config")
def set_knowledge_base_endpoint(knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service)):
    """Mengambil konfigurasi dari database dan membuat knowledge base."""
    try:
        return knowledge_base_service.retrieve_and_apply_kb_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get and apply config: {e}")
    
@router.post("/update-knowledge-base")
def update_config_endpoint(
    new_config: KnowledgeBaseConfig,
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Mengupdate konfigurasi di database"""
    try:
        updated_config = knowledge_base_service.update_knowledge_base_config(new_config)
        return {"message": "Configuration updated successfully", "config": updated_config}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")