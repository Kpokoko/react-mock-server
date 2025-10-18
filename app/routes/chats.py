from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import ChatRead, ChatCreate, MessageRead, MessageCreate
from ..models import Chat, Message
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=ChatRead)
async def create_chat(chat: ChatCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_obj = Chat(name=chat.name, is_group=chat.is_group)
    db.add(chat_obj)
    await db.commit()
    await db.refresh(chat_obj)
    return chat_obj


@router.get("/", response_model=List[ChatRead])
async def list_chats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat))
    return result.scalars().all()


@router.post("/{chat_id}/messages", response_model=MessageRead)
async def send_message(chat_id: int, msg: MessageCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Проверим, что чат существует
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    message = Message(chat_id=chat_id, sender_id=user_id, content=msg.content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{chat_id}/messages", response_model=List[MessageRead])
async def get_messages(chat_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
    )
    return result.scalars().all()
