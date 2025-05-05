from agno.agent import Agent
from agno.tools.postgres import PostgresTools
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.tools.baidusearch import BaiduSearchTools
from agno.tools.telegram import TelegramTools
from agno.storage.postgres import PostgresStorage
from models.openai_model import openai_model
from models.gemini_model import gemini_model
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, URL_DB_POSTGRES, SESSION_TABLE_NAME, KNOWLEDGE_TABLE_NAME, HOST, PORT, DB_NAME, USER_DB, PASSWORD_DB, SCHEMA_TABLE
from agents.customer_service_agent.prompt import prompt_agent
from agno.embedder.openai import OpenAIEmbedder

storage = PostgresStorage(table_name=SESSION_TABLE_NAME, db_url=URL_DB_POSTGRES)
storage.upgrade_schema()


knowledge_base = PDFKnowledgeBase(
    path="products",
    vector_db=PgVector(
        embedder=OpenAIEmbedder(),
        table_name=KNOWLEDGE_TABLE_NAME,
        db_url=URL_DB_POSTGRES,
        search_type=SearchType.hybrid,
        content_language="indonesian",
    ),
)

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host=HOST,
    port=PORT,
    db_name=DB_NAME,
    user=USER_DB,
    password=PASSWORD_DB,
    table_schema=SCHEMA_TABLE
)

def call_customer_service_agent(session_id, user_id) :
    agent = Agent(
        model=openai_model(temperature=0.3, max_tokens=1000),
        # model=gemini_model(),
        session_id=session_id,
        user_id=user_id,
        knowledge=knowledge_base, 
        show_tool_calls=True,
        search_knowledge=True,
        tools=[postgres_tools, BaiduSearchTools(), TelegramTools(token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)],
        instructions=prompt_agent(),
        
        # Store the chat history in the database
        storage=storage,
        # Add the chat history to the messages
        add_history_to_messages=True,
        # Number of history runs
        num_history_runs=3,

        add_datetime_to_instructions=True,

        markdown=True,
        debug_mode=True,
       
        )
    
    return agent

# app = FastAPI()


# # Pydantic models
# class ChatRequest(BaseModel):
#     session_id: str
#     user_id: str
#     message: str

# class ChatResponse(BaseModel):
#     reply: str

# # Endpoint to chat with the agent
# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(req: ChatRequest):
#     try:
#         # Panggil agent seperti pada websocket
#         agent = call_agent(req.user_id, req.session_id)  # Samakan cara pemanggilan

#         result = agent.run(req.message, show_full_reasoning=True)
#         content = result.content

#         if not isinstance(content, str):
#             content = str(content)

#         # Bersihkan log internal jika perlu
#         cleaned_response = re.sub(r" - Running:\s*search_knowledge_base\(query=.*?\)\\n?", "", content)
#         cleaned_response = re.sub(r" - Running:\s*\w+\(.*?\)\n?", "", cleaned_response)
#         cleaned_response = re.sub(r" - Running:.*?\(.*?\)\n?", "", cleaned_response, flags=re.MULTILINE)

#         return ChatResponse(reply=cleaned_response)
#     except Exception as e:
#         print(f"❌ Error saat memanggil agent: {e}")
#         raise HTTPException(status_code=500, detail=str(e))