from phi.tools.postgres import PostgresTools

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host="localhost",
    port=5532,
    db_name="ai",
    user="ai", 
    password="ai",
    inspect_queries=True,
)