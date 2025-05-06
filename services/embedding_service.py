# app/services/embedding_service.py
from utils.save_file_from_postgres import save_pdfs_locally
from agents.tools.knowledge_base_tools import knowledge_base
from models.knowledge_base_config_model import KnowledgeBaseConfig
from utils.get_knowledge_base_param import get_knowledge_base_config

class EmbeddingService:
    def __init__(self):
        pass  # Bisa menerima dependensi konfigurasi di sini jika diperlukan

    async def process_embedding(self):
        print("Memulai embedding proses di service...")
        try:
            save_pdfs_locally()
            print("PDFs saved locally (service).")

            db_config = get_knowledge_base_config()
            kb_config = KnowledgeBaseConfig(**db_config)

            kb = knowledge_base(
                chunk_size=kb_config.chunk_size,
                overlap=kb_config.overlap,
                num_documents=kb_config.num_documents,
            )

            kb.load(recreate=True, upsert=True)
            print("Knowledge base loaded (service).")

            return {"message": "Embedding berhasil diproses oleh service!"}
        except Exception as e:
            print(f"Error di service: {str(e)}")
            raise