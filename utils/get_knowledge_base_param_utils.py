import psycopg2
import logging
from core.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

logger = logging.getLogger(__name__)

def get_knowledge_base_config() -> dict:
    """
    Mengambil konfigurasi knowledge base terbaru dari database PostgreSQL.

    Returns:
        dict: Berisi 'chunk_size', 'overlap', dan 'num_documents'.

    Raises:
        ValueError: Jika tidak ada konfigurasi ditemukan.
        psycopg2.Error: Jika terjadi kesalahan pada koneksi atau query database.
    """
    try:
        with psycopg2.connect(
            dbname=DB_NAME,
            user=USER_DB,
            password=PASSWORD_DB,
            host=HOST,
            port=PORT
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT chunk_size, overlap, num_documents 
                    FROM ms_knowledge_base_config
                    ORDER BY id DESC
                    LIMIT 1
                """)
                result = cursor.fetchone()

                if not result:
                    logger.warning("No knowledge base config found in the database.")
                    raise ValueError("No configuration found in the database.")
                
                config = {
                    "chunk_size": result[0],
                    "overlap": result[1],
                    "num_documents": result[2]
                }
                logger.info(f"Knowledge base config fetched: {config}")
                return config

    except psycopg2.Error as e:
        logger.error(f"Database error while fetching knowledge base config: {e}", exc_info=True)
        raise
