from itsdangerous import URLSafeTimedSerializer
from fastapi import Request, Response
from typing import Optional
from ..config import settings

sessions = {}

serializer = URLSafeTimedSerializer(settings.secret_key)

def create_session(user_id: int) -> str:
    token = serializer.dumps(user_id)
    sessions[token] = user_id
    return token

def get_user_id(token: str) -> Optional[int]:
    return sessions.get(token)

def remove_session(token: str):
    sessions.pop(token, None)

def get_current_user(request: Request) -> Optional[int]:
    token = request.cookies.get("session_token")
    if token:
        return get_user_id(token)
    return None
