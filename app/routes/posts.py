from typing import List

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import PostRead, PostCreate, PostUpdate, CommentRead
from ..models import Post, Comment
from ..db import get_db
from ..services.session_manager import get_current_user
from sqlalchemy.future import select

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
        comments=[],
    )
    return res


@router.get("/", response_model=List[PostRead])
async def list_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post)
        .options(
            selectinload(Post.comments).selectinload(Comment.author),
            selectinload(Post.author),
        )
        .order_by(Post.created_at.desc())
    )

    posts = result.scalars().all()

    res = []
    for post in posts:
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

        res.append(
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

    return res


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id).where(Post.is_published == True).options(selectinload(Post.comments)))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
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
    return PostRead(
        id=post.id,
        user=post.author.username,
        userId=post.author.id,
        postTime=post.created_at,
        text=post.content,
        image=post.image_url,
        likes=100,
        comments=comments_list,
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

