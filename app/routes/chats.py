import datetime
from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import ChatRead, ChatCreate, MessageRead, MessageCreate, ChatSend
from ..models import Chat, Message, ChatMember
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select

router = APIRouter(prefix="/chats", tags=["chats"])

async def is_chat_member(db, user_id, chat_id):
    result = await db.execute(select(ChatMember).where(ChatMember.chat_id == chat_id).where(ChatMember.user_id == user_id))
    if result.scalars.all():
        return True
    return False


@router.post("/", response_model=ChatSend)
async def create_chat(chat: ChatCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_obj = Chat(name=chat.name, is_group=chat.is_group)
    db.add(chat_obj)
    await db.commit()
    await db.refresh(chat_obj)
    return ChatSend(
            name = chat.name,
            preview = '...',
            chatTime = datetime.datetime.utcnow()
        )

@router.get("/{chat_id}", response_model=ChatSend)
async def get_chat(chat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    result = await db.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.desc()).limit(1))
    message = result.scalars().first()
    return ChatSend(
            name = chat.name,
            preview = message.content,
            chatTime = message.created_at
        )

@router.get("/", response_model=List[ChatSend])
async def list_chats(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Chat)
                              .join(ChatMember, ChatMember.chat_id == Chat.id)
                              .where(ChatMember.user_id == user_id))
    chats = result.scalars().all()
    res = []
    for c in chats:
        result = await db.execute(
            select(Message).where(Message.chat_id == c.id).order_by(Message.created_at.desc()).limit(1))
        message = result.scalars().first()
        res.append(ChatSend(
            name = c.name,
            preview = message.content,
            chatTime = message.created_at
        ))
    return res


@router.post("/{chat_id}/messages", response_model=MessageRead)
async def send_message(chat_id: int, msg: MessageCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not is_chat_member(db, user_id, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    message = Message(chat_id=chat_id, sender_id=user_id, content=msg.content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{chat_id}/messages", response_model=List[MessageRead])
async def get_messages(request: Request, chat_id: int, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if not is_chat_member(db, user_id, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
    )
    return result.scalars().all()
