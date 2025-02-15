# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
# from slowapi import Limiter
# from slowapi.util import get_remote_address
# from sqlalchemy.orm import Session
# import jwt
# import time
# from agents.product_information_agent.product_information_agent import call_agent
# from config.config_db import config_db
# from models.chat_history_model import ChatHistory
# from config.settings import SECRET_KEY
# from middleware.verify_token import verify_token

# # Inisialisasi router dan limiter
# router = APIRouter()
# limiter = Limiter(key_func=get_remote_address)

# # Menyimpan koneksi WebSocket yang aktif
# active_connections = {}

# @router.websocket("/ws/chat")
# async def websocket_chat(
#     websocket: WebSocket,
#     db: Session = Depends(config_db)
# ):
#     # Ambil token JWT dari query parameters atau headers
#     # token = websocket.query_params.get("Sec-WebSocket-Protocol")
#     # if not token or not token.startswith("Bearer "):
#     #     await websocket.close(code=1008)  # Close connection jika token tidak valid
#     #     raise HTTPException(status_code=401, detail="Unauthorized")

#     # token = token.split(" ")[1]  # Hapus "Bearer" dari token
#     # try:
#     #     decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#     #     user_id = decoded_token.get("user_id")
#     #     if not user_id:
#     #         await websocket.close(code=1008)
#     #         raise HTTPException(status_code=401, detail="Invalid token")
#     # except Exception:
#     #     await websocket.close(code=1008)
#     #     raise HTTPException(status_code=401, detail="Invalid token")

#     # Terima koneksi WebSocket
#     await websocket.accept()
#     user_id = "ttest1234"
#     active_connections[user_id] = websocket  # Simpan koneksi pengguna
#     print(f"User {user_id} connected")

#     try:
#         while True:
#             # Terima pesan dari klien
#             data = await websocket.receive_json()
#             question = data.get("question")
#             if not question:
#                 await websocket.send_json({"success": False, "error": "Question is required"})
#                 continue

#             start_time = time.time()
#             try:
#                 # Panggil agent untuk memproses pertanyaan
#                 # user_id="test1223"
#                 agent = call_agent(user_id, user_id)
#                 response = agent.run(question)
#                 save_response = response.content if isinstance(response.content, str) else str(response.content)
#                 latency = time.time() - start_time

#                 # Simpan chat history ke database
#                 chat_history = ChatHistory(
#                     name=user_id,
#                     input=question,
#                     output=save_response,
#                     error=None,
#                     latency=latency,
#                     agent_name="product information agent",
#                 )
#                 db.add(chat_history)
#                 db.commit()

#                 # Kirim jawaban kembali ke klien
#                 await websocket.send_json({"success": True, "data": save_response})
#             except Exception as e:
#                 latency = time.time() - start_time

#                 # Simpan error ke chat history
#                 chat_history = ChatHistory(
#                     name=user_id,
#                     input=question,
#                     output=None,
#                     error=str(e),
#                     latency=latency,
#                     agent_name="product information agent",
#                 )
#                 db.add(chat_history)
#                 db.commit()

#                 await websocket.send_json({"success": False, "error": str(e)})
#     except WebSocketDisconnect:
#         print(f"User {user_id} disconnected")
#         active_connections.pop(user_id, None)

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

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
active_connections = {}

@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(config_db)
):
    # Ambil token dari query parameter
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token tidak ditemukan")
    
    try:
        # Decode JWT token
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")
        print(user_id)
        if not user_id:
            await websocket.close(code=1008)
            raise HTTPException(status_code=401, detail="Token tidak valid")
            
        # Terima koneksi WebSocket
        await websocket.accept()
        active_connections[user_id] = websocket
        print(f"User {user_id} terhubung")

        try:
            while True:
                data = await websocket.receive_json()
                question = data.get("question")
                
                if not question:
                    await websocket.send_json({"success": False, "error": "Pertanyaan diperlukan"})
                    continue

                start_time = time.time()
                try:
                    agent = call_agent(user_id, user_id)
                    response = agent.run(question)
                    save_response = response.content if isinstance(response.content, str) else str(response.content)
                    latency = time.time() - start_time

                    # Simpan ke database
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

                    await websocket.send_json({"success": True, "data": save_response})
                except Exception as e:
                    latency = time.time() - start_time
                    
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
            print(f"User {user_id} terputus")
            active_connections.pop(user_id, None)
            
    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token kedaluwarsa")
    except jwt.InvalidTokenError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token tidak valid")
    except Exception as e:
        await websocket.close(code=1008)
        raise HTTPException(status_code=500, detail=f"Kesalahan server: {str(e)}")