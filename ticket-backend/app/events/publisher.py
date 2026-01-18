"""Event publisher for n8n and WebSocket integration."""

from datetime import datetime, timezone
from typing import Any, Optional
import asyncio
import httpx

from app.models import Ticket, QueueType
from app.websockets import connection_manager

from dotenv import load_dotenv
import os

load_dotenv()
webhook_url = os.getenv("N8N_AI_WEBHOOK_URL")


class EventPublisher:
    """Publishes events for ticket state changes to WebSocket and external systems."""

    def __init__(self):
        self._external_webhook_url: Optional[str] = None  # For n8n integration

    def set_webhook_url(self, url: str) -> None:
        """Set the external webhook URL for n8n integration."""
        self._external_webhook_url = url

    async def publish_ticket_created(self, ticket: Ticket) -> None:
        """Publish ticket.created event."""
        await self._publish_event(
            event_type="ticket.created",
            data={
                "ticket_id": ticket.id,
                "source": ticket.source.value,
                "queue": ticket.current_queue.value,
                "priority": ticket.priority.value,
                "sender": ticket.content.sender,
            },
            ticket=ticket,
        )

    async def publish_ticket_updated(
        self, ticket: Ticket, changes: dict[str, Any]
    ) -> None:
        """Publish ticket.updated event."""
        await self._publish_event(
            event_type="ticket.updated",
            data={
                "ticket_id": ticket.id,
                "changes": changes,
                "status": ticket.status.value,
                "queue": ticket.current_queue.value,
            },
            ticket=ticket,
        )

    async def publish_ticket_moved(
        self,
        ticket: Ticket,
        from_queue: QueueType,
        to_queue: QueueType,
    ) -> None:
        """Publish ticket.moved event."""
        await self._publish_event(
            event_type="ticket.moved",
            data={
                "ticket_id": ticket.id,
                "from_queue": from_queue.value,
                "to_queue": to_queue.value,
                "status": ticket.status.value,
            },
            ticket=ticket,
            extra_channels=[f"queue.{from_queue.value}", f"queue.{to_queue.value}"],
        )

    async def publish_ticket_assigned(
        self,
        ticket: Ticket,
        assignee: str,
        previous_assignee: Optional[str] = None,
    ) -> None:
        """Publish ticket.assigned event."""
        await self._publish_event(
            event_type="ticket.assigned",
            data={
                "ticket_id": ticket.id,
                "assignee": assignee,
                "previous_assignee": previous_assignee,
                "queue": ticket.current_queue.value,
            },
            ticket=ticket,
            extra_channels=[f"agent.{assignee}"],
        )

    async def publish_ticket_triage_pending(self, ticket: Ticket) -> None:
        """Publish ticket.triage_pending event - triggers n8n AI workflow."""
        from app.services.user_service import user_service

        await self._publish_event(
            event_type="ticket.triage_pending",
            data={
                "ticket_id": ticket.id,
                "source": ticket.source.value,
                "content_preview": ticket.content.extract_body()[:500],
                "priority": ticket.priority.value,
                "available_agents": user_service.get_available_agents(),
            },
            ticket=ticket,
        )

    async def publish_queue_stats(
        self, queue: QueueType, stats: dict[str, Any]
    ) -> None:
        """Publish queue.stats event."""
        await connection_manager.broadcast_event(
            event_type="queue.stats",
            data={
                "queue": queue.value,
                "stats": stats,
            },
            channels=["all", f"queue.{queue.value}"],
        )

    async def publish_coding_agent_trigger(self, ticket: Ticket) -> None:
        """Trigger n8n webhook for coding agent when a ticket has coding tags"""
        print(
            f"Triggering coding agent for ticket {ticket.id} (Priority: {ticket.priority.value})"
        )

        payload = {
            "ticket_id": ticket.id,
            "tags": ticket.tags,
            "priority": ticket.priority.value,
            "source": ticket.source.value,
            "content": {
                "subject": ticket.title,
                "body": ticket.content.extract_body(),
                "sender": ticket.content.sender,
            },
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()
        except Exception as e:
            # Log error but don't fail the ticket creation
            print(f"Failed to trigger coding agent webhook: {e}")

    async def _publish_event(
        self,
        event_type: str,
        data: dict[str, Any],
        ticket: Optional[Ticket] = None,
        extra_channels: Optional[list[str]] = None,
    ) -> None:
        """Internal method to publish events to WebSocket and external webhook."""
        # Determine channels to broadcast to
        channels = ["all", "tickets.all"]
        if ticket:
            channels.append(f"ticket.{ticket.id}")
            channels.append(f"queue.{ticket.current_queue.value}")
        if extra_channels:
            channels.extend(extra_channels)

        # Broadcast to WebSocket clients
        await connection_manager.broadcast_event(
            event_type=event_type,
            data=data,
            channels=channels,
        )

        if self._external_webhook_url:
            try:
                payload = {**data, "event": event_type}
                
                async with httpx.AsyncClient() as client:
                    await client.post(self._external_webhook_url, json=payload, timeout=5.0)
            except Exception as e:
                # Log error but don't fail the operation
                print(f"Failed to send webhook for {event_type}: {e}")


# Global event publisher instance
event_publisher = EventPublisher()
