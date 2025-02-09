import psycopg2
from config.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

def get_knowledge_base_config():
    """
    Fungsi untuk mengambil konfigurasi knowledge_base dari database.
    """
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=USER_DB,
        password=PASSWORD_DB,
        host=HOST,
        port=PORT
    )
    try:
        with connection.cursor() as cursor:
            # Query untuk mengambil chunk_size, overlap, dan num_documents
            cursor.execute("""
                SELECT chunk_size, overlap, num_documents 
                FROM knowledge_base_config
                ORDER BY id DESC LIMIT 1
            """)
            result = cursor.fetchone()  # Ambil satu baris terakhir
            if result:
                return {
                    "chunk_size": result[0],
                    "overlap": result[1],
                    "num_documents": result[2]
                }
            else:
                raise ValueError("No configuration found in the database.")
    finally:
        connection.close()
