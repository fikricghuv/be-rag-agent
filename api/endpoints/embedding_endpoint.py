# app/api/endpoints/embedding_endpoint.py
from fastapi import APIRouter, HTTPException, Depends
from services.embedding_service import EmbeddingService

router = APIRouter()

@router.get("/embedding-file")
async def process_embedding_endpoint(embedding_service: EmbeddingService = Depends()):
    print("Menerima request embedding di endpoint...")
    try:
        result = await embedding_service.process_embedding()
        return result
    except Exception as e:
        print(f"Error di endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))