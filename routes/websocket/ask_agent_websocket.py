from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
import jwt
import time
from agents.customer_service_team.customer_service_team import call_agent
from config.config_db import config_db
from models.chat_history_model import ChatHistory, ChatHistoryEmbedding
from config.settings import SECRET_KEY, ALGORITHM
from sqlalchemy import text
import numpy as np
from agno.embedder.ollama import OllamaEmbedder
from agno.embedder.openai import OpenAIEmbedder
from sqlalchemy.sql import text

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
active_connections = {}

# Inisialisasi FAISS sebagai cache retrieval
embedding_dim = 1536  # Sesuaikan dengan model embedding (OLLAMA atau lainnya)

# Inisialisasi embedder
embedder = OpenAIEmbedder()  

def search_cached_answer(user_question, db, similarity_threshold=0.85, limit=1):
    """
    Mencari jawaban yang paling mirip berdasarkan embedding input dan output di PostgreSQL.

    - user_question: string pertanyaan user
    - db: koneksi database SQLAlchemy
    - similarity_threshold: batas minimal kesamaan (default 0.85)
    - limit: jumlah jawaban maksimal yang dikembalikan
    """
    user_embedding = embedder.get_embedding(user_question)  # Dapatkan embedding pertanyaan

    query = text("""
        SELECT ch.output,
            1 - (che.embedding_question <-> :embedding) AS input_similarity,
            1 - (che.embedding_answer <-> :embedding) AS output_similarity
        FROM ai.chat_history_embedding che
        JOIN ai.chat_history ch ON ch.id = che.refidchathistory
        WHERE (1 - (che.embedding_question <-> :embedding) > :threshold
            OR 1 - (che.embedding_answer <-> :embedding) > :threshold)
        ORDER BY GREATEST(1 - (che.embedding_question <-> :embedding), 
                        1 - (che.embedding_answer <-> :embedding)) DESC
        LIMIT :limit;
    """)

    results = db.execute(query, {
        "embedding": user_embedding,  # Tidak perlu diubah formatnya
        "threshold": similarity_threshold,
        "limit": limit
    }).fetchall()

    return results[0][0] if results else None  

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
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("user_id")
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
                    
                    # Cek apakah pertanyaan sudah ada di cache FAISS
                    cached_response = search_cached_answer(question, db)

                    if cached_response and cached_response["output"]:  # Pastikan response tidak kosong
                        input_similarity = cached_response["input_similarity"]
                        output_similarity = cached_response["output_similarity"]

                        # Jika tingkat kesamaan terlalu rendah, jangan gunakan cache
                        if max(input_similarity, output_similarity) < 0.85:
                            cached_response = None  

                    if cached_response:
                        latency = time.time() - start_time
                        embedding_input = embedder.get_embedding(question)   # Embed pertanyaan
                        embedding_output = embedder.get_embedding(cached_response["output"])   # Embed jawaban

                        # Simpan ke chat history
                        chat_history = ChatHistory(
                            name=user_id,
                            input=question,
                            output=cached_response["output"],
                            error=None,
                            latency=latency,
                            agent_name="product information agent",
                        )
                        db.add(chat_history)
                        db.commit()

                        # Kirim respons ke frontend
                        await websocket.send_json({
                            "success": True,
                            "data": cached_response["output"],
                            "similarity": max(input_similarity, output_similarity)
                        })
                        return  # Stop execution jika hasil ditemukan dalam cache

                    
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

                    # Ambil ID yang baru dimasukkan untuk referensi di tabel embedding
                    chat_history_id = chat_history.id  
                    print("chat_history_id : ", chat_history_id)

                    embedding_input = embedder.get_embedding(question)   # Embed pertanyaan
                    embedding_output = embedder.get_embedding(save_response)   # Embed jawaban
                    embedding_input_array = np.array(embedding_input).tolist()
                    embedding_output_array = np.array(embedding_output).tolist()

                    chat_history_embedding = ChatHistoryEmbedding(
                        refidchathistory=chat_history_id,
                        embedding_answer=embedding_output_array,
                        embedding_question=embedding_input_array
                    )

                    db.add(chat_history_embedding)
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