from agno.tools import tool
import psycopg2
from core.settings import HOST, PORT, DB_NAME, USER_DB, PASSWORD_DB
import logging
import time
from typing import Any, Callable, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def database_logger_hook(
    function_name: str, 
    function_call: Callable, 
    arguments: Dict[str, Any]
) -> Any:
    """Log database operations with timing and details"""
    logger.info(f"Starting {function_name} with arguments: {arguments}")
    start_time = time.time()
    
    try:
        result = function_call(**arguments)
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ {function_name} completed successfully in {duration:.2f}s")
        logger.info(f"Result: {result}")
        return result
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        logger.error(f"❌ {function_name} failed after {duration:.2f}s: {str(e)}")
        raise

@tool(
    name="insert_customer_feedback",
    description="Insert customer feedback into PostgreSQL database",
    tool_hooks=[database_logger_hook],
    show_result=False
)

def insert_customer_feedback(
    feedback_text: str,
    sentiment: str,
    potential_actions: str,
    keyword_issue: str,
    category: str,
    product_name: str,
    email_user: str,
    client_id: str
) -> str:
    """
    Insert customer feedback into dt_customer_feedback table.
    
    Args:
        feedback_text: Customer feedback text
        sentiment: Sentiment analysis result
        potential_actions: Suggested actions
        keyword_issue: Issue keywords
        category: Feedback category
        product_name: Product name
        email_user: User email
        client_id: Client identifier
    
    Returns:
        str: Success/failure message
    """
    try:
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DB_NAME,
            user=USER_DB,
            password=PASSWORD_DB
        )
        
        cursor = conn.cursor()
        
        query = """
        INSERT INTO dt_customer_feedback 
        (feedback_from_customer, sentiment, potential_actions, keyword_issue, 
         category, product_name, email_user, client_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            feedback_text, sentiment, potential_actions, keyword_issue,
            category, product_name, email_user, client_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return "Customer feedback inserted successfully"
        
    except Exception as e:
        return f"Error inserting feedback: {str(e)}"
