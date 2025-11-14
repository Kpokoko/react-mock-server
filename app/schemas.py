from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- USER ---
class UserCreate(BaseModel):
    username: str
    password: str
    confirmPassword: str
    email: str

class UserAuth(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


# --- COMMENT ---
class CommentCreate(BaseModel):
    postId: int
    content: str


class CommentRead(BaseModel):
    id: int
    postId: int
    userId: int
    username: str
    content: str
    createdAt: datetime


# --- POST ---
class PostCreate(BaseModel):
    content: str
    imgUrl: Optional[str] = None


class PostRead(BaseModel):
    id: int
    user: str
    userId: int
    postTime: datetime
    text: str
    image: str | None
    likes: int
    comments: list[CommentRead] | list[str]

class PostUpdate(BaseModel):
    text: str | None = None
    image: str | None = None


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


# --- IMAGES ---
class ImageRead(BaseModel):
    id: int
    filename: str
    filepath: str


# --- FRIEND ---
class FriendCreate(BaseModel):
    friendId: int

class FriendRead(BaseModel):
    id: int
    user_id: int
    friend_id: int
    status: str