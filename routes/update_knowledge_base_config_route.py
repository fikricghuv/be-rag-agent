from fastapi import APIRouter, HTTPException, Depends
from controllers.knowledge_base_controller import update_knowledge_base_config
from models.knowledge_base_config_schema import KnowledgeBaseConfig

router = APIRouter()

@router.post("/update-knowledge-base")
def update_config(new_config: KnowledgeBaseConfig):
    """Mengupdate konfigurasi di database"""
    try:
        updated_config = update_knowledge_base_config(new_config)
        return {"message": "Configuration updated successfully", "config": updated_config}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
