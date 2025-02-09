from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.ask_agent_route import router as ask_agent_router
from routes.delete_file_route import router as delete_file_router
from routes.embedding_file_route import router as process_embedding_router
from routes.get_all_files_route import router as get_all_files_router
from routes.get_chat_history import router as get_chat_history_router
from routes.get_feedback_route import router as get_feedbacks_router
from routes.get_prompt_route import router as get_prompts_router
from routes.send_message_admin_route import router as send_admin_message_router
from routes.update_prompt_route import router as update_prompt_router
from routes.upload_file_route import router as upload_file_router
from routes.get_knowledge_base_config import router as get_knowledge_base_config
from routes.update_knowledge_base_config_route import router as update_knowledge_base_config_route

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Service Monitoring Agent!"}

# Daftarkan router
app.include_router(ask_agent_router)
app.include_router(delete_file_router)
app.include_router(process_embedding_router)
app.include_router(get_all_files_router)
app.include_router(get_chat_history_router)
app.include_router(get_feedbacks_router)
app.include_router(get_prompts_router)
app.include_router(send_admin_message_router)
app.include_router(update_prompt_router)
app.include_router(upload_file_router)
app.include_router(get_knowledge_base_config)
app.include_router(update_knowledge_base_config_route)