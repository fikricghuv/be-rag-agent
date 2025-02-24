from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import jwt
import time
import re
from config.config_db import config_db
from models.chat_history_model import ChatHistory
from config.settings import SECRET_KEY, ALGORITHM, SECRET_KEY_ADMIN
from agents.customer_service_agent.customer_service_agent import call_agent
from middleware.verify_token_websocket import verify_token

router = APIRouter()
active_connections = {}  # Menyimpan {user_id: {"websocket": WebSocket, "role": "user" atau "admin"}}

async def broadcast_active_users():
    active_users = [{"user_id": user_id, "role": conn["role"]} for user_id, conn in active_connections.items()]
    for conn in active_connections.values():
        try:
            await conn["websocket"].send_json({"type": "active_users", "data": active_users})
        except:
            pass  # Handle jika ada koneksi yang tidak dapat menerima pesan

@router.get("/active-users")
async def get_active_users():
    active_users = [{"user_id": user_id, "role": conn["role"]} for user_id, conn in active_connections.items()]
    return {"success": True, "active_users": active_users}

@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(config_db)
):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token tidak ditemukan")
    
    try:
        decoded_token = verify_token(token)
        user_id = decoded_token.get("user_id")
        role = decoded_token.get("role")
        
        if not user_id or role not in ["user", "admin"]:
            await websocket.close(code=1008)
            raise HTTPException(status_code=401, detail="Token tidak valid")

        await websocket.accept()
        active_connections[user_id] = {"websocket": websocket, "role": role}
        await broadcast_active_users()
        
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
                    print(f"User {user_id} bertanya:", question)
                    agent = call_agent(user_id, user_id)
                    response = agent.run(question)
                    save_response = response.content if isinstance(response.content, str) else str(response.content)
                    save_response = re.sub(r" - Running:\s*search_knowledge_base\(query=.*?\)\\n?", "", save_response)
                    save_response = re.sub(r" - Running:\s*\w+\(.*?\)\n?", "", save_response)

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

                    await websocket.send_json({"success": True, "data": save_response})

                    for admin_id, conn in active_connections.items():
                        if conn["role"] == "admin":
                            await conn["websocket"].send_json({
                                "success": True,
                                "user_id": user_id,
                                "question": question,
                                "output": save_response
                            })
                            print(f"📨 [BACKEND] Pesan dari user {user_id} dikirim ke admin {admin_id}")
                
                elif role == "admin":
                    start_time = time.time()
                    target_user_id = data.get("user_id")
                    admin_message = data.get("question")

                    if not target_user_id or not admin_message:
                        await websocket.send_json({"success": False, "error": "Target user dan pesan diperlukan"})
                        continue

                    target_conn = active_connections.get(target_user_id)
                    if target_conn and target_conn["role"] == "user":
                        await target_conn["websocket"].send_json({
                            "success": True,
                            "data": admin_message,
                            "from": "bot"
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
            await broadcast_active_users()

    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token kedaluwarsa")
    except jwt.InvalidTokenError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Token tidak valid")
    except Exception as e:
        await websocket.close(code=1008)
        raise HTTPException(status_code=500, detail=f"Kesalahan server: {str(e)}")
