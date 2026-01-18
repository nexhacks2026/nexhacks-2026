"""Webhook service for sending notifications to n8n for ticket resolutions."""

import logging
from typing import Any, Optional
import httpx
import os
from dotenv import load_dotenv

from app.models import Ticket, TicketSource

load_dotenv()
logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications to n8n."""

    def __init__(self):
        self.n8n_resolution_webhook_url = os.getenv("N8N_RESOLUTION_WEBHOOK_URL")
        self.timeout = 10.0

    async def send_resolution_notification(
        self, ticket: Ticket, resolution_message: Optional[str] = None
    ) -> bool:
        """
        Send ticket resolution notification to n8n.
        
        Args:
            ticket: The resolved ticket
            resolution_message: Optional custom resolution message
            
        Returns:
            bool: True if webhook was sent successfully, False otherwise
        """
        if not self.n8n_resolution_webhook_url:
            logger.warning("N8N_RESOLUTION_WEBHOOK_URL not configured, skipping webhook")
            return False

        payload = self._build_resolution_payload(ticket, resolution_message)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.n8n_resolution_webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"Successfully sent resolution webhook for ticket {ticket.id}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send resolution webhook for ticket {ticket.id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending resolution webhook for ticket {ticket.id}: {e}")
            return False

    def _build_resolution_payload(
        self, ticket: Ticket, resolution_message: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Build the webhook payload for ticket resolution.
        
        The payload includes:
        - ticket_id: For fetching full ticket data via API
        - source: Where the ticket came from (discord, email, github)
        - source_data: Original source-specific identifiers for responding back
        - resolution: Information about how the ticket was resolved
        - ticket_summary: Key ticket information
        """
        # Extract source-specific data for routing the response back
        source_data = self._extract_source_data(ticket)
        
        # Build resolution info
        resolution_info = {
            "message": resolution_message or self._get_default_resolution_message(ticket),
            "action": ticket.resolution_action.value,
            "resolved_at": ticket.updated_at.isoformat(),
            "assignee": ticket.assignee,
        }
        
        # Include AI response if available
        if ticket.ai_reasoning:
            if "auto_response" in ticket.ai_reasoning:
                resolution_info["ai_response"] = ticket.ai_reasoning["auto_response"]
            if "source_docs" in ticket.ai_reasoning:
                resolution_info["source_docs"] = ticket.ai_reasoning["source_docs"]
        
        payload = {
            "event": "ticket.resolved",
            "ticket_id": ticket.id,
            "source": ticket.source.value,
            "source_data": source_data,
            "resolution": resolution_info,
            "ticket_summary": {
                "title": ticket.title,
                "description": ticket.description,
                "category": ticket.category.value if ticket.category else None,
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "created_at": ticket.created_at.isoformat(),
            }
        }
        
        return payload

    def _extract_source_data(self, ticket: Ticket) -> dict[str, Any]:
        """Extract source-specific identifiers for routing responses."""
        content = ticket.content
        source_data = {
            "type": ticket.source.value,
            "sender": content.sender,
        }
        
        if ticket.source == TicketSource.EMAIL:
            source_data.update({
                "sender_email": content.sender_email,
                "recipient_email": content.recipient_email,
                "subject": content.subject,
                "thread_id": content.thread_id,
            })
        elif ticket.source == TicketSource.DISCORD:
            source_data.update({
                "username": content.sender,
            })
        elif ticket.source == TicketSource.GITHUB:
            source_data.update({
                "issue_number": content.issue_number,
                "author": content.sender,
                "url": content.url,
            })
        elif ticket.source == TicketSource.FORM:
            # For form submissions, try to extract contact info
            form_fields = content.form_fields
            source_data.update({
                "form_id": content.form_id,
                "submitter_email": content.submitter_email,
                "submitter_name": content.submitter_name,
                "form_fields": form_fields,
            })
        
        return source_data

    def _get_default_resolution_message(self, ticket: Ticket) -> str:
        """Generate a default resolution message based on ticket info."""
        if ticket.resolution_action.value == "FAQ_LINK":
            return "Your issue has been resolved. Please check the provided documentation links."
        elif ticket.resolution_action.value == "AUTO_RESPONSE":
            return "Your issue has been automatically resolved. See the response below."
        elif ticket.assignee:
            return f"Your ticket has been resolved by {ticket.assignee}."
        else:
            return "Your ticket has been resolved."


# Global webhook service instance
webhook_service = WebhookService()
