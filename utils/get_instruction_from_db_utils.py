import psycopg2
import logging
from core.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

logger = logging.getLogger(__name__)

def get_instructions_from_db(name: str):
    """
    Mengambil content dari tabel ai.prompts berdasarkan nama prompt.
    
    Args:
        name (str): Nama prompt yang ingin diambil.

    Returns:
        List[str]: Daftar konten hasil query.
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
                cursor.execute("SELECT content FROM ai.prompts WHERE name = %s", (name,))
                results = [row[0] for row in cursor.fetchall()]
                logger.info(f"Retrieved {len(results)} instructions for name='{name}'")
                return results

    except psycopg2.Error as e:
        logger.error(f"Database error while fetching instructions: {e}")
        return []
