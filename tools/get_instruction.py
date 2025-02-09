import psycopg2

def get_instructions_from_db():
    """Fungsi untuk mengambil instructions dari database."""
    connection = psycopg2.connect(
        dbname="ai",
        user="ai",
        password="ai",
        host="localhost",
        port="5532"
    )
    try:
        with connection.cursor() as cursor:
            # Query untuk mengambil content dari tabel
            cursor.execute("SELECT content FROM ai.prompts WHERE name='Product Information Agent'")
            return [row[0] for row in cursor.fetchall()]  # Ambil semua hasil
    finally:
        connection.close()