from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserCreate, UserRead, PostRead, PostCreate
from ..models import User, Post
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select
from passlib.hash import bcrypt
from ..common import hash_password, check_password

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostRead)
async def create_post(post: PostCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    post_obj = Post(author_id=user_id, content=post.content, image_url=post.image_url)
    db.add(post_obj)
    await db.commit()
    await db.refresh(post_obj)
    return post_obj


@router.get("/", response_model=List[PostRead])
async def list_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    return result.scalars().all()


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
