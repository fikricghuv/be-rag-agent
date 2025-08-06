import redis.asyncio as redis
from core.settings import REDIS_HOST, REDIS_PORT

redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT,
    decode_responses=True 
)

def get_redis_client() -> redis.Redis:
    return redis_client