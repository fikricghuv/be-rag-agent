from fastapi import APIRouter, HTTPException
from tools.save_file_from_postgres import save_pdfs_locally
from tools.knowledge_base_tools import knowledge_base

router = APIRouter()

@router.get("/embedding-file")
async def process_embedding():
    print("Memulai embedding proses...")
    try:
        save_pdfs_locally()
        print("PDFs saved locally.")
        kb = knowledge_base()  # Pastikan knowledge_base diinisialisasi
        print("Knowledge base initialized.")
        kb.load(recreate=True, upsert=True)
        print("Knowledge base loaded.")
        return {"message": "Embedding berhasil diproses!"}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
