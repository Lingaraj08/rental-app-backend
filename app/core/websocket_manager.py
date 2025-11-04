# app/core/websocket_manager.py
"""Minimal WebSocket manager stub.

Provides a send_to_user coroutine used by the realtime listener. You can
extend this to maintain actual WebSocket connections and broadcast messages.
"""

import asyncio
from typing import Any, Dict, Set


class WebSocketManager:
    def __init__(self) -> None:
        # Map user_id -> set of websocket connections (optional, not wired yet)
        self._connections: Dict[str, Set[Any]] = {}

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific user.

        This stub prints to the console. Replace with actual broadcast logic
        if you're tracking active WebSocket connections.
        """
        # Example implementation if you track connections:
        # for ws in list(self._connections.get(user_id, [])):
        #     try:
        #         await ws.send_json(message)
        #     except Exception:
        #         pass
        print(f"[WS] -> user {user_id}: {message}")


# Singleton manager instance
manager = WebSocketManager()
