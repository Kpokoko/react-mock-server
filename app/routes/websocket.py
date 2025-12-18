import asyncio
import json
from typing import Dict, Set, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models import ChatMember, User, Message
from ..services.session_manager import get_user_id

router = APIRouter(prefix="/ws", tags=["websocket"])  # optional prefix for documentation

class ConnectionManager:
    def __init__(self):
        # Map user_id -> set of WebSocket connections
        self.active_connections: Dict[Optional[int], Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        token = websocket.cookies.get("session_token")
        user_id = get_user_id(token) if token else None
        async with self._lock:
            conns = self.active_connections.setdefault(user_id, set())
            conns.add(websocket)
        return user_id

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            for user_id, conns in list(self.active_connections.items()):
                if websocket in conns:
                    conns.remove(websocket)
                    if not conns:
                        del self.active_connections[user_id]
                    break

    async def send_personal(self, websocket: WebSocket, data: dict):
        await websocket.send_text(json.dumps(data))

    async def send_to_user(self, user_id: int, data: dict):
        # send to all connections for this user
        async with self._lock:
            conns = self.active_connections.get(user_id) or set()
            for ws in list(conns):
                try:
                    await ws.send_text(json.dumps(data))
                except Exception:
                    # if send fails, remove that websocket
                    conns.remove(ws)

    async def broadcast_chat_message(self, db: AsyncSession, message: Message):
        """Send a message to all members of the chat that message belongs to.
        The message will be formatted to match the shape returned by the `get_messages` endpoint
        (fields: direction, name, message, time).
        Direction is computed per-recipient: 'send' for the sender, 'recieved' for others (keeps existing typo).
        """
        # Load sender username and chat members
        result = await db.execute(select(Message).options(selectinload(Message.sender)).where(Message.id == message.id))
        m = result.scalars().first()
        if not m:
            return

        # Get chat members
        result = await db.execute(select(ChatMember).where(ChatMember.chat_id == m.chat_id).options(selectinload(ChatMember.user)))
        members = result.scalars().all()
        recipients = [mem.user.id for mem in members]

        # For each recipient, compute direction and send
        for uid in recipients:
            direction = "recieved" if uid != m.sender_id else "send"
            payload = {
                "type": "message",
                "payload": {
                    "chatId": m.chat_id,
                    "message": {
                        "direction": direction,
                        "name": m.sender.username if m.sender else "Unknown",
                        "message": m.content,
                        "time": m.created_at.isoformat(),
                        "imageUrl": m.attachment_url
                    },
                },
            }
            await self.send_to_user(uid, payload)


manager = ConnectionManager()


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """A simple websocket endpoint that registers the connection and keeps it alive.

    The user's session token (cookie `session_token`) is used to associate the connection with a user id.
    """
    user_id = await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; we don't expect clients to send messages for now.
            data = await websocket.receive_text()
            # Optionally, you can handle client messages here (e.g., pings or subscription requests)
            # We'll ignore/echo
            try:
                parsed = json.loads(data)
            except Exception:
                parsed = {"type": "raw", "data": data}
            await manager.send_personal(websocket, {"type": "echo", "payload": parsed})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        # on any error just disconnect
        await manager.disconnect(websocket)
