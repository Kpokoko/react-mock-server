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

class UserUpdateAvatar(BaseModel):
    avatarUrl: str


# --- COMMENT ---
class CommentCreate(BaseModel):
    postId: int
    content: str


class CommentRead(BaseModel):
    id: int
    postId: int
    userId: int
    username: str
    avatarUrl: str | None = None
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
    avatarUrl: str | None
    likes: int
    isLiked: bool
    comments: list[CommentRead] | list[str]

class PostUpdate(BaseModel):
    text: str | None = None
    image: str | None = None


# --- CHAT ---
class ChatCreate(BaseModel):
    name: str | None = None
    members: list[int] | None = None


class ChatRead(BaseModel):
    id: int
    name: Optional[str] = None
    is_group: bool
    class Config:
        orm_mode = True

class ChatMemberSend(BaseModel):
    id: int
    username: str

class ChatSend(BaseModel):
    id: int
    name: str
    preview: str
    chatTime: datetime
    chatBadge: str | None = None
    chatMembers: list[ChatMemberSend] | None = None


# --- MESSAGE ---
class MessageCreate(BaseModel):
    content: str
    imageUrl: str | None = None


class MessageRead(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    created_at: datetime
    class Config:
        orm_mode = True


class MessageSend(BaseModel):
    direction: str
    name: str
    message: str
    imageUrl: str | None = None
    time: datetime
    avatarUrl: str | None = None


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


# --- LIKE ---
class LikeCreate(BaseModel):
    postId: int


class LikeRead(BaseModel):
    id: int
    postId: int
    authorId: int
    createdAt: datetime

    class Config:
        orm_mode = True


# --- CHAT MEMBER ---
class ChatMemberAdd(BaseModel):
    members: list[int]


# --- FRIEND STATUS ---
class FriendStatus(BaseModel):
    status: str


# --- SETTINGS ---
class SettingsCreate(BaseModel):
    notifications_enabled: Optional[bool] = True
    theme: Optional[str] = "light"


class SettingsRead(BaseModel):
    user_id: int
    notifications_enabled: bool
    theme: str

    class Config:
        orm_mode = True


class SettingsUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    theme: Optional[str] = None

class GalleryItem(BaseModel):
    id: int
    url: str
