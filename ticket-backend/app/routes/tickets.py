"""Ticket API endpoints."""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.models import (
    Ticket,
    TicketSource,
    TicketPriority,
    TicketCategory,
    TicketStatus,
    QueueType,
    EmailContent,
    DiscordContent,
    GitHubContent,
    FormContent,
)
from app.storage import ticket_repository
from app.queues import queue_manager
from app.events import event_publisher

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


# Request/Response Models

class EmailPayload(BaseModel):
    """Email content payload."""
    sender_email: str = Field(..., alias="from")
    recipient_email: str = Field(..., alias="to")
    subject: str
    body: str
    timestamp: str
    thread_id: Optional[str] = None

    class Config:
        populate_by_name = True


class DiscordPayload(BaseModel):
    """Discord content payload."""
    channel_id: str
    user_id: str
    message_id: str
    message_text: str
    timestamp: str
    username: Optional[str] = None
    guild_id: Optional[str] = None


class GitHubPayload(BaseModel):
    """GitHub content payload."""
    repo: str
    issue_number: int
    author: str
    title: str
    body: str
    timestamp: Optional[str] = None
    labels: Optional[list[str]] = None
    url: Optional[str] = None


class FormPayload(BaseModel):
    """Form submission payload."""
    form_fields: dict[str, Any] = Field(..., alias="fields")
    submission_time: Optional[str] = None
    form_id: Optional[str] = None
    submitter_email: Optional[str] = None
    submitter_name: Optional[str] = None

    class Config:
        populate_by_name = True


