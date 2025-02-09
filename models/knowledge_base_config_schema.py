from pydantic import BaseModel

# Simpan konfigurasi default
class KnowledgeBaseConfig(BaseModel):
    chunk_size: int 
    overlap: int 
    num_documents: int 