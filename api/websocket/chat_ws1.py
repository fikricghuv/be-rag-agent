import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from controllers.chat_history_controller import search_cached_answer, save_chat_history
from middleware.verify_token_websocket import verify_token
from agents.customer_service_team.customer_service_team import call_agent
from sqlalchemy.orm import Session
from core.config_db import config_db
from agents.customer_service_agent.customer_service_agent import call_customer_service_agent
from controllers.auth_controller import AuthController
from database.models.chat_ids_model import ChatIds, UserRole 
import re
import time

router = APIRouter()
active_connections = {}
active_agents = {}

def get_team(chatId, role):
    if chatId not in active_agents:
        # active_agents[user_id] = call_agent(user_id, role)
        active_agents[chatId] = call_customer_service_agent(chatId, role)
    return active_agents[chatId]

async def broadcast_active_users():
    active_users_copy = active_connections.copy()
    for conn in active_users_copy.values():
        try:
            await conn["websocket"].send_json({"type": "active_users", "users": list(active_users_copy.keys())})
        except Exception as e:
            print(f"❌ Gagal mengirim daftar pengguna aktif: {e}")

@router.get("/active-users")
async def get_active_users():
    active_users = [{"user_id": chatId, "role": conn["role"]} for chatId, conn in active_connections.items()]
    return {"success": True, "active_users": active_users}

@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, chatId: str = None, role: str = None, db: Session = Depends(config_db)):    
    
    start_time = time.time()
    
    print("🔑 Token diterima:", chatId, role)

    if not chatId or role not in ["user", "admin"]:
        error_message = "chatId dan/atau role tidak valid"
        print(f"WebSocket Error: {error_message}, chatId: {chatId}, role: {role}")
        await websocket.send_json({"error": error_message})
        await websocket.close(code=1008)  # 1008: Policy Violation
        return  # Penting: Keluar dari fungsi jika parameter tidak valid

    try:
        await websocket.accept()
        verify_id = AuthController().get_chat_id_data(chatId, db)  # Instantiate AuthController
        if not verify_id:
            error_message = "chatId tidak ditemukan di database"
            print(f"WebSocket Error: {error_message}, chatId: {chatId}")
            await websocket.send_json({"error": error_message})
            await websocket.close(code=1008)  # 1008: Policy Violation
            return

        active_connections[chatId] = {"websocket": websocket, "role": role}
        await broadcast_active_users()
        
        try:

            while True:
                data = await websocket.receive_json()
                print("📩 Data diterima:", data)
                question = data.get("question")
                role = data.get("role")
                chatId = data.get("user_id")
                print("🔑 Token diterima:", chatId, role, question)

                if not question:
                    await websocket.send_json({"success": False, "error": "Pesan diperlukan"})
                    continue

                if role == "user":
                    # Cek jawaban di cache
                    # cached_response = search_cached_answer(question, db)

                    # if cached_response:
                    #     await websocket.send_json({
                    #         "success": True,
                    #         "data": cached_response["output"],
                    #         "similarity": max(cached_response["input_similarity"], cached_response["output_similarity"])
                    #     })
                    #     continue
                    
                    # team = get_team(user_id, role)
                    # loop = asyncio.get_running_loop()
                    # response = await loop.run_in_executor(None, team.run, question)

                    agent = call_customer_service_agent(chatId, chatId)
                    print("🧠 Memanggil agent...")
                    loop = asyncio.get_running_loop()
                    print("📥 Pertanyaan diterima:", question)

                    response = await loop.run_in_executor(None, agent.run, question)

                    end_time = time.time()
                    latency = round(end_time - start_time, 2)
                    print("⏱️ Latency:", latency)

                    save_response = save_chat_history(db, chatId, question, response.content, latency)

                    print("📦 Response ke UI:", save_response)

                    await websocket.send_json({"success": True, "data": save_response})

                    # Kirim pesan ke semua admin yang aktif
                    for admin_id, conn in active_connections.items():
                        if conn["role"] == "admin":
                            await conn["websocket"].send_json({
                                "success": True,
                                "user_id": chatId,
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

                        end_time = time.time()
                        latency = round(end_time - start_time, 2)
                        
                        question = ''
                        save_response = save_chat_history(db, target_user_id, question, admin_message, latency)
                        
                        await target_conn["websocket"].send_json({
                            "success": True,
                            "data": admin_message,
                            "from": "admin"
                        })
                        await websocket.send_json({"success": True, "admin_message": admin_message, "user_id": target_user_id})
                    else:
                        await websocket.send_json({"success": False, "error": "User tidak ditemukan atau tidak aktif"})

        except WebSocketDisconnect:
            print(f"{role.capitalize()} {chatId} terputus")            
    
    finally: #gunakan finally untuk memastikan selalu di jalankan.
        active_connections.pop(chatId, None)
        active_agents.pop(chatId, None)
        await asyncio.sleep(0.1)
        await broadcast_active_users()