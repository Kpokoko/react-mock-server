from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import CommentRead, CommentCreate
from ..models import User, Post, Comment
from ..db import get_db
from ..services.session_manager import get_current_user
from sqlalchemy.future import select

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentRead)
async def create_comment(
    data: CommentCreate,
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

    comment = Comment(
        post_id=data.postId,
        author_id=user_id,
        content=data.content,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    result_user = await db.execute(select(User).where(User.id == user_id))
    user = result_user.scalars().first()

    return CommentRead(
        id=comment.id,
        postId=comment.post_id,
        userId=user.id,
        username=user.username,
        content=comment.content,
        createdAt=comment.created_at,
    )


@router.get("/{post_id}", response_model=list[CommentRead])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
    )
    result = await db.execute(query)
    comments = result.scalars().all()

    return [
        CommentRead(
            id=c.id,
            postId=c.post_id,
            userId=c.author.id,
            username=c.author.username,
            content=c.content,
            createdAt=c.created_at,
        )
        for c in comments
    ]


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(query)
    comment = result.scalars().first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete this comment")

    await db.delete(comment)
    await db.commit()

    return Response(status_code=204)