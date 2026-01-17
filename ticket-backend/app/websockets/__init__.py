"""WebSocket package for real-time updates."""

from .manager import ConnectionManager, WebSocketClient, connection_manager

__all__ = [
    "ConnectionManager",
    "WebSocketClient",
    "connection_manager",
]
