# app/api/routes_ws.py

from fastapi import APIRouter, WebSocket, Query
from app.core.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket connection for a specific user."""
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 {user_id}: {data}")  # optional
    except Exception:
        manager.disconnect(user_id)
