from app.agents.base import BaseAgent
from app.models import SupportAnalysisRequest, SupportAnalysisResult
from app.config import Config
from app.services.doc_loader import doc_loader

import logging

logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(model=Config.SUPPORT_MODEL)

    async def analyze(self, request: SupportAnalysisRequest) -> SupportAnalysisResult:
        logger.info(
            f"Analyzing support request for ticket: {request.ticket.id if hasattr(request.ticket, 'id') else 'new'}"
        )
        ticket = request.ticket

        # Get documentation context and list of available docs
        docs_context = doc_loader.get_docs_context()
        available_docs = doc_loader.list_docs()

        system_prompt = """
You are a support specialist. Your job is to resolve tickets using the provided documentation.

Analyze the ticket and determine if you can provide a helpful response based on the documentation.

Rules:
1. If the documentation contains relevant information, provide a clear, helpful response.
2. Include the SPECIFIC document name(s) you used in `source_docs`.
3. Set `resolution_action` based on outcome:
   - "FAQ_LINK": Documentation directly answers the question
   - "SELF_SERVICE_REDIRECT": User can resolve themselves with provided steps
   - "ESCALATE": Documentation doesn't cover this, needs human help
4. Write `response_text` as if you're replying directly to the user. Be friendly and helpful.
5. Be honest about confidence. If docs are only partially relevant, lower confidence.
6. Any commands listed in the runbooks should be usable by you and you are expected to execute them to help the user.
7. Always provide reasoning in the `reasoning` field explaining how you arrived at your conclusion.

Output schema (JSON):
{
  "resolution_action": "FAQ_LINK|SELF_SERVICE_REDIRECT|ESCALATE",
  "faq_match": {
    "doc_name": "...",
    "relevant_section": "..."
  },
  "self_service": {
    "action": "...",
    "steps": ["..."]
  },
  "confidence": 0.0,
  "reasoning": "...",
  "response_text": "Your friendly response to the user...",
  "source_docs": ["doc_name1", "doc_name2"]
}
"""

        user_content = f"""
Ticket Subject: {ticket.content.subject or ticket.content.issue_title or 'No subject'}
Ticket Body: {ticket.content.body or ticket.content.message_text or 'No body'}

Available Documentation Files: {', '.join(available_docs) if available_docs else 'None'}

Reference Documentation:
{docs_context}
"""

        result_json = await self._call_llm(
            system_prompt=system_prompt, user_content=user_content, temperature=0.1
        )

        return SupportAnalysisResult(**result_json)


# Singleton instance
support_agent = SupportAgent()
