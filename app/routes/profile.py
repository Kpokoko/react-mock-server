from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import UserCreate, UserRead, PostRead, PostCreate, CommentRead
from ..models import User, Post, Comment
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
    posts = await db.execute(select(Post).options(
            selectinload(Post.comments).selectinload(Comment.author),
            selectinload(Post.author),
        )
        .where(Post.author_id == user_id))
    user = result.scalars().first()
    res_post = []
    for post in posts.scalars().all():
        comments_list = [
            CommentRead(
                id=c.id,
                postId=c.post_id,
                userId=c.author_id,
                username=c.author.username,
                content=c.content,
                createdAt=c.created_at
            )
            for c in post.comments
        ]

        res_post.append(
            PostRead(
                id=post.id,
                user=post.author.username,
                userId=post.author.id,
                postTime=post.created_at,
                text=post.content,
                image=post.image_url,
                likes=100,
                comments=comments_list,
            )
        )

    res = {
        "userId": user.id,
        "name": user.username,
        "friendCount": 100,
        "photoCount": 20,
        "subscriberCount": 6,
        "posts": res_post
    }
    return res
