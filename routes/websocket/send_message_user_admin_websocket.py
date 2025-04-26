import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from controllers.chat_history_controller import search_cached_answer, save_chat_history
from middleware.verify_token_websocket import verify_token
from agents.customer_service_team.customer_service_team import call_agent
from sqlalchemy.orm import Session
from config.config_db import config_db

router = APIRouter()
active_connections = {}
active_agents = {}

def get_team(user_id, role):
    if user_id not in active_agents:
        active_agents[user_id] = call_agent(user_id, role)
    return active_agents[user_id]

async def broadcast_active_users():
    active_users_copy = active_connections.copy()
    for conn in active_users_copy.values():
        try:
            await conn["websocket"].send_json({"type": "active_users", "users": list(active_users_copy.keys())})
        except Exception as e:
            print(f"❌ Gagal mengirim daftar pengguna aktif: {e}")

@router.get("/active-users")
async def get_active_users():
    active_users = [{"user_id": user_id, "role": conn["role"]} for user_id, conn in active_connections.items()]
    return {"success": True, "active_users": active_users}

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(config_db)):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_json({"error": "Token tidak ditemukan"})
        await websocket.close(code=1008)
        return

    try:
        decoded_token = verify_token(token)
        user_id = decoded_token.get("sub")
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
                    # Cek jawaban di cache
                    cached_response = search_cached_answer(question, db)

                    if cached_response:
                        await websocket.send_json({
                            "success": True,
                            "data": cached_response["output"],
                            "similarity": max(cached_response["input_similarity"], cached_response["output_similarity"])
                        })
                        continue
                    
                    team = get_team(user_id, role)
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(None, team.run, question)

                    save_response = save_chat_history(db, user_id, question, response.content)
                    await websocket.send_json({"success": True, "data": save_response})

                    # Kirim pesan ke semua admin yang aktif
                    for admin_id, conn in active_connections.items():
                        if conn["role"] == "admin":
                            await conn["websocket"].send_json({
                                "success": True,
                                "user_id": user_id,
                                "question": question,
                                "output": save_response
                            })
                            print(f"📨 Pesan dikirim ke admin {admin_id}")

                elif role == "admin":
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
                        await websocket.send_json({"success": True, "message": "Pesan terkirim ke user", "user_id": target_user_id})
                    else:
                        await websocket.send_json({"success": False, "error": "User tidak ditemukan atau tidak aktif"})

        except WebSocketDisconnect:
            print(f"{role.capitalize()} {user_id} terputus")
        finally:
            active_connections.pop(user_id, None)
            active_agents.pop(user_id, None)
            await asyncio.sleep(0.1)
            await broadcast_active_users()

    except HTTPException as e:
        print(f"❌ HTTPException: {str(e)}")
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
