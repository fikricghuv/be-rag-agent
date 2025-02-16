from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
import jwt
import time
from agents.product_information_agent.product_information_agent import call_agent
from config.config_db import config_db
from models.chat_history_model import ChatHistory
from config.settings import SECRET_KEY, ALGORITHM
from sqlalchemy import text
import faiss
import numpy as np
from agno.embedder.ollama import OllamaEmbedder

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
active_connections = {}

# Inisialisasi FAISS sebagai cache retrieval
embedding_dim = 4096  # Sesuaikan dengan model embedding (OLLAMA atau lainnya)
faiss_index = faiss.IndexFlatL2(embedding_dim)  # Menggunakan L2 distance
faiss_responses = {}  # Dictionary untuk menyimpan hasil response terkait dengan embedding

# Inisialisasi embedder
embedder = OllamaEmbedder()  

# Fungsi untuk mencari di FAISS cache sebelum menjalankan agent
def search_cached_answer(user_question, db, similarity_threshold=0.85, limit=1):
    """
    Mencari jawaban yang paling mirip berdasarkan embedding input dan output di PostgreSQL.
    
    - user_question: string pertanyaan user
    - db: koneksi database SQLAlchemy
    - similarity_threshold: batas minimal kesamaan (default 0.85)
    - limit: jumlah jawaban maksimal yang dikembalikan
    """
    user_embedding = embedder.get_embedding(user_question)  # Buat embedding pertanyaan
    embedding_array = np.array(user_embedding).tolist()  # Konversi ke format list agar bisa digunakan di SQL
    
    query = text("""
        SELECT output, 
            1 - (embedding_input::vector <-> %(embedding)s::vector) AS input_similarity,
            1 - (embedding_output::vector <-> %(embedding)s::vector) AS output_similarity
        FROM chat_history
        WHERE (1 - (embedding_input::vector <-> %(embedding)s::vector) > %(threshold)s
            OR 1 - (embedding_output::vector <-> %(embedding)s::vector) > %(threshold)s)
        ORDER BY GREATEST(1 - (embedding_input::vector <-> %(embedding)s::vector), 
                        1 - (embedding_output::vector <-> %(embedding)s::vector)) DESC
        LIMIT %(limit)s;
    """)

    result = db.execute(query, {
        "embedding": embedding_array,
        "threshold": similarity_threshold,
        "limit": limit
    }).fetchone()

    return result[0] if result else None 

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
                    
                    # Cek apakah pertanyaan sudah ada di cache FAISS
                    # cached_response = search_cached_answer(question, db)
                    # print("cached_response : ", cached_response)
                    # if cached_response:
                    #     latency = time.time() - start_time
                    #     embedding_input = embedder.get_embedding(question)   # Embed pertanyaan
                    #     embedding_output = embedder.get_embedding(cached_response)   # Embed jawaban
                    #     embedding_input_array = np.array(embedding_input).tolist()
                    #     embedding_output_array = np.array(embedding_output).tolist()
                    #     chat_history = ChatHistory(
                    #         name=user_id,
                    #         input=question,
                    #         output=cached_response,
                    #         error=None,
                    #         latency=latency,
                    #         agent_name="product information agent",
                    #         embedding_output=embedding_output_array,
                    #         embedding_input=embedding_input_array,
                    #     )
                    #     db.add(chat_history)
                    #     db.commit()
                    #     await websocket.send_json({"success": True, "data": cached_response})
                    #     return  # Stop execution jika hasil ditemukan dalam cache
                    
                    agent = call_agent(user_id, user_id)
                    response = agent.run(question)
                    save_response = response.content if isinstance(response.content, str) else str(response.content)
                    
                    latency = time.time() - start_time

                    embedding_input = embedder.get_embedding(question)   # Embed pertanyaan
                    embedding_output = embedder.get_embedding(save_response)   # Embed jawaban
                    embedding_input_array = np.array(embedding_input).tolist()
                    embedding_output_array = np.array(embedding_output).tolist()

                    # Simpan ke database
                    chat_history = ChatHistory(
                        name=user_id,
                        input=question,
                        output=save_response,
                        error=None,
                        latency=latency,
                        agent_name="product information agent",
                        # embedding_output=embedding_output_array,
                        # embedding_input=embedding_input_array,
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
                        # embedding_output=[],
                        # embedding_input=[],
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