class IngestRequest(BaseModel):
    """Request body for ticket ingestion."""
    source: TicketSource
    content_type: str
    payload: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response after ticket ingestion."""
    ticket_id: str
    status: str
    queue: str
    position_in_queue: int
    estimated_time_to_triage: str
    created_at: str


class TriageCompleteRequest(BaseModel):
    """Request body for triage completion."""
    category: TicketCategory
    priority: TicketPriority
    suggested_assignee: Optional[str] = None
    ai_reasoning: Optional[dict[str, Any]] = None
    auto_resolve: bool = False
    resolution_reason: Optional[str] = None


class TicketUpdateRequest(BaseModel):
    """Request body for ticket updates."""
    title: Optional[str] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    tags: Optional[list[str]] = None
    assignee: Optional[str] = None


class TicketResponse(BaseModel):
    """Standard ticket response."""
    ticket: dict[str, Any]


class TicketListResponse(BaseModel):
    """Response for listing tickets."""
    tickets: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


# Helper functions

def parse_timestamp(ts: Optional[str]) -> datetime:
    """Parse timestamp string to datetime."""
    if ts is None:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def create_content_from_payload(content_type: str, payload: dict[str, Any]):
    """Create appropriate content type from payload."""
    content_type = content_type.lower()

    if content_type == "email":
        return EmailContent(
            sender_email=payload.get("from", payload.get("sender_email", "")),
            recipient_email=payload.get("to", payload.get("recipient_email", "")),
            subject=payload.get("subject", ""),
            body=payload.get("body", ""),
            timestamp=parse_timestamp(payload.get("timestamp")),
            thread_id=payload.get("thread_id"),
        )
    elif content_type == "discord":
        return DiscordContent(
            channel_id=payload["channel_id"],
            user_id=payload["user_id"],
            message_id=payload.get("message_id", ""),
            message_text=payload.get("message_text", ""),
            timestamp=parse_timestamp(payload.get("timestamp")),
            username=payload.get("username"),
            guild_id=payload.get("guild_id"),
        )
    elif content_type == "github":
        return GitHubContent(
            repo=payload["repo"],
            issue_number=payload["issue_number"],
            author=payload["author"],
            issue_title=payload.get("title", payload.get("issue_title", "")),
            issue_body=payload.get("body", payload.get("issue_body", "")),
            timestamp=parse_timestamp(payload.get("timestamp")),
            labels=payload.get("labels"),
            url=payload.get("url"),
        )
    elif content_type == "form":
        return FormContent(
            form_fields=payload.get("fields", payload.get("form_fields", {})),
            submission_time=parse_timestamp(payload.get("submission_time")),
            form_id=payload.get("form_id"),
            submitter_email=payload.get("submitter_email"),
            submitter_name=payload.get("submitter_name"),
        )
    else:
        raise ValueError(f"Unknown content type: {content_type}")


# Endpoints

@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest_ticket(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
):
    """
    Webhook ingestion endpoint from n8n.
    Accepts tickets from various sources and enqueues them for processing.
    """
    try:
        # Validate and create content
        content = create_content_from_payload(request.content_type, request.payload)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

    # Extract priority hint from metadata if provided
    priority = TicketPriority.MEDIUM
    tags = []
    if request.metadata:
        if "priority" in request.metadata:
            try:
                priority = TicketPriority(request.metadata["priority"])
            except ValueError:
                pass
        if "tags" in request.metadata:
            tags = request.metadata.get("tags", [])

    # Create ticket
    ticket = Ticket.create(
        source=request.source,
        content=content,
        priority=priority,
        tags=tags,
    )

    # Save ticket
    ticket_repository.save(ticket)

    # Keep in INBOX queue (don't move to TRIAGE automatically)
    # ticket.move_to_queue(QueueType.TRIAGE)
    # ticket_repository.save(ticket)

    # Enqueue in INBOX
    position = queue_manager.enqueue(
        ticket=ticket,
        queue=QueueType.INBOX,
        reason="ingested from webhook",
    )

    # Estimate wait time
    wait_seconds = queue_manager.estimate_wait_time(QueueType.INBOX, position)
    wait_minutes = max(1, int(wait_seconds / 60))

    # Publish events in background
    background_tasks.add_task(event_publisher.publish_ticket_created, ticket)
    # Don't publish triage_pending since we're keeping it in inbox
    # background_tasks.add_task(event_publisher.publish_ticket_triage_pending, ticket)

    return IngestResponse(
        ticket_id=ticket.id,
        status=ticket.status.value,
        queue=ticket.current_queue.value,
        position_in_queue=position,
        estimated_time_to_triage=f"{wait_minutes} minutes",
        created_at=ticket.created_at.isoformat(),
    )


@router.post("/{ticket_id}/triage_complete")
async def triage_complete(
    ticket_id: str,
    request: TriageCompleteRequest,
    background_tasks: BackgroundTasks,
):
    """
    Callback endpoint for AI triage completion.
    Called by n8n after AI agent processes the ticket.
    """
    ticket = ticket_repository.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.current_queue != QueueType.TRIAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket is not in TRIAGE queue (currently in {ticket.current_queue.value})"
        )

    # Apply triage results
    ticket.set_category(request.category)
    ticket.update_priority(request.priority)

    if request.ai_reasoning:
        ticket.log_reasoning(request.ai_reasoning)

    if request.suggested_assignee:
        ticket.set_suggested_assignee(request.suggested_assignee)

    # Determine next queue
    old_queue = ticket.current_queue

    if request.auto_resolve:
        # Auto-resolve bypasses ACTIVE queue
        from app.models import AutoResolveAction
        ticket.mark_resolved(AutoResolveAction.FAQ_LINK if request.resolution_reason else AutoResolveAction.NONE)
        queue_manager.move_ticket(
            ticket_id=ticket_id,
            from_queue=QueueType.TRIAGE,
            to_queue=QueueType.RESOLUTION,
            ticket=ticket,
            reason=f"auto-resolved: {request.resolution_reason or 'AI decision'}",
        )
    else:
        # Move to assignment queue
        ticket.move_to_queue(QueueType.ASSIGNMENT)
        queue_manager.move_ticket(
            ticket_id=ticket_id,
            from_queue=QueueType.TRIAGE,
            to_queue=QueueType.ASSIGNMENT,
            ticket=ticket,
            reason="triage complete",
        )

    ticket_repository.save(ticket)

    # Publish events
    background_tasks.add_task(
        event_publisher.publish_ticket_moved,
        ticket,
        old_queue,
        ticket.current_queue,
    )

    return {
        "ticket_id": ticket_id,
        "status": ticket.status.value,
        "queue": ticket.current_queue.value,
        "category": ticket.category.value if ticket.category else None,
        "priority": ticket.priority.value,
        "suggested_assignee": ticket.suggested_assignee,
    }


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """Get ticket details by ID."""
    ticket = ticket_repository.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Include queue position if applicable
    ticket_dict = ticket.to_dict()
    position = queue_manager.get_queue_position(ticket_id)
    if position:
        ticket_dict["queue_position"] = position[1]

    return TicketResponse(ticket=ticket_dict)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    request: TicketUpdateRequest,
    background_tasks: BackgroundTasks,
):
    """Update ticket properties."""
    ticket = ticket_repository.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    changes = {}

    if request.title is not None:
        ticket.update_title(request.title)
        changes["title"] = request.title

    if request.priority is not None:
        ticket.update_priority(request.priority)
        changes["priority"] = request.priority.value

    if request.category is not None:
        ticket.set_category(request.category)
        changes["category"] = request.category.value

    if request.tags is not None:
        for tag in request.tags:
            ticket.add_tag(tag)
        changes["tags"] = ticket.tags

    if request.assignee is not None:
        old_assignee = ticket.assignee
        ticket.assign(request.assignee)
        changes["assignee"] = request.assignee

        background_tasks.add_task(
            event_publisher.publish_ticket_assigned,
            ticket,
            request.assignee,
            old_assignee,
        )

    ticket_repository.save(ticket)

    if changes:
        background_tasks.add_task(
            event_publisher.publish_ticket_updated,
            ticket,
            changes,
        )

    return TicketResponse(ticket=ticket.to_dict())


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[TicketStatus] = None,
    queue: Optional[QueueType] = None,
    priority: Optional[TicketPriority] = None,
    category: Optional[TicketCategory] = None,
    assignee: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List tickets with optional filters."""
    tickets = ticket_repository.find(
        status=status,
        queue=queue,
        priority=priority,
        category=category,
        assignee=assignee,
        limit=limit,
        offset=offset,
    )

    total = ticket_repository.count()

    return TicketListResponse(
        tickets=[t.to_dict() for t in tickets],
        total=total,
        limit=limit,
        offset=offset,
    )
