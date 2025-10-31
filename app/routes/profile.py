from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import UserCreate, UserRead, PostRead, PostCreate
from ..models import User, Post
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select
from passlib.hash import bcrypt
from ..common import hash_password, check_password

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/")
async def profile(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(User).where(User.id == user_id))
    posts = await db.execute(select(Post).where(Post.author_id == user_id))
    user = result.scalars().first()
    res = {
        "userId"
        "name": user.username,
        "friendCount": 100,
        "photoCount": 20,
        "subscriberCount": 6,
        "posts": [
            PostRead(
                id = i.id,
                user = i.author.username,
                userId = i.author.id,
                postTime = i.created_at,
                text = i.content,
                image = i.image_url,
                likes = 100,
                comments = ["scam", "scam"],
            )
            for i in posts.scalars().all()
        ]
    }
    return res
