from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import UserCreate, UserRead, PostRead, PostCreate, CommentRead, UserUpdateAvatar, GalleryItem
from ..models import User, Post, Comment, Friend, ImageUser
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select
from passlib.hash import bcrypt
from ..common import hash_password, check_password

router = APIRouter(prefix="/gallery", tags=["gallery"])

@router.get("/{user_id}", response_model=list[GalleryItem])
async def get_gallery(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = get_current_user(request)
    if current_user != user_id:
        result = await db.execute(select(ImageUser)
                                  .where(and_(ImageUser.user_id == user_id, ImageUser.private == False))
                                  .options(selectinload(ImageUser.image)))
    else:
        result = await db.execute(select(ImageUser)
                                  .where(ImageUser.user_id == user_id)
                                  .options(selectinload(ImageUser.image)))
    images = result.scalars().all()
    return [GalleryItem(id=i.id, url=i.image.filepath) for i in images]