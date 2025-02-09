from fastapi import APIRouter, HTTPException
from models.knowledge_base_config_schema import KnowledgeBaseConfig
import psycopg2
from config.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

router = APIRouter()

@router.post("/update-knowledge-base")
def update_config(new_config: KnowledgeBaseConfig):
    """Mengupdate konfigurasi di database"""

    # Validasi parameter jika dibutuhkan
    # if new_config.chunk_size < 1000 or new_config.overlap <= 0 or new_config.num_documents <= 1:
    #     raise HTTPException(status_code=400, detail="Invalid parameters for config parameters knowledge base")

    # Koneksi ke database
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=USER_DB,
        password=PASSWORD_DB,
        host=HOST,
        port=PORT
    )

    try:
        with connection.cursor() as cursor:
            # Update data di tabel knowledge_base_config
            cursor.execute("""
                UPDATE knowledge_base_config
                SET chunk_size = %s,
                    overlap = %s,
                    num_documents = %s
                WHERE id = 1
            """, (new_config.chunk_size, new_config.overlap, new_config.num_documents))
            
            # Commit perubahan
            connection.commit()

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
    
    finally:
        connection.close()

    # Return response
    return {"message": "Configuration updated successfully", "config": new_config.dict()}
