from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- USER ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

# --- POST ---
class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None


class PostRead(BaseModel):
    id: int
    author_id: int
    content: str
    image_url: Optional[str]
    created_at: datetime
    class Config:
        orm_mode = True


# --- CHAT ---
class ChatCreate(BaseModel):
    name: str
    is_group: bool = False


class ChatRead(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    class Config:
        orm_mode = True


# --- MESSAGE ---
class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    created_at: datetime
    class Config:
        orm_mode = True