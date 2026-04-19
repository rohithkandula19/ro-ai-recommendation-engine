"""WebSocket endpoints for real-time features: watch-party sync, live notifications,
presence, typing indicators, and live admin dashboard."""
import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from core.security import decode_token

router = APIRouter(tags=["ws"])


class RoomManager:
    """In-memory pub/sub per room. For multi-instance, swap for Redis pubsub."""
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self.user_rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self.presence: dict[str, set[str]] = defaultdict(set)

    async def join(self, room: str, ws: WebSocket):
        self.rooms[room].add(ws)

    async def leave(self, room: str, ws: WebSocket):
        self.rooms[room].discard(ws)
        if not self.rooms[room]:
            self.rooms.pop(room, None)

    async def broadcast(self, room: str, message: dict, exclude: WebSocket | None = None):
        dead = []
        for ws in self.rooms.get(room, set()):
            if ws is exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.rooms[room].discard(ws)

    async def broadcast_user(self, user_id: str, message: dict):
        for ws in list(self.user_rooms.get(user_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                self.user_rooms[user_id].discard(ws)

    def mark_online(self, user_id: str, ws: WebSocket):
        self.user_rooms[user_id].add(ws)
        self.presence["online"].add(user_id)

    def mark_offline(self, user_id: str, ws: WebSocket):
        self.user_rooms[user_id].discard(ws)
        if not self.user_rooms[user_id]:
            self.presence["online"].discard(user_id)


rooms = RoomManager()


async def _auth_or_close(ws: WebSocket, token: str | None) -> str | None:
    if not token:
        await ws.close(code=4401); return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await ws.close(code=4401); return None
    return payload["sub"]


@router.websocket("/ws/party/{room_code}")
async def party_ws(ws: WebSocket, room_code: str, token: str | None = None):
    user_id = await _auth_or_close(ws, token)
    if not user_id: return
    await ws.accept()
    await rooms.join(room_code, ws)
    await rooms.broadcast(room_code, {"type": "join", "user_id": user_id}, exclude=ws)
    try:
        while True:
            msg = await ws.receive_json()
            msg["user_id"] = user_id
            await rooms.broadcast(room_code, msg, exclude=ws)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"party_ws err: {e}")
    finally:
        await rooms.leave(room_code, ws)
        await rooms.broadcast(room_code, {"type": "leave", "user_id": user_id})


@router.websocket("/ws/notifications")
async def notif_ws(ws: WebSocket, token: str | None = None):
    user_id = await _auth_or_close(ws, token)
    if not user_id: return
    await ws.accept()
    rooms.mark_online(user_id, ws)
    await ws.send_json({"type": "hello", "online": list(rooms.presence.get("online", set()))})
    try:
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        rooms.mark_offline(user_id, ws)


@router.websocket("/ws/chat-typing/{other_id}")
async def typing_ws(ws: WebSocket, other_id: str, token: str | None = None):
    user_id = await _auth_or_close(ws, token)
    if not user_id: return
    await ws.accept()
    room = "dm:" + ":".join(sorted([user_id, other_id]))
    await rooms.join(room, ws)
    try:
        while True:
            msg = await ws.receive_json()
            await rooms.broadcast(room, {"type": "typing", "user_id": user_id, "is_typing": msg.get("is_typing", False)}, exclude=ws)
    except WebSocketDisconnect:
        pass
    finally:
        await rooms.leave(room, ws)


@router.websocket("/ws/admin/live")
async def admin_live(ws: WebSocket, token: str | None = None):
    user_id = await _auth_or_close(ws, token)
    if not user_id: return
    payload = decode_token(token)
    if not payload or not payload.get("is_admin"):
        await ws.close(code=4403); return
    await ws.accept()
    try:
        while True:
            await asyncio.sleep(2)
            # Piggyback on Prometheus metrics for a quick live counter.
            from middleware.metrics_middleware import REQUEST_COUNT
            total = 0
            try:
                for m in REQUEST_COUNT.collect():
                    for s in m.samples:
                        total += int(s.value)
            except Exception:
                pass
            await ws.send_json({"type": "tick", "total_requests": total,
                                "online_users": len(rooms.presence.get("online", set()))})
    except WebSocketDisconnect:
        pass


async def push_to_user(user_id: str, payload: dict):
    """Helper callable from other routers to push live notification to a user."""
    await rooms.broadcast_user(user_id, {"type": "notification", **payload})
