from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import UserCreate, UserRead, PostRead, PostCreate, CommentRead
from ..models import User, Post, Comment, Friend
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
            selectinload(Post.likes),
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
                likes=len(post.likes) if hasattr(post, 'likes') else 0,
                isLiked=any(getattr(l, 'author_id', None) == user_id for l in post.likes) if hasattr(post, 'likes') else False,
                comments=comments_list,
            )
        )

    # compute friend and subscriber counts
    friends_res = await db.execute(select(Friend).where(Friend.user_id == user.id).where(Friend.status == "accepted"))
    friend_count = len(friends_res.scalars().all())

    subs_res = await db.execute(select(Friend).where(Friend.friend_id == user.id).where(Friend.status == "pending"))
    subscriber_count = len(subs_res.scalars().all())

    res = {
        "userId": user.id,
        "name": user.username,
        "friendCount": friend_count,
        "photoCount": 20,
        "subscriberCount": subscriber_count,
        "posts": res_post
    }
    return res


@router.get("/{user_id}")
async def other_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    posts = await db.execute(select(Post).options(
            selectinload(Post.comments).selectinload(Comment.author),
            selectinload(Post.author),
            selectinload(Post.likes),
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
                likes=len(post.likes) if hasattr(post, 'likes') else 0,
                isLiked=any(getattr(l, 'author_id', None) == user_id for l in post.likes) if hasattr(post, 'likes') else False,
                comments=comments_list,
            )
        )

    friends_res = await db.execute(select(Friend).where(Friend.user_id == user.id).where(Friend.status == "accepted"))
    friend_count = len(friends_res.scalars().all())

    subs_res = await db.execute(select(Friend).where(Friend.friend_id == user.id).where(Friend.status == "pending"))
    subscriber_count = len(subs_res.scalars().all())

    res = {
        "userId": user.id,
        "name": user.username,
        "friendCount": friend_count,
        "photoCount": 20,
        "subscriberCount": subscriber_count,
        "posts": res_post
    }
    return res