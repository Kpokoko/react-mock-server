import datetime
from typing import List

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas import ChatCreate, MessageRead, MessageCreate, ChatSend, MessageSend, ChatMemberAdd, ChatMemberSend, \
    ChatMemberAdd2
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

    chat_obj = Chat(name=chat.name, is_group=True)
    db.add(chat_obj)
    await db.commit()
    await db.refresh(chat_obj)

    # Add the current user as a ChatMember
    chat_members = [ChatMember(chat_id=chat_obj.id, user_id=user_id)]

    # Add additional members if provided
    users = None
    if chat.members:
        result = await db.execute(select(User).where(User.id.in_(chat.members)))
        users = result.scalars().all()
        if len(users) != len(chat.members):
            raise HTTPException(status_code=404, detail="One or more users not found")

        for member_id in chat.members:
            if member_id != user_id:  # Avoid adding the current user twice
                chat_members.append(ChatMember(chat_id=chat_obj.id, user_id=member_id))

    db.add_all(chat_members)
    await db.commit()

    return ChatSend(
        id=chat_obj.id,
        name=chat.name if chat.name else "Undefined",
        preview="...",
        chatTime=datetime.datetime.utcnow(),
        chatMembers=None,
    )


@router.post("/private", response_model=ChatSend)
async def create_private_chat(member: ChatMemberAdd2, request: Request, db: AsyncSession = Depends(get_db)):
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
    member_names = [ChatMemberSend(
        id = m.user.id,
        username = m.user.username,
        avatarUrl = m.user.avatar_url
    ) for m in members]

    mem = None
    for m in members:
        if m.user.id != user_id:
            mem = m.user

    if not chat.is_group and mem:
        name = mem.username
        chat_badge = mem.avatar_url
    else:
        name = chat.name
        chat_badge = chat.avatar_url

    return ChatSend(
        id=chat.id,
        name=name if name else "Undefined",
        preview=message.content if message else "...",
        chatBadge=chat_badge,
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
        member_names = [ChatMemberSend(
            id = m.user.id,
            username = m.user.username,
            avatarUrl = m.user.avatar_url
        ) for m in members]

        mem = None
        for m in members:
            if m.user.id != user_id:
                mem = m.user

        if not c.is_group and mem:
            name = mem.username
            chat_badge = mem.avatar_url
        else:
            name = c.name
            chat_badge = c.avatar_url

        res.append(ChatSend(
            id=c.id,
            name=name if name else "Undefined",
            preview=message.content if message else "...",
            chatBadge=chat_badge,
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

    if not await is_chat_member(db, user_id, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    message = Message(chat_id=chat_id, sender_id=user_id, content=msg.content, attachment_url=msg.imageUrl)
    db.add(message)
    await db.commit()

    # Ensure sender is loaded for broadcasting
    result = await db.execute(
        select(Message).options(selectinload(Message.sender)).where(Message.id == message.id)
    )
    full_message = result.scalars().first()

    # Broadcast to chat members (best-effort; failures won't break the request)
    try:
        from .websocket import manager
        if full_message:
            await manager.broadcast_chat_message(db, full_message)
    except Exception:
        # don't block sending on ws errors
        pass

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
    if not await is_chat_member(db, user_id, chat_id):
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
            imageUrl=m.attachment_url,
            avatarUrl=m.sender.avatar_url
        ))
    return res


@router.post("/{chat_id}/members")
async def add_chat_member(
    chat_id: int,
    members: ChatMemberAdd,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Add new members to an existing chat."""
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Check current user is a chat member
    if not await is_chat_member(db, current_user, chat_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not members.members:
        return {"message": "No users to add"}

    # Load users
    result = await db.execute(
        select(User).where(User.id.in_(members.members))
    )
    users = result.scalars().all()

    if len(users) != len(set(members.members)):
        raise HTTPException(status_code=404, detail="One or more users not found")

    # Get existing chat members
    result = await db.execute(
        select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
    )
    existing_user_ids = set(result.scalars().all())

    new_members = []
    for user in users:
        if user.id == current_user:
            continue  # do not add yourself
        if user.id in existing_user_ids:
            continue  # already in chat

        new_members.append(
            ChatMember(chat_id=chat_id, user_id=user.id)
        )

    if not new_members:
        return {"message": "No new users were added"}

    db.add_all(new_members)
    await db.commit()

    return {"message": "Users added to chat successfully"}



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

    if not chat.is_group:
        await db.delete(chat)

    # Remove the user from the chat
    else:
        await db.delete(chat_member)
    await db.commit()

    return {"message": "You have left the chat successfully"}
