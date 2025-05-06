import psycopg2
from core.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

def get_instructions_from_db(name):
    """Fungsi untuk mengambil instructions dari database."""
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=USER_DB,
        password=PASSWORD_DB,
        host=HOST,
        port=PORT
    )
    try:
        with connection.cursor() as cursor:
            # Query untuk mengambil content dari tabel
            cursor.execute("SELECT content FROM ai.prompts WHERE name=%s", (name,))
            return [row[0] for row in cursor.fetchall()]  # Ambil semua hasil
    finally:
        connection.close()