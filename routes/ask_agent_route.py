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

# from fastapi import APIRouter, Depends, HTTPException, Request
# from slowapi import Limiter
# from slowapi.util import get_remote_address
# from sqlalchemy.orm import Session
# import time
# from agents.product_information_agent.product_information_agent import call_agent
# from config.config_db import config_db
# from models.query_request_schema import QueryRequest
# from models.chat_history_model import ChatHistory
# from config.settings import VALID_API_KEYS

# # Inisialisasi router dan limiter
# router = APIRouter()
# limiter = Limiter(key_func=get_remote_address)

# list_api_keys = VALID_API_KEYS

# # Middleware untuk memverifikasi API Key
# def verify_api_key(request: Request):
#     api_key = request.headers.get("x-api-key")
#     if not api_key or api_key not in list_api_keys:
#         raise HTTPException(status_code=403, detail="Invalid or missing API Key.")

# @router.post("/ask")
# @limiter.limit("5/minute")  # Maksimum 5 request per menit per IP
# async def ask_agent(request: Request, body: QueryRequest, db: Session = Depends(config_db)):
#     verify_api_key(request)  # Panggil fungsi verifikasi API Key
#     start_time = time.time()
#     try:
#         # Panggil agent untuk memproses pertanyaan
#         agent = call_agent(body.user_id, body.user_id)
#         response = agent.run(body.question)
#         save_response = response.content if isinstance(response.content, str) else str(response.content)
#         latency = time.time() - start_time

#         # Simpan chat history ke database
#         chat_history = ChatHistory(
#             name=body.user_id,
#             input=body.question,
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

#         # Simpan error ke chat history
#         chat_history = ChatHistory(
#             name=body.user_id,
#             input=body.question,
#             output=None,
#             error=str(e),
#             latency=latency,
#             agent_name="product information agent",
#         )
#         db.add(chat_history)
#         db.commit()

#         raise HTTPException(status_code=500, detail=str(e))

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
from config.settings import SECRET_KEY, VALID_API_KEYS

# Inisialisasi router dan limiter
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()  # Untuk parsing header Authorization

# Middleware untuk memverifikasi JWT
def verify_jwt(request: Request):
    token = request.headers.get("Authorization")
    print("get token: " + token)
    if not token:
        raise HTTPException(status_code=401, detail="Token missing.")
    
    # Pastikan token memiliki format "Bearer <token>"
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format.")
    
    try:
        token = token.split("Bearer ")[1]  # Ambil bagian token saja
        print("get clear token: " + token)
        decoded_token = jwt.decode(
            token,
            SECRET_KEY,  # Pastikan SECRET_KEY cocok
            algorithms=["HS256"],  # Pastikan algoritma cocok
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        print("Token expired.")
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError as e:
        print("invalid token: " + str(e))
        raise HTTPException(status_code=401, detail="Invalid token: " + str(e))


# Middleware untuk memverifikasi API Key
def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    print("get api-key" + api_key)
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key.")

@router.post("/ask")
@limiter.limit("5/minute")  # Maksimum 5 request per menit per IP
async def ask_agent(
    request: Request,
    body: QueryRequest, 
    db: Session = Depends(config_db), 
    decoded_token: dict = Depends(verify_jwt),  # Verifikasi token JWT
      # Hapus `Depends()` di sini
):
    verify_api_key(request)  # Panggil fungsi verifikasi API Key
    start_time = time.time()
    try:
        # Ambil user_id dari token
        user_id = decoded_token.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token.")

        # Panggil agent untuk memproses pertanyaan
        agent = call_agent(user_id, user_id)
        response = agent.run(body.question)
        save_response = response.content if isinstance(response.content, str) else str(response.content)
        latency = time.time() - start_time
        print("ini adalah response model: " + save_response)
        # Simpan chat history ke database
        chat_history = ChatHistory(
            name=user_id,
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
