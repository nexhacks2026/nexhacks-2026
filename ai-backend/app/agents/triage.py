from app.agents.base import BaseAgent
from app.models import TicketData, TriageResult
from app.config import Config

class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__(model=Config.TRIAGE_MODEL)

    async def analyze(self, ticket: TicketData) -> TriageResult:
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

Output schema:
{
  "category": "...",
  "priority": "...",
  "confidence": 0.0,
  "reasoning": "...",
  "suggested_assignee_team": "...",
  "tags": ["..."],
  "estimated_resolution_time_hours": 0
}
"""
        
        user_content = f"""
Ticket Source: {ticket.source}
Content: {ticket.content.subject} / {ticket.content.body}
Title: {ticket.content.issue_title}
Message: {ticket.content.message_text}
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
