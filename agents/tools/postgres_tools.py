from agno.tools.postgres import PostgresTools
from core.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host=HOST,
    port=PORT,
    db_name=DB_NAME,
    user=USER_DB, 
    password=PASSWORD_DB,
    inspect_queries=True,
)