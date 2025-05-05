import re
import time
import numpy as np
from models.chat_history_model import ChatHistory, ChatHistoryEmbedding
from agno.embedder.openai import OpenAIEmbedder
from sqlalchemy.sql import text
from fastapi import HTTPException

embedder = OpenAIEmbedder()

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

    return {
        "output": result[0], 
        "input_similarity": result[1] or 0, 
        "output_similarity": result[2] or 0
    }

def save_chat_history(db, user_id, question, save_response):
    start_time = time.time()
    save_response = re.sub(r" - Running:.*?\n?", "", save_response, flags=re.MULTILINE)
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

    chat_history_id = chat_history.id

    embedding_question = embedder.get_embedding(question)
    embedding_answer = embedder.get_embedding(save_response)
    embedding_question_array = np.array(embedding_question).tolist()
    embedding_answer_array = np.array(embedding_answer).tolist()

    chat_history_embedding = ChatHistoryEmbedding(
        refidchathistory=chat_history_id,
        embedding_answer=embedding_answer_array,
        embedding_question=embedding_question_array
    )

    db.add(chat_history_embedding)
    db.commit()
    return save_response
