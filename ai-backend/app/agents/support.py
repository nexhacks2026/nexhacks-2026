from app.agents.base import BaseAgent
from app.models import SupportAnalysisRequest, SupportAnalysisResult
from app.config import Config

import logging

logger = logging.getLogger(__name__)

class SupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(model=Config.SUPPORT_MODEL)

    async def analyze(self, request: SupportAnalysisRequest) -> SupportAnalysisResult:
        logger.info(f"Analyzing support request for ticket: {request.ticket.ticket_id if hasattr(request.ticket, 'ticket_id') else 'new'}")
        ticket = request.ticket
        context = request.context
        
        faq_list_str = ""
        if context and context.faqs:
            for faq in context.faqs:
                faq_list_str += f"- ID: {faq.id}\n  Question: {faq.question}\n  Answer: {faq.answer}\n  Link: {faq.link}\n"

        system_prompt = """
You are a support specialist. Match the ticket to FAQs or self-service actions.

Determine:
1. Does this match an FAQ? If yes, which one?
2. Is this a duplicate?
3. Can the user self-service?
4. If none, escalate.

Output schema (JSON):
{
  "resolution_action": "FAQ_LINK|DUPLICATE_CLOSE|SELF_SERVICE_REDIRECT|ESCALATE",
  "faq_match": {
    "faq_id": "...",
    "question": "...",
    "link": "...",
    "confidence": 0.0
  },
  "self_service": {
    "action": "...",
    "steps": ["..."]
  },
  "confidence": 0.0,
  "reasoning": "..."
}
"""

        user_content = f"""
Ticket: {ticket.content.issue_title or ticket.content.subject}
Body: {ticket.content.body or ticket.content.message_text}

Available FAQs:
{faq_list_str}
"""

        result_json = await self._call_llm(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.1
        )

        return SupportAnalysisResult(**result_json)

support_agent = SupportAgent()
