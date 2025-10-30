from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserCreate, UserRead, UserAuth
from ..models import User
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select
from passlib.hash import bcrypt
from ..common import hash_password, check_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead)
async def register(user: UserCreate, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    existing = result.scalars().first()
    if user.password != user.passwordRep:
        raise HTTPException(status_code=400, detail="Password not correct")
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user_obj = User(username=user.username, password_hash=hash_password(user.password))
    db.add(user_obj)
    token = create_session(user_obj.id)
    response.set_cookie(key="session_token", value=token, httponly=True)
    await db.commit()
    await db.refresh(user_obj)
    return user_obj

@router.post("/login")
async def login(user: UserAuth, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalars().first()
    if not db_user or not check_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session(db_user.id)
    response.set_cookie(key="session_token", value=token, httponly=True)
    return {"message": "Logged in"}

@router.get("/profile")
async def profile(request: Request, db: AsyncSession = Depends(get_db)):
    # user_id = get_current_user(request)
    # if not user_id:
    #     raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalars().first()
    res = {
        "name": "aboba",
        "friendCount": 100,
        "photoCount": 20,
        "subscriberCount": 6,
        "posts": [
            {
                "id": 2,
                "user": "aboba",
                "postTime": "2025-10-13T09:45:00.000Z",
                "text": "scam",
                "image": "/images/2.png",
                "likes": 8,
                "comments": ['Отстой']
            }
        ]
    }
    return res
