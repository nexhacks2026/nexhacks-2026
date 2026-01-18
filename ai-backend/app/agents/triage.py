from app.agents.base import BaseAgent
from app.models import TicketData, TriageResult
from app.config import Config
from app.services.doc_loader import doc_loader

import logging

logger = logging.getLogger(__name__)


class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__(model=Config.TRIAGE_MODEL)

    async def analyze(self, ticket: TicketData) -> TriageResult:
        logger.info(
            f"Analyzing ticket for triage: {ticket.ticket_id if hasattr(ticket, 'ticket_id') else 'new'}"
        )
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

Auto-Resolution Rules:
- Set `can_auto_resolve` to TRUE ONLY when:
  1. The ticket can be FULLY answered from the provided documentation
  2. AND no human action is required (no account changes, no investigation, no judgment calls)
  3. AND you are NOT assigning to a human agent
- Set `can_auto_resolve` to FALSE when:
  1. You are assigning to a human (suggested_assignee is set)
  2. OR it requires human judgment, account-specific investigation, or actions
  3. OR it's a bug report, feature request, or billing dispute
- If `can_auto_resolve` is true, provide `auto_resolve_reasoning`.
- IMPORTANT: can_auto_resolve and suggested_assignee are mutually exclusive!

Assignee Selection:
- If ticket needs human help, you MUST assign someone (suggested_assignee).
- SPECIAL RULE: If the ticket is about code, programming, debugging, API errors, 
  build failures, or technical implementation, assign to "coding_agent".
- Match ticket content to agent `skills`.
- Avoid agents with status "offline" unless no one else is available.
- Prefer agents with lower `current_load` if skills are a match.
- If assigned to human or coding_agent, set can_auto_resolve to false.
- Only leave suggested_assignee null if can_auto_resolve is true.

Output schema:
{
  "category": "...",
  "priority": "...",
  "confidence": 0.0,
  "reasoning": "...",
  "can_auto_resolve": true/false,
  "auto_resolve_reasoning": "..." or null,
  "suggested_assignee_team": "...",
  "suggested_assignee": "user-ID-or-null",
  "tags": ["..."],
  "estimated_resolution_time_hours": 0
}
"""

        # Format available agents for the prompt
        agents_context = "No agent data available."
        if hasattr(ticket, "available_agents") and ticket.available_agents:
            agents_list = []
            for agent in ticket.available_agents:
                skills_str = ", ".join(agent.get("skills", []))
                agents_list.append(
                    f"- ID: {agent.get('id')} | Name: {agent.get('name')} | "
                    f"Status: {agent.get('status')} | Load: {agent.get('current_load')} | "
                )
            agents_context = "\n".join(agents_list)
            
        logger.info(f"Available agents for triage: {ticket.available_agents}")
        logger.info(f"Formatted agents context: {agents_context}")

        # Get compressed documentation context
        docs_context = doc_loader.get_docs_context()

        user_content = f"""
Ticket Source: {ticket.source}
Content: {ticket.content.subject} / {ticket.content.body}
Title: {ticket.content.issue_title}
Message: {ticket.content.message_text}

Available Agents:
{agents_context}

Reference Documentation (use these runbooks to inform your decisions):
{docs_context}
"""

        result_json = await self._call_llm(
            system_prompt=system_prompt, user_content=user_content, temperature=0.3
        )

        # Parse and validate with Pydantic
        # Ensure fields map correctly or defaults are handled
        return TriageResult(**result_json)


# Singleton instance
triage_agent = TriageAgent()
