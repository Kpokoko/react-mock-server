from typing import List

from fastapi import APIRouter, Depends, Request, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db import get_db
from ..models import Like, Post
from ..schemas import LikeCreate, LikeRead
from ..services.session_manager import get_current_user

router = APIRouter(prefix="/likes", tags=["likes"])


@router.post("/", response_model=LikeRead)
async def create_like(
    data: LikeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Post).where(Post.id == data.postId))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Prevent duplicate likes from the same user
    result = await db.execute(
        select(Like).where(Like.post_id == data.postId, Like.author_id == user_id)
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    like = Like(post_id=data.postId, author_id=user_id)
    db.add(like)
    await db.commit()
    await db.refresh(like)

    return LikeRead(
        id=like.id,
        postId=like.post_id,
        authorId=like.author_id,
        createdAt=like.created_at,
    )


@router.get("/{post_id}", response_model=list[LikeRead])
async def list_likes(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Like).where(Like.post_id == post_id).order_by(Like.created_at.desc())
    )
    likes = result.scalars().all()

    return [
        LikeRead(
            id=l.id,
            postId=l.post_id,
            authorId=l.author_id,
            createdAt=l.created_at,
        )
        for l in likes
    ]


@router.delete("/{post_id}")
async def delete_like(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Like).where(Like.post_id == post_id, Like.author_id == user_id)
    )
    like = result.scalars().first()

    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    await db.delete(like)
    await db.commit()

    return Response(status_code=204)
