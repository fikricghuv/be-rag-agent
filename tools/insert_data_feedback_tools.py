from typing import Optional
from agno.tools import Toolkit
from agno.utils.log import logger
import psycopg2  # Library untuk PostgreSQL
from config.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

connection_params = {
    "host": HOST,
    "port": PORT,
    "dbname": DB_NAME,
    "user": USER_DB,
    "password": PASSWORD_DB
}

class PostgresInsertToolkit(Toolkit):
    def __init__(self, connection_params: dict):
        """
        Custom toolkit untuk melakukan operasi insert ke PostgreSQL.

        Args:
            connection_params (dict): Parameter koneksi untuk PostgreSQL (host, port, dbname, user, password).
        """
        super().__init__(name="postgres_insert_toolkit")
        self.connection_params = connection_params
        self.register(self.insert_feedback_data)

    def insert_feedback_data(
        self,
        feedback_from_customer: str,
        sentiment: str,
        potential_actions: str,
        keyword_issue: str,
        schema_name: Optional[str] = "ai",  # Schema default: ai
        table_name: Optional[str] = "customer_feedback",
    ) -> str:
        """
        Menyisipkan data feedback pelanggan ke tabel PostgreSQL di schema tertentu.

        Args:
            feedback_from_customer (str): Feedback dari pelanggan.
            sentiment (str): Sentimen dari feedback (Positive, Negative, Neutral).
            potential_actions (str): Tindakan potensial berdasarkan feedback.
            keyword_issue (str): Kata kunci terkait masalah dalam feedback.
            schema_name (str, optional): Nama schema di database. Default: "ai".
            table_name (str, optional): Nama tabel di database. Default: "customer_feedback".

        Returns:
            str: Pesan sukses atau error.
        """
        # Query untuk menyisipkan data
        insert_query = f"""
        INSERT INTO {schema_name}.{table_name}(
            feedback_from_customer, sentiment, potential_actions, keyword_issue
        ) VALUES (%s, %s, %s, %s);
        """

        try:
            # Membuka koneksi ke PostgreSQL
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()

            # Menjalankan query insert
            logger.info(f"Executing query: {insert_query}")
            cursor.execute(
                insert_query,
                (feedback_from_customer, sentiment, potential_actions, keyword_issue),
            )

            # Commit dan tutup koneksi
            conn.commit()
            cursor.close()
            conn.close()
            return "Data successfully inserted into PostgreSQL."
        except Exception as e:
            logger.error(f"Failed to insert data into PostgreSQL: {e}")
            return f"Error: {e}"

