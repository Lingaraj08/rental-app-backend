# app/core/websocket_manager.py

from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    """Handles active WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # key: user_id

    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept and store connection for a user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"🔗 User {user_id} connected")

    def disconnect(self, user_id: str):
        """Remove disconnected user."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"❌ User {user_id} disconnected")

    async def send_to_user(self, user_id: str, message: dict):
        """Send a JSON message to a specific user."""
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(message)
        else:
            print(f"⚠️ User {user_id} not connected, message dropped.")

    async def broadcast(self, message: dict):
        """Send to all connected users."""
        for user_id, ws in self.active_connections.items():
            await ws.send_json(message)


# Global instance
manager = ConnectionManager()
