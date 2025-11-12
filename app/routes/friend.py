from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import ChatRead, ChatCreate, MessageRead, MessageCreate
from ..models import Chat, ChatMember, Friend
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select

router = APIRouter(prefix="/friend", tags=["friend"])

async def is_friend(db, user_id, friend_id):
    result = await db.execute(select(Friend).where(Friend.user_id == user_id).where(Friend.friend_id == friend_id))
    if result.scalars.all():
        return True
    return False


@router.post("/", response_model=ChatRead)
async def create_friend(chat: ChatCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")


    chat_obj = Chat(name=chat.name, is_group=chat.is_group)
    db.add(chat_obj)
    await db.commit()
    await db.refresh(chat_obj)
    return chat_obj

