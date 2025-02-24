from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
import jwt
import time
from agents.product_information_agent.product_information_agent import call_agent
from config.config_db import config_db
from models.query_request_schema import QueryRequest
from models.chat_history_model import ChatHistory
from config.settings import SECRET_KEY
from middleware.verify_token import verify_token
from agents.customer_service_agent.customer_service_agent import call_agent

# Inisialisasi router dan limiter
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()  # Untuk parsing header Authorization

@router.post("/ask")
@limiter.limit("5/minute")  # Maksimum 5 request per menit per IP
async def ask_agent(
    request: Request,
    body: QueryRequest, 
    db: Session = Depends(config_db), 
    # decoded_token: dict = Depends(verify_token),  # Verifikasi token JWT
    ):

    start_time = time.time()
    try:
        # Ambil user_id dari token
        # user_id = decoded_token.get("user_id")
        # if not user_id:
        #     raise HTTPException(status_code=401, detail="User ID not found in token.")

        # Panggil agent untuk memproses pertanyaan
        user_id = "user_id"
        agent = call_agent(user_id, user_id)
        response = agent.run(body.question)
        save_response = response.content if isinstance(response.content, str) else str(response.content)
        latency = time.time() - start_time
        print("ini adalah response model: " + save_response)
        # Simpan chat history ke database
        chat_history = ChatHistory(
            name="tset123",
            input=body.question,
            output=save_response,
            error=None,
            latency=latency,
            agent_name="product information agent",
        )
        db.add(chat_history)
        db.commit()

        return {"success": True, "data": save_response}
    except Exception as e:
        latency = time.time() - start_time

        # Simpan error ke chat history
        chat_history = ChatHistory(
            name=body.user_id,
            input=body.question,
            output=None,
            error=str(e),
            latency=latency,
            agent_name="product information agent",
        )
        db.add(chat_history)
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))
