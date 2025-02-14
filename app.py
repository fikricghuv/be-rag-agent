from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
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
from routes.generate_token import router as generate_token
from routes.get_name_from_history_chat import router as get_name_from_history_chat
from routes.get_chat_from_history_chat import router as get_chat_from_history_chat
from routes.get_total_chat_from_history_chat import router as get_total_chat_from_history_chat
from routes.get_total_user_from_history_chat import router as get_total_user_from_history_chat
from routes.websocket.ask_agent_websocket import router as ask_agent_websocket
from starlette.responses import JSONResponse

# Inisialisasi aplikasi dan limiter
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):

    response = await call_next(request)
    # response.headers["Content-Security-Policy"] = "default-src 'self'"
    # response.headers["X-Content-Type-Options"] = "nosniff"
    # response.headers["X-Frame-Options"] = "DENY"
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # response.headers["Referrer-Policy"] = "no-referrer"

    return response


# Tambahkan handler untuk rate limit error
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded."},
    )

# Tambahkan handler untuk API Key error
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 403:
        print("Forbidden: Invalid or missing API Key.")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden: Invalid or missing API Key."},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Daftarkan route
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
app.include_router(generate_token)
app.include_router(get_name_from_history_chat)
app.include_router(get_chat_from_history_chat)
app.include_router(get_total_chat_from_history_chat)
app.include_router(get_total_user_from_history_chat)
app.include_router(ask_agent_websocket)

# Rate limit untuk root endpoint
@app.get("/")
@limiter.limit("10/minute")  # Maksimum 10 request per menit
async def read_root(request: Request):  # Tambahkan parameter 'request'
    return {"message": "Welcome to the Service Monitoring Agent!"}

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
import jwt
import time
from agents.product_information_agent.product_information_agent import call_agent
from config.config_db import config_db
from models.chat_history_model import ChatHistory
from config.settings import SECRET_KEY
from middleware.verify_token import verify_token

limiter = Limiter(key_func=get_remote_address)

# Menyimpan koneksi WebSocket yang aktif
active_connections = {}

@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(config_db)
):
    # Ambil token JWT dari query parameters atau headers
    token = websocket.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        await websocket.close(code=1008)  # Close connection jika token tidak valid
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = token.split(" ")[1]  # Hapus "Bearer" dari token
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")
        if not user_id:
            await websocket.close(code=1008)
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Invalid token")

    # Terima koneksi WebSocket
    await websocket.accept()
    active_connections[user_id] = websocket  # Simpan koneksi pengguna
    print(f"User {user_id} connected")

    try:
        while True:
            # Terima pesan dari klien
            data = await websocket.receive_json()
            question = data.get("question")
            if not question:
                await websocket.send_json({"success": False, "error": "Question is required"})
                continue

            start_time = time.time()
            try:
                # Panggil agent untuk memproses pertanyaan
                agent = call_agent(user_id, user_id)
                response = agent.run(question)
                save_response = response.content if isinstance(response.content, str) else str(response.content)
                latency = time.time() - start_time

                # Simpan chat history ke database
                chat_history = ChatHistory(
                    name=user_id,
                    input=question,
                    output=save_response,
                    error=None,
                    latency=latency,
                    agent_name="product information agent",
                )
                db.add(chat_history)
                db.commit()

                # Kirim jawaban kembali ke klien
                await websocket.send_json({"success": True, "data": save_response})
            except Exception as e:
                latency = time.time() - start_time

                # Simpan error ke chat history
                chat_history = ChatHistory(
                    name=user_id,
                    input=question,
                    output=None,
                    error=str(e),
                    latency=latency,
                    agent_name="product information agent",
                )
                db.add(chat_history)
                db.commit()

                await websocket.send_json({"success": False, "error": str(e)})
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected")
        active_connections.pop(user_id, None)