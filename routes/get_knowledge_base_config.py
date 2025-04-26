from fastapi import APIRouter, HTTPException
from controllers.knowledge_base_controller import retrieve_and_apply_kb_config

router = APIRouter()

@router.get("/get-knowledge-base-config")
def set_knowledge_base():
    """Mengambil konfigurasi dari database dan membuat knowledge base."""
    try:
        return retrieve_and_apply_kb_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get and apply config: {e}")
