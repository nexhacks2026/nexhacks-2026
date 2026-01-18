from app.agents.base import BaseAgent
from app.models import TicketData, TriageResult
from app.config import Config

import logging

logger = logging.getLogger(__name__)

class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__(model=Config.TRIAGE_MODEL)

    async def analyze(self, ticket: TicketData) -> TriageResult:
        logger.info(f"Analyzing ticket for triage: {ticket.ticket_id if hasattr(ticket, 'ticket_id') else 'new'}")
        system_prompt = """
You are a ticket triage classifier. Analyze the ticket and output JSON.

Rules:
- Category must be one of: BILLING, TECHNICAL_SUPPORT, FEATURE_REQUEST, BUG_REPORT, ADMIN, OTHER
- Priority must be one of: LOW, MEDIUM, HIGH, CRITICAL
- Confidence is 0.0-1.0. Be honest about uncertainty.
- Do NOT make assumptions. If unclear, lower confidence.
- CRITICAL is only for: total outages, security breaches, data loss
- HIGH is for: features broken, major bugs, urgent requests
- MEDIUM is for: minor bugs, non-urgent requests, questions
- LOW is for: documentation, enhancement ideas, off-topic

Assignee Selection:
- Select the best `suggested_assignee` (user ID) from the provided list of available agents.
- Match ticket content to agent `skills`.
- Avoid agents with status "offline" unless no one else is available.
- Prefer agents with lower `current_load` if skills are a match.
- If no good match found, leave `suggested_assignee` null.

Output schema:
{
  "category": "...",
  "priority": "...",
  "confidence": 0.0,
  "reasoning": "...",
  "suggested_assignee_team": "...",
  "suggested_assignee": "user-ID-or-null",
  "tags": ["..."],
  "estimated_resolution_time_hours": 0
}
"""
        
        # Format available agents for the prompt
        agents_context = "No agent data available."
        if hasattr(ticket, 'available_agents') and ticket.available_agents:
            agents_list = []
            for agent in ticket.available_agents:
                skills_str = ", ".join(agent.get('skills', []))
                agents_list.append(
                    f"- ID: {agent.get('id')} | Name: {agent.get('name')} | "
                    f"Status: {agent.get('status')} | Load: {agent.get('current_load')} | "
                    f"Skills: {skills_str}"
                )
            agents_context = "\n".join(agents_list)

        user_content = f"""
Ticket Source: {ticket.source}
Content: {ticket.content.subject} / {ticket.content.body}
Title: {ticket.content.issue_title}
Message: {ticket.content.message_text}

Available Agents:
{agents_context}
"""
        
        result_json = await self._call_llm(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.3
        )
        
        # Parse and validate with Pydantic
        # Ensure fields map correctly or defaults are handled
        return TriageResult(**result_json)

# Singleton instance
triage_agent = TriageAgent()
