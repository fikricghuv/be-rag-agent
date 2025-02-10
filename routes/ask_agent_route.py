# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from datetime import time
# import time 
# from agents.product_information_agent.product_information_agent import call_agent
# from config.config_db import config_db
# from models.query_request_schema import QueryRequest
# from models.chat_history_model import ChatHistory

# router = APIRouter()

# @router.post("/ask")
# def ask_agent(request: QueryRequest, db: Session = Depends(config_db)):
#     start_time = time.time()
#     try:
#         agent = call_agent(request.user_id, request.user_id)
#         response = agent.run(request.question)
#         save_response = response.content if isinstance(response.content, str) else str(response.content)
#         latency = time.time() - start_time

#         chat_history = ChatHistory(
#             name=request.user_id,
#             input=request.question,
#             output=save_response,
#             error=None,
#             latency=latency,
#             agent_name="product information agent",
#         )
#         db.add(chat_history)
#         db.commit()
#         return {"success": True, "data": save_response}
#     except Exception as e:
#         latency = time.time() - start_time
#         chat_history = ChatHistory(
#             name=request.user_id,
#             input=request.question,
#             output=None,
#             error=str(e),
#             latency=latency,
#             agent_name="product information agent",
#         )
#         db.add(chat_history)
#         db.commit()
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
import time
from agents.product_information_agent.product_information_agent import call_agent
from config.config_db import config_db
from models.query_request_schema import QueryRequest
from models.chat_history_model import ChatHistory
from config.settings import VALID_API_KEYS

# Inisialisasi router dan limiter
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

list_api_keys = VALID_API_KEYS

# Middleware untuk memverifikasi API Key
def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    if not api_key or api_key not in list_api_keys:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key.")

@router.post("/ask")
@limiter.limit("5/minute")  # Maksimum 5 request per menit per IP
async def ask_agent(request: Request, body: QueryRequest, db: Session = Depends(config_db)):
    verify_api_key(request)  # Panggil fungsi verifikasi API Key
    start_time = time.time()
    try:
        # Panggil agent untuk memproses pertanyaan
        agent = call_agent(body.user_id, body.user_id)
        response = agent.run(body.question)
        save_response = response.content if isinstance(response.content, str) else str(response.content)
        latency = time.time() - start_time

        # Simpan chat history ke database
        chat_history = ChatHistory(
            name=body.user_id,
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
