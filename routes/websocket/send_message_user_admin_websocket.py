from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import jwt
import time
import re
from config.config_db import config_db
from models.chat_history_model import ChatHistory, ChatHistoryEmbedding
# from models.chat_history_embedding_model import ChatHistoryEmbedding
from config.settings import SECRET_KEY, ALGORITHM, SECRET_KEY_ADMIN
from agents.customer_service_agent.customer_service_agent import call_agent
from middleware.verify_token_websocket import verify_token
from agno.embedder.openai import OpenAIEmbedder
from sqlalchemy.sql import text
import numpy as np
import asyncio

router = APIRouter()
active_connections = {}  # Menyimpan {user_id: {"websocket": WebSocket, "role": "user" atau "admin"}}
embedding_dim = 1536  # Sesuaikan dengan model embedding (OLLAMA atau lainnya)

# Inisialisasi embedder
embedder = OpenAIEmbedder() 
active_agents = {}

def get_team(user_id, role):
    if user_id not in active_agents:
        active_agents[user_id] = call_agent(user_id, role)
    return active_agents[user_id]

# async def call_agent_async(user_id, role, question):
#     agent = get_agent(user_id, role)
#     loop = asyncio.get_event_loop()
#     response = await loop.run_in_executor(None, agent.run, question)
#     return response

def search_cached_answer(user_question, db, similarity_threshold=0.85, limit=1):
    user_embedding = embedder.get_embedding(user_question)

    query = text("""
        SELECT ch.output,
            1 - (che.embedding_question <-> CAST(:embedding AS vector)) AS input_sim,
            1 - (che.embedding_answer <-> CAST(:embedding AS vector)) AS output_sim
        FROM ai.chat_history_embedding che
        JOIN ai.chat_history ch ON ch.id = che.refidchathistory
        WHERE (1 - (che.embedding_question <-> CAST(:embedding AS vector)) > :threshold
            OR 1 - (che.embedding_answer <-> CAST(:embedding AS vector)) > :threshold)
        ORDER BY input_sim DESC, output_sim DESC
        LIMIT :limit;
    """)

    result = db.execute(query, {
        "embedding": user_embedding,
        "threshold": similarity_threshold,
        "limit": limit
    }).fetchone()

    if not result:
        return None

    if result:
        return {
            "output": result[0], 
            "input_similarity": result[1] or 0, 
            "output_similarity": result[2] or 0
            }
    return None
 
async def broadcast_active_users():
    active_users_copy = active_connections.copy()  # Buat salinan dictionary
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
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(config_db)
):
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
                    start_time = time.time()
                    print(f"User {user_id} mengirim pesan:", question)

                    # Cari jawaban di cache terlebih dahulu
                    # cached_response = search_cached_answer(question, db)

                    # # Pastikan cached_response memiliki format yang benar
                    # if isinstance(cached_response, list): 
                    #     cached_response = cached_response[0] if cached_response else {}

                    # if cached_response and isinstance(cached_response, dict) and cached_response.get("output"):

                    #     input_similarity = cached_response.get("input_similarity", 0)
                    #     output_similarity = cached_response.get("output_similarity", 0)

                    #     # Jika tingkat kesamaan terlalu rendah, jangan gunakan cache
                    #     if max(input_similarity, output_similarity) < 0.85:
                    #         cached_response = None  

                    # if cached_response:
                    #     latency = time.time() - start_time

                    #     # Simpan ke chat history
                    #     chat_history = ChatHistory(
                    #         name=user_id,
                    #         input=question,
                    #         output=cached_response["output"],
                    #         error=None,
                    #         latency=latency,
                    #         agent_name="product information agent",
                    #     )
                    #     db.add(chat_history)
                    #     db.commit()

                    #     # Kirim respons ke frontend
                    #     await websocket.send_json({
                    #         "success": True,
                    #         "data": cached_response["output"],
                    #         "similarity": max(input_similarity, output_similarity)
                    #     })
                    #     return  # Stop execution jika hasil ditemukan dalam cache
                    
                    team = get_team(user_id, role)
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(None, team.run, question)

                    save_response = response.content
                    response_metrics = response.metrics
                    if not isinstance(save_response, str):
                        save_response = str(save_response)
                        

                    print("ini adalah content metrics: " + str(response_metrics))
                    print("save response :" , save_response)
                    # save_response = response.content if isinstance(response.content, str) else str(response.content)
                    save_response = re.sub(r" - Running:\s*search_knowledge_base\(query=.*?\)\\n?", "", save_response)
                    save_response = re.sub(r" - Running:\s*\w+\(.*?\)\n?", "", save_response)
                    save_response = re.sub(r" - Running:.*?\(.*?\)\n?", "", save_response, flags=re.MULTILINE)

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
                    # db.flush()
                    db.commit()

                    # Ambil ID yang baru dimasukkan untuk referensi di tabel embedding
                    chat_history_id = chat_history.id 

                    embedding_question = embedder.get_embedding(question)   # Embed pertanyaan
                    embedding_answer = embedder.get_embedding(save_response)   # Embed jawaban
                    embedding_question_array = np.array(embedding_question).tolist()
                    embedding_answer_array = np.array(embedding_answer).tolist()

                    chat_history_embedding = ChatHistoryEmbedding(
                        refidchathistory=chat_history_id,
                        embedding_answer=embedding_answer_array,
                        embedding_question=embedding_question_array
                    )

                    db.add(chat_history_embedding)
                    db.commit()

                    try:
                        await websocket.send_json({"success": True, "data": save_response})
                    except Exception as e:
                        print(f"⚠️ Gagal mengirim pesan ke user {user_id}: {e}")

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
        finally:
            active_connections.pop(user_id, None)
            active_agents.pop(user_id, None)
            await asyncio.sleep(0.1)
            await broadcast_active_users()

    except jwt.ExpiredSignatureError:
        print({"error": "Token telah kedaluwarsa"})
        await websocket.close(code=4001, reason="TokenExpired")
    except jwt.InvalidTokenError:
        print({"error": "Token tidak valid"})
        await websocket.close(code=4001, reason="TokenExpired")

    except HTTPException as e:
        print({"error": str(e.detail)})

    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
