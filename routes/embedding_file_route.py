from fastapi import APIRouter, HTTPException
from models.knowledge_base_config_schema import KnowledgeBaseConfig
from tools.save_file_from_postgres import save_pdfs_locally
from tools.knowledge_base_tools import knowledge_base, knowledge_base_json
from tools.get_knowledge_base_param import get_knowledge_base_config
router = APIRouter()

@router.get("/embedding-file")
async def process_embedding():
    print("Memulai embedding proses...")
    try:
        save_pdfs_locally()
        print("PDFs saved locally.")

        # db_config = get_knowledge_base_config()

        # kb_config = KnowledgeBaseConfig(**db_config)
        
        # kb = knowledge_base(
        #     chunk_size=kb_config.chunk_size,
        #     overlap=kb_config.overlap,
        #     num_documents=kb_config.num_documents,
        # )
        kb = knowledge_base_json()
        print("Knowledge base initialized.")

        kb.load(recreate=True, upsert=True)
        print("Knowledge base loaded.")
        
        return {"message": "Embedding berhasil diproses!"}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
