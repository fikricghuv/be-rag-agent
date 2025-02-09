from fastapi import APIRouter, HTTPException
from models.knowledge_base_config_schema import KnowledgeBaseConfig
from tools.knowledge_base_tools import knowledge_base
from tools.get_knowledge_base_param import get_knowledge_base_config

router = APIRouter()

# Function untuk mendapatkan Knowledge Base dengan parameter yang sudah diupdate
@router.get("/get-knowledge-base-config")
def set_knowledge_base():
    """Mengambil konfigurasi dari database dan membuat knowledge base."""
    # Mengambil konfigurasi dari database
    db_config = get_knowledge_base_config()

    kb_config = KnowledgeBaseConfig(**db_config)

    # Membuat knowledge base menggunakan konfigurasi dari database
    kb = knowledge_base(
        chunk_size=kb_config.chunk_size,
        overlap=kb_config.overlap,
        num_documents=kb_config.num_documents,
    )

    # Return informasi konfigurasi
    return {"message": "Knowledge base config retrieved and applied", "config": kb_config}
