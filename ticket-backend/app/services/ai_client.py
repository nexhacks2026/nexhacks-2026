import httpx
import os
import logging
from typing import Optional, Any
from app.models import Ticket
from app.services.user_service import user_service


class AIClient:
    def __init__(self):
        # In Docker compose, ai-service is the hostname.
        # Fallback to localhost if running outside docker but port mapped?
        # But we are in docker mostly.
        self.base_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")
        self.logger = logging.getLogger(__name__)

    async def analyze_triage(self, ticket: Ticket) -> Optional[dict]:
        """
        Call AI backend to triage a ticket.
        """
        url = f"{self.base_url}/analyze/triage"
        try:
            # Prepare payload matching ai-backend TicketData schema
            payload = ticket.to_dict()
            # Include available agents for AI to suggest assignees
            payload["available_agents"] = user_service.get_available_agents()

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Failed to call AI triage: {e}")
            return None

    async def analyze_code(self, ticket: Ticket, code_context: dict) -> Optional[dict]:
        """
        Call AI backend for code analysis.
        """
        url = f"{self.base_url}/analyze/code"
        try:
            payload = {"ticket": ticket.to_dict(), "code_context": code_context}
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Failed to call AI code analysis: {e}")
            return None

    async def analyze_support(self, ticket: Ticket, context: dict) -> Optional[dict]:
        """
        Call AI backend for support analysis.
        """
        url = f"{self.base_url}/analyze/support"
        try:
            payload = {"ticket": ticket.to_dict(), "context": context}
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Failed to call AI support analysis: {e}")
            return None


ai_client = AIClient()
