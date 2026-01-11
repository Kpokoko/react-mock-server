from itsdangerous import URLSafeTimedSerializer
from fastapi import Request
from typing import Optional
import redis
from ..config import settings

redis_client = redis.Redis(host="10.130.0.11", port=6379, decode_responses=True)

serializer = URLSafeTimedSerializer(settings.secret_key)
SESSION_TTL = 60 * 60 * 24 * 7

def create_session(user_id: int) -> str:
    token = serializer.dumps(user_id)
    redis_client.set(f"session:{token}", user_id, ex=SESSION_TTL)
    return token

def get_user_id(token: str) -> Optional[int]:
    user_id = redis_client.get(f"session:{token}")
    if user_id:
        return int(user_id)
    return None

def remove_session(token: str):
    redis_client.delete(f"session:{token}")

def get_current_user(request: Request) -> Optional[int]:
    token = request.cookies.get("session_token")
    if token:
        return get_user_id(token)
    return None
