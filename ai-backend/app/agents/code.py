import json
from app.agents.base import BaseAgent
from app.models import CodeAnalysisRequest, CodeAnalysisResult
from app.config import Config

import logging

logger = logging.getLogger(__name__)

class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__(model=Config.CODE_MODEL)

    async def analyze(self, request: CodeAnalysisRequest) -> CodeAnalysisResult:
        logger.info(f"Analyzing code request for ticket: {request.ticket.ticket_id if hasattr(request.ticket, 'ticket_id') else 'new'}")
        ticket = request.ticket
        context = request.code_context
        
        related_files_str = ""
        if context and context.related_files:
            for f in context.related_files:
                related_files_str += f"\nFile: {f.get('path', 'unknown')}\nContent:\n{f.get('content', '')}\n"

        system_prompt = """
You are an expert software engineer. Analyze the bug and generate a fix.

Your task:
1. Identify the root cause
2. Propose a fix (as a code patch or strategy)
3. Suggest test cases
4. Rate your confidence (0-1)

Output schema (JSON):
{
  "analysis": {
    "root_cause": "...",
    "severity": "HIGH|MEDIUM|LOW",
    "affected_flows": ["..."]
  },
  "fix": {
    "strategy": "...",
    "approach": "...",
    "tradeoffs": "..."
  },
  "patch": {
    "file": "path/to/file",
    "diff": "...",
    "changed_lines": [1, 2]
  },
  "pr_draft": {
    "title": "...",
    "description": "...",
    "labels": ["..."]
  },
  "confidence": 0.0,
  "caveats": "..."
}
"""

        user_content = f"""
Ticket: {ticket.content.issue_title or ticket.content.subject}
Description: {ticket.content.body or ticket.content.message_text}
Error Snippet: {context.error_snippet if context else 'None'}

Related Files:
{related_files_str}
"""

        result_json = await self._call_llm(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.2 # Deterministic for code
        )

        return CodeAnalysisResult(**result_json)

code_agent = CodeAgent()
