from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import jwt
import time
from agents.product_information_agent.product_information_agent import call_agent
from config.config_db import config_db
from models.chat_history_model import ChatHistory
from config.settings import SECRET_KEY, ALGORITHM, SECRET_KEY_ADMIN
import re

router = APIRouter()
active_connections = {}  # Menyimpan {user_id: {"websocket": WebSocket, "role": "user" atau "cs"}}


def verify_token(token: str):
    """Coba decode token dengan dua SECRET_KEY"""
    for key in [SECRET_KEY, SECRET_KEY_ADMIN]:
        try:
            return jwt.decode(token, key, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidSignatureError:
            continue  # Coba SECRET_KEY yang lain
    raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(config_db)
):
    token = websocket.query_params.get("token")
    print("token", token)
    
    if not token:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token tidak ditemukan")
    
    try:
        # decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded_token = verify_token(token)
        user_id = decoded_token.get("user_id")
        role = decoded_token.get("role")  # Menentukan apakah user atau customer service
        
        if not user_id or role not in ["user", "admin"]:
            await websocket.close(code=1008)
            raise HTTPException(status_code=401, detail="Token tidak valid")

        await websocket.accept()
        active_connections[user_id] = {"websocket": websocket, "role": role}

        print(f"{role.capitalize()} {user_id} terhubung")

        try:
            while True:
                data = await websocket.receive_json()
                question = data.get("question")

                if not question:
                    await websocket.send_json({"success": False, "error": "Pesan diperlukan"})
                    continue

                if role == "user":
                    start_time = time.time()
                    # Jika user yang bertanya, agent yang menjawab
                    print(f"User {user_id} bertanya:", question)
                    agent = call_agent(user_id, user_id)
                    response = agent.run(question)
                    save_response = response.content if isinstance(response.content, str) else str(response.content)

                    save_response = re.sub(r" - Running:\s*search_knowledge_base\(query=.*?\)\n?", "", save_response)

                    # Simpan ke database
                    end_time = time.time()
                    latency = round(end_time - start_time, 2)
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

                    # Kirim balasan ke user
                    await websocket.send_json({"success": True, "data": save_response})

                    # 🔥 **Tambahan: Kirim Pesan User ke Semua Admin yang Terhubung**
                    for admin_id, conn in active_connections.items():
                        if conn["role"] == "admin":
                            await conn["websocket"].send_json({
                                "success": True,
                                "user_id": user_id,
                                "question": question,  # Pesan user ke admin
                                "output": save_response  # Balasan agent ke admin
                            })
                            print(f"📨 [BACKEND] Pesan dari user {user_id} dikirim ke admin {admin_id}")


                elif role == "admin":
                    start_time = time.time()
                    # Jika yang mengirim adalah customer service
                    target_user_id = data.get("user_id")
                    admin_message = data.get("question")
                    print("target_user_id: " , target_user_id)
                    print("cs_message :" , admin_message)

                    if not target_user_id or not admin_message:
                        await websocket.send_json({"success": False, "error": "Target user dan pesan diperlukan"})
                        continue

                    target_conn = active_connections.get(target_user_id)

                    if target_conn and target_conn["role"] == "user":
                        await target_conn["websocket"].send_json({
                            "success": True,
                            "data": admin_message,
                            "from": "bot"  # Mengirim seolah-olah dari agent
                        })
                        end_time = time.time()
                        latency = round(end_time - start_time, 2)
                        chat_history = ChatHistory(
                        name=target_user_id,
                        input="",
                        output=admin_message,
                        error=None,
                        latency=latency,
                        agent_name="Admin",
                        )

                        db.add(chat_history)
                        db.commit()
                        print("chat admin tersimpan")

                        await websocket.send_json({"success": True, "message": "Pesan terkirim ke user", "user_id": target_user_id})
                    else:
                        await websocket.send_json({"success": False, "error": "User tidak ditemukan atau tidak aktif"})

        except WebSocketDisconnect:
            print(f"{role.capitalize()} {user_id} terputus")
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
