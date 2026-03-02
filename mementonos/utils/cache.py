import redis
import base64
from typing import Optional

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def save_master_key(user_id: int, master_key: bytes):
    """Сохраняет мастер-ключ в Redis."""
    key = f"user:{user_id}:master_key"
    redis_client.setex(key, 3600, base64.b64encode(master_key).decode())

def get_master_key(user_id: int) -> Optional[bytes]:
    """Получает мастер-ключ из Redis."""
    key = f"user:{user_id}:master_key"
    data = redis_client.get(key)
    if data:
        return base64.b64decode(data)
    return None