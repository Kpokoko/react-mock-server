from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import FriendCreate, FriendRead, FriendStatus
from ..models import Friend, User
from ..db import get_db
from ..services.session_manager import create_session, get_current_user
from sqlalchemy.future import select

router = APIRouter(prefix="/friend", tags=["friend"])

async def get_friend(db, user_id, friend_id):
    result = await db.execute(select(Friend).where(Friend.user_id == user_id).where(Friend.friend_id == friend_id))
    friend = result.scalars().first()
    return friend


@router.post("/", response_model=FriendRead)
async def create_friend(friend: FriendCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user_id == friend.friendId:
        raise HTTPException(status_code=400)

    user = await db.execute(select(User).where(User.id == friend.friendId))
    if not user.scalars().first():
        raise HTTPException(status_code=400)

    post_friend = await get_friend(db, user_id, friend.friendId)
    my_friend = await get_friend(db, friend.friendId, user_id)

    if post_friend or my_friend and my_friend.status == "accepted":
        raise HTTPException(status_code=400, detail="Request has already been sent")

    if my_friend:
        friend_obj = Friend(user_id=user_id, friend_id=friend.friendId, status="accepted")
        my_friend.status = "accepted"
    else:
        friend_obj = Friend(user_id=user_id, friend_id=friend.friendId, status="pending")

    db.add(friend_obj)
    await db.commit()
    await db.refresh(friend_obj)
    return friend_obj

@router.delete("/{friend_id}", status_code=204)
async def delete_friend(friend_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    friend_link = await get_friend(db, user_id, friend_id)
    reverse_link = await get_friend(db, friend_id, user_id)

    if not friend_link and not reverse_link:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if friend_link:
        await db.delete(friend_link)
    if reverse_link:
        await db.delete(reverse_link)

    await db.commit()
    return Response(status_code=204)


@router.get("/{user_id}", response_model=list[FriendRead])
async def list_friends(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # current_user = get_current_user(request)
    # if not current_user:
    #     raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Friend).where(Friend.user_id == user_id).where(Friend.status == "accepted")
    )
    friends = result.scalars().all()

    return [
        FriendRead(id=f.id, user_id=f.user_id, friend_id=f.friend_id, status=f.status)
        for f in friends
    ]


@router.get("/following/{user_id}", response_model=list[FriendRead])
async def list_following(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # current_user = get_current_user(request)
    # if not current_user:
    #     raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Friend).where(Friend.friend_id == user_id).where(Friend.status == "pending")
    )
    subs = result.scalars().all()

    return [
        FriendRead(id=s.id, user_id=s.friend_id, friend_id=s.user_id, status=s.status)
        for s in subs
    ]

@router.get("/requests/{user_id}", response_model=list[FriendRead])
async def list_requests(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # current_user = get_current_user(request)
    # if not current_user:
    #     raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Friend).where(Friend.user_id == user_id).where(Friend.status == "pending")
    )
    subs = result.scalars().all()

    return [
        FriendRead(id=s.id, user_id=s.user_id, friend_id=s.friend_id, status=s.status)
        for s in subs
    ]

@router.get("/status/{user_id}/{friend_id}", response_model=FriendStatus)
async def get_friendship_status(user_id: int, friend_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Friend).where(Friend.user_id == user_id, Friend.friend_id == friend_id)
    )
    result2 = await db.execute(
        select(Friend).where(Friend.user_id == user_id, Friend.friend_id == friend_id)
    )
    friend = result.scalars().first()
    friend2 = result2.scalars().first()

    status = None
    if friend:
        status = friend.status

    status2 = None
    if friend2:
        status2 = friend2.status
    
    if status == 'accepted':
        return FriendStatus(status="friends")
    
    elif status == 'pending':
        return FriendStatus(status="following")
    
    elif status2 == 'pending':
        return FriendStatus(status="requested")
    else:
        return FriendStatus(status="none")

