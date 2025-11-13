from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import UserCreate, UserRead, PostRead, PostCreate, PostUpdate
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

    post_obj = Post(author_id=user_id, content=post.content, image_url=post.imgUrl)
    db.add(post_obj)
    await db.commit()
    await db.refresh(post_obj)
    res = PostRead(
        id=post_obj.id,
        user=post_obj.author.username,
        userId=post_obj.author.id,
        postTime=post_obj.created_at,
        text=post_obj.content,
        image=post_obj.image_url,
        likes=100,
        comments=["scam", "scam"],
    )
    return res


@router.get("/", response_model=List[PostRead])
async def list_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post)
                              .order_by(Post.created_at.desc()))

    res = [
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
        for i in result.scalars().all()
    ]
    return res


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id).where(Post.is_published == True))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostRead(
        id=post.id,
        user=post.author.username,
        userId=post.author.id,
        postTime=post.created_at,
        text=post.content,
        image=post.image_url,
        likes=100,
        comments=["scam", "scam"],
    )

@router.post("/{post_id}")
async def update_post(updates: PostUpdate, post_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Post).where(Post.id == post_id).where(Post.author_id == user_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    for field, value in updates.items():
        if field == "text":
            post.content = value
        elif field == "image":
            post.image_url = value

    await db.commit()
    await db.refresh(post)
    return Response(status_code=204)

@router.delete("/{post_id}")
async def delete_post(post_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Post).where(Post.id == post_id).where(Post.author_id == user_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    return Response(status_code=204)

