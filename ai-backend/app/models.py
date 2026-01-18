from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class TicketContent(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    issue_title: Optional[str] = None
    message_text: Optional[str] = None

class TicketData(BaseModel):
    """Simplified ticket data for AI analysis"""
    id: str
    content: TicketContent
    source: str
    priority: Optional[str] = "MEDIUM"
    tags: List[str] = []

# --- Triage Models ---
class TriageResult(BaseModel):
    category: str
    priority: str
    confidence: float
    reasoning: str
    suggested_assignee_team: Optional[str] = None
    tags: List[str] = []
    estimated_resolution_time_hours: Optional[int] = None

# --- Code Analysis Models ---
class CodeContext(BaseModel):
    repo_url: str
    related_files: List[dict] = []
    error_snippet: Optional[str] = None

class CodeAnalysisRequest(BaseModel):
    ticket: TicketData
    code_context: Optional[CodeContext] = None

class CodeAnalysisResult(BaseModel):
    analysis: dict
    fix: dict
    patch: Optional[dict] = None
    pr_draft: Optional[dict] = None
    confidence: float

# --- Support Models ---
class FAQItem(BaseModel):
    id: str
    question: str
    answer: str
    link: Optional[str] = None

class SupportContext(BaseModel):
    faqs: List[FAQItem] = []
    # Could add past tickets here

class SupportAnalysisRequest(BaseModel):
    ticket: TicketData
    context: Optional[SupportContext] = None

class SupportAnalysisResult(BaseModel):
    resolution_action: str # FAQ_LINK, DUPLICATE_CLOSE, SELF_SERVICE_REDIRECT, ESCALATE
    faq_match: Optional[dict] = None
    self_service: Optional[dict] = None
    confidence: float
    reasoning: str
