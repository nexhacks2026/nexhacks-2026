from fastapi import FastAPI, HTTPException
from app.models import (
    TicketData, 
    TriageResult, 
    CodeAnalysisRequest, 
    CodeAnalysisResult,
    SupportAnalysisRequest,
    SupportAnalysisResult
)
from app.agents.triage import triage_agent
from app.agents.code import code_agent
from app.agents.support import support_agent

app = FastAPI(title="AI Agent Backend", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/analyze/triage", response_model=TriageResult)
async def analyze_triage(ticket: TicketData):
    """
    Analyze a ticket to determine category and priority.
    """
    return await triage_agent.analyze(ticket)

@app.post("/analyze/code", response_model=CodeAnalysisResult)
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyze code-related tickets and suggest fixes.
    """
    return await code_agent.analyze(request)

@app.post("/analyze/support", response_model=SupportAnalysisResult)
async def analyze_support(request: SupportAnalysisRequest):
    """
    Provide support responses based on FAQs.
    """
    return await support_agent.analyze(request)
