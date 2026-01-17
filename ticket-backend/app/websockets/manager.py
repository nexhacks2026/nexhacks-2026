"""WebSocket connection manager for real-time updates."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client."""
    client_id: str
    websocket: WebSocket
    subscriptions: set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionManager:
    """Manages WebSocket connections with channel-based subscriptions."""

    def __init__(self):
        self._connections: dict[str, WebSocketClient] = {}
        self._channel_subscribers: dict[str, set[str]] = {}  # channel -> set of client_ids

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections[client_id] = WebSocketClient(
            client_id=client_id,
            websocket=websocket,
        )
        # Auto-subscribe to "all" channel
        await self.subscribe(client_id, "all")

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection and clean up subscriptions."""
        if client_id in self._connections:
            client = self._connections[client_id]
            # Remove from all channels
            for channel in client.subscriptions:
                if channel in self._channel_subscribers:
                    self._channel_subscribers[channel].discard(client_id)
            del self._connections[client_id]

    async def subscribe(self, client_id: str, channel: str) -> bool:
        """Subscribe a client to a channel."""
        if client_id not in self._connections:
            return False

        client = self._connections[client_id]
        client.subscriptions.add(channel)

        if channel not in self._channel_subscribers:
            self._channel_subscribers[channel] = set()
        self._channel_subscribers[channel].add(client_id)

        # Send confirmation
        await self.send_personal_message(
            client_id,
            {
                "event": "subscribed",
                "channel": channel,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return True

    async def unsubscribe(self, client_id: str, channel: str) -> bool:
        """Unsubscribe a client from a channel."""
        if client_id not in self._connections:
            return False

        client = self._connections[client_id]
        client.subscriptions.discard(channel)

        if channel in self._channel_subscribers:
            self._channel_subscribers[channel].discard(client_id)

        # Send confirmation
        await self.send_personal_message(
            client_id,
            {
                "event": "unsubscribed",
                "channel": channel,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return True

    async def send_personal_message(
        self,
        client_id: str,
        message: dict[str, Any],
    ) -> bool:
        """Send a message to a specific client."""
        if client_id not in self._connections:
            return False

        client = self._connections[client_id]
        try:
            await client.websocket.send_json(message)
            return True
        except Exception:
            # Client disconnected, clean up
            self.disconnect(client_id)
            return False

    async def broadcast(self, message: dict[str, Any]) -> int:
        """Broadcast message to all connected clients."""
        return await self.broadcast_to_channel("all", message)

    async def broadcast_to_channel(
        self,
        channel: str,
        message: dict[str, Any],
    ) -> int:
        """Broadcast message to all clients subscribed to a channel."""
        if channel not in self._channel_subscribers:
            return 0

        sent_count = 0
        disconnected = []

        for client_id in self._channel_subscribers[channel].copy():
            if client_id in self._connections:
                client = self._connections[client_id]
                try:
                    await client.websocket.send_json(message)
                    sent_count += 1
                except Exception:
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

        return sent_count

    async def broadcast_event(
        self,
        event_type: str,
        data: dict[str, Any],
        channels: Optional[list[str]] = None,
    ) -> int:
        """Broadcast an event to specified channels (or all if none specified)."""
        message = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if channels is None:
            return await self.broadcast(message)

        total_sent = 0
        sent_clients = set()  # Avoid sending duplicate messages

        for channel in channels:
            if channel in self._channel_subscribers:
                for client_id in self._channel_subscribers[channel].copy():
                    if client_id not in sent_clients and client_id in self._connections:
                        success = await self.send_personal_message(client_id, message)
                        if success:
                            total_sent += 1
                            sent_clients.add(client_id)

        return total_sent

    def get_connected_clients(self) -> list[str]:
        """Get list of connected client IDs."""
        return list(self._connections.keys())

    def get_client_subscriptions(self, client_id: str) -> set[str]:
        """Get channels a client is subscribed to."""
        if client_id in self._connections:
            return self._connections[client_id].subscriptions.copy()
        return set()

    def get_channel_subscribers(self, channel: str) -> set[str]:
        """Get clients subscribed to a channel."""
        return self._channel_subscribers.get(channel, set()).copy()

    def get_stats(self) -> dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self._connections),
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self._channel_subscribers.items()
            },
        }


# Global connection manager instance
connection_manager = ConnectionManager()
