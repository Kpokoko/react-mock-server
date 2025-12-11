import datetime
from typing import List

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import ChatCreate, MessageRead, MessageCreate, ChatSend, MessageSend, ChatMemberAdd
from ..models import Chat, Message, ChatMember, User
from ..db import get_db
from ..services.session_manager import get_current_user
from sqlalchemy.future import select
from sqlalchemy import func

router = APIRouter(prefix="/chats", tags=["chats"])

async def is_chat_member(db, user_id, chat_id):
    result = await db.execute(select(ChatMember).where(ChatMember.chat_id == chat_id).where(ChatMember.user_id == user_id))
    if result.scalars().all():
        return True
    return False


@router.post("/", response_model=ChatSend)
async def create_chat(chat: ChatCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_obj = Chat(name=chat.name, is_group=False)
    db.add(chat_obj)
    await db.commit()
    await db.refresh(chat_obj)

    # Add the current user as a ChatMember
    chat_member = ChatMember(chat_id=chat_obj.id, user_id=user_id)
    db.add(chat_member)
    await db.commit()

    return ChatSend(
        id=chat_obj.id,
        name=chat.name if chat.name else "Undefined",
        preview="...",
        chatTime=datetime.datetime.utcnow(),
    )


@router.post("/private", response_model=ChatSend)
async def create_private_chat(member: ChatMemberAdd, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a private chat between the current user and another user."""
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user == member.userId:
        raise HTTPException(status_code=400, detail="Cannot create a private chat with yourself")

    # Check if the other user exists
    result = await db.execute(select(User).where(User.id == member.userId))
    other_user = result.scalars().first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(Chat.is_group == False)
        .where(ChatMember.user_id.in_([current_user, member.userId]))
        .group_by(Chat.id)
        .having(func.count(ChatMember.user_id) == 2)
    )
    existing_chat = result.scalars().first()
    if existing_chat:
        raise HTTPException(status_code=400, detail="Private chat already exists")

    # Create the private chat
    chat = Chat(name=None, is_group=False)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    # Add chat members
    chat_members = [
        ChatMember(chat_id=chat.id, user_id=current_user),
        ChatMember(chat_id=chat.id, user_id=member.userId),
    ]
    db.add_all(chat_members)
    await db.commit()

    return ChatSend(
        id=chat.id,
        name=str(member.userId),
        preview="...",
        chatTime=datetime.datetime.utcnow(),
    )


@router.get("/{chat_id}", response_model=ChatSend)
async def get_chat(chat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not await is_chat_member(db, user_id, chat_id):
        raise HTTPException(status_code=404, detail="Not authenticated")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    result = await db.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.desc()).limit(1))
    message = result.scalars().first()

    # Fetch chat members
    result = await db.execute(select(ChatMember).where(ChatMember.chat_id == chat_id).options(selectinload(ChatMember.user)))
    members = result.scalars().all()
    member_names = [m.user.username for m in members]

    mem = None
    for m in members:
        if m.user.id != user_id:
            mem = m.user

    if not chat.is_group and mem:
        name = mem.username
    else:
        name = chat.name

    return ChatSend(
        id=chat.id,
        name=name if name else "Undefined",
        preview=message.content if message else "...",
        chatTime=message.created_at if message else datetime.datetime.utcnow(),
        chatMembers=member_names,
    )


@router.get("/", response_model=List[ChatSend])
async def list_chats(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Chat)
                              .join(ChatMember, ChatMember.chat_id == Chat.id)
                              .where(ChatMember.user_id == user_id))
    chats = result.scalars().all()
    res = []
    for c in chats:
        result = await db.execute(
            select(Message).where(Message.chat_id == c.id).order_by(Message.created_at.desc()).limit(1))
        message = result.scalars().first()

        # Fetch chat members
        result = await db.execute(select(ChatMember).where(ChatMember.chat_id == c.id).options(selectinload(ChatMember.user)))
        members = result.scalars().all()
        member_names = [m.user.username for m in members]

        mem = None
        for m in members:
            if m.user.id != user_id:
                mem = m.user

        if not c.is_group and mem:
            name = mem.username
        else:
            name = c.name

        res.append(ChatSend(
            id=c.id,
            name=name if name else "Undefined",
            preview=message.content if message else "...",
            chatTime=message.created_at if message else datetime.datetime.utcnow(),
            chatMembers=member_names,
        ))
    return res


@router.post("/{chat_id}/messages", response_model=MessageRead)
async def send_message(chat_id: int, msg: MessageCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not is_chat_member(db, user_id, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    message = Message(chat_id=chat_id, sender_id=user_id, content=msg.content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{chat_id}/messages", response_model=List[MessageSend])
async def get_messages(request: Request, chat_id: int, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if not is_chat_member(db, user_id, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.sender))
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc()
        )
    )
    messages = result.scalars().all()
    res = []
    for m in messages:
        direction = 'recieved'
        if user_id == m.sender_id:
            direction = 'send'
        res.append(MessageSend(
            direction=direction,
            name=m.sender.username,
            message=m.content,
            time=m.created_at,
        ))
    return res


@router.post("/{chat_id}/members")
async def add_chat_member(chat_id: int, member: ChatMemberAdd, request: Request, db: AsyncSession = Depends(get_db)):
    """Add a new member to an existing chat."""
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify the chat exists
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Verify the current user is a member of the chat
    if not await is_chat_member(db, current_user, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Verify the user to be added exists
    result = await db.execute(select(User).where(User.id == member.userId))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user is already a member of the chat
    result = await db.execute(select(ChatMember).where(ChatMember.chat_id == chat_id).where(ChatMember.user_id == member.userId))
    existing_member = result.scalars().first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of the chat")

    # Add the user as a new chat member
    new_member = ChatMember(chat_id=chat_id, user_id=member.userId)
    db.add(new_member)
    await db.commit()

    return {"message": "User added to chat successfully"}


@router.delete("/{chat_id}/leave")
async def leave_chat(chat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Allow the current user to leave a chat."""
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify the chat exists
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Verify the user is a member of the chat
    result = await db.execute(select(ChatMember).where(ChatMember.chat_id == chat_id).where(ChatMember.user_id == user_id))
    chat_member = result.scalars().first()
    if not chat_member:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    # Remove the user from the chat
    await db.delete(chat_member)
    await db.commit()

    return {"message": "You have left the chat successfully"}
