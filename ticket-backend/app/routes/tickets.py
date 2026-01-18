"""Ticket API endpoints."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    tags: Optional[list[str]] = None
    assignee: Optional[str] = None


class ResolveTicketRequest(BaseModel):
    """Request body for resolving a ticket."""

    resolution_message: Optional[str] = None
    resolution_action: Optional[str] = "MANUAL"  # MANUAL, FAQ_LINK, AUTO_RESPONSE, etc.


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
        # Handle unified payload structure where all sources send the same fields
        # For email, use 'id' as thread_id and provide default values for missing fields
        return EmailContent(
            sender_email=payload.get(
                "from",
                payload.get("sender_email", payload.get("user", "unknown@unknown.com")),
            ),
            recipient_email=payload.get(
                "to", payload.get("recipient_email", "nexhacks2026@gmail.com")
            ),
            subject=payload.get("subject", "No Subject"),
            body=payload.get("body", ""),
            timestamp=parse_timestamp(payload.get("timestamp")),
            thread_id=payload.get("thread_id", payload.get("id")),
        )
    elif content_type == "discord":
        # Use unified fields: 'id' as message_id, 'user' as user_id, 'body' as message_text
        return DiscordContent(
            channel_id=payload.get("channel_id", "unknown"),
            user_id=payload.get("user_id", payload.get("user", "unknown")),
            message_id=payload.get("message_id", payload.get("id", "")),
            message_text=payload.get("message_text", payload.get("body", "")),
            timestamp=parse_timestamp(payload.get("timestamp")),
            username=payload.get("username", payload.get("user")),
            guild_id=payload.get("guild_id"),
        )
    elif content_type == "github":
        # Use unified fields: 'repo_url' as repo, 'issue_url' for url, 'user' as author
        repo = payload.get("repo", payload.get("repo_url", "unknown/unknown"))
        # Extract repo name from URL if full URL provided
        if repo and repo != "null" and "github.com" in repo:
            repo = "/".join(repo.rstrip("/").split("/")[-2:])
        elif repo == "null":
            repo = "unknown/unknown"

        return GitHubContent(
            repo=repo,
            issue_number=payload.get("issue_number", 0),
            author=payload.get("author", payload.get("user", "unknown")),
            issue_title=payload.get(
                "title", payload.get("issue_title", payload.get("subject", ""))
            ),
            issue_body=payload.get("body", payload.get("issue_body", "")),
            timestamp=parse_timestamp(payload.get("timestamp")),
            labels=payload.get("labels"),
            url=payload.get("url", payload.get("issue_url")),
        )
    elif content_type == "form":
        return FormContent(
            form_fields=payload.get("fields", payload.get("form_fields", {})),
            submission_time=parse_timestamp(
                payload.get("submission_time", payload.get("timestamp"))
            ),
            form_id=payload.get("form_id", payload.get("id")),
            submitter_email=payload.get("submitter_email"),
            submitter_name=payload.get("submitter_name", payload.get("user")),
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
    category = None
    tags = []
    if request.metadata:
        if "priority" in request.metadata:
            try:
                priority = TicketPriority(request.metadata["priority"])
            except ValueError:
                pass
        if "category" in request.metadata:
            try:
                category = TicketCategory(request.metadata["category"])
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
    
    # Set category if provided
    if category:
        ticket.set_category(category)

    # Set status to TRIAGE_PENDING for immediate feedback (shows in Inbox)
    ticket.update_status(TicketStatus.TRIAGE_PENDING)

    # Allow optional title coming from metadata or payload (useful for form submissions)
    # Priority: metadata.title -> payload.fields.subject -> payload.fields.title -> payload.fields.message
    title_candidate = None
    if request.metadata and isinstance(request.metadata, dict):
        if "title" in request.metadata:
            title_candidate = request.metadata.get("title")

    if not title_candidate:
        payload_fields = (
            request.payload.get("fields") if isinstance(request.payload, dict) else None
        )
        if not payload_fields:
            payload_fields = (
                request.payload.get("form_fields")
                if isinstance(request.payload, dict)
                else None
            )

        if isinstance(payload_fields, dict):
            if "subject" in payload_fields:
                title_candidate = payload_fields.get("subject")
            elif "title" in payload_fields:
                title_candidate = payload_fields.get("title")
            elif "message" in payload_fields:
                title_candidate = payload_fields.get("message")

    if title_candidate:
        try:
            ticket.update_title(str(title_candidate))
        except Exception:
            # If updating title fails for any reason, continue without blocking ingestion
            pass

    # Extract description from form fields (important for AI processing)
    description_candidate = None
    if request.metadata and isinstance(request.metadata, dict):
        if "description" in request.metadata:
            description_candidate = request.metadata.get("description")

    if not description_candidate:
        payload_fields = (
            request.payload.get("fields") if isinstance(request.payload, dict) else None
        )
        if not payload_fields:
            payload_fields = (
                request.payload.get("form_fields")
                if isinstance(request.payload, dict)
                else None
            )

        if isinstance(payload_fields, dict):
            if "description" in payload_fields:
                description_candidate = payload_fields.get("description")
            elif "content" in payload_fields:
                description_candidate = payload_fields.get("content")
            elif "body" in payload_fields:
                description_candidate = payload_fields.get("body")
            elif "message" in payload_fields:
                description_candidate = payload_fields.get("message")

    if description_candidate:
        try:
            ticket.update_description(str(description_candidate))
        except Exception:
            # If updating description fails for any reason, continue without blocking ingestion
            pass

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

    # Coding agent trigger is now handled by QueueManager when AI assigns to coding-agent

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
            detail=f"Ticket is not in TRIAGE queue (currently in {ticket.current_queue.value})",
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

        ticket.mark_resolved(
            AutoResolveAction.FAQ_LINK
            if request.resolution_reason
            else AutoResolveAction.NONE
        )
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
    is_being_resolved = False
    old_status = ticket.status

    if request.title is not None:
        ticket.update_title(request.title)
        changes["title"] = request.title

    if request.description is not None:
        ticket.update_description(request.description)
        changes["description"] = request.description

    if request.status is not None:
        print(f"📝 Status update requested: {old_status.value} -> {request.status.value}")
        
        # Check if ticket is being resolved
        if request.status == TicketStatus.RESOLVED and old_status != TicketStatus.RESOLVED:
            print(f"🎯 Ticket is being RESOLVED!")
            is_being_resolved = True
            
            # Import AutoResolveAction enum
            from app.models import AutoResolveAction
            
            # Mark as resolved with MANUAL action
            ticket.mark_resolved(action=AutoResolveAction.MANUAL)
            
            # Move to RESOLUTION queue if not already there
            if ticket.current_queue != QueueType.RESOLUTION:
                print(f"📦 Moving ticket from {ticket.current_queue.value} to RESOLUTION queue")
                old_queue = ticket.current_queue
                queue_manager.move_ticket(
                    ticket_id=ticket_id,
                    from_queue=old_queue,
                    to_queue=QueueType.RESOLUTION,
                    ticket=ticket,
                    reason="manually resolved via status update"
                )
        else:
            ticket.update_status(request.status)
        
        changes["status"] = request.status.value

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
    print(f"💾 Ticket saved to repository")

    # If ticket is being resolved, trigger the resolution webhook
    if is_being_resolved:
        print(f"📡 Triggering resolution webhook for ticket {ticket_id}")
        background_tasks.add_task(
            event_publisher.publish_ticket_resolved,
            ticket,
            "Ticket resolved manually by agent",
        )
    elif changes:
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

    logger.info(
        f"Listing tickets with filters: status={status}, queue={queue}, priority={priority}, category={category}"
    )
    logger.info(f"Found {len(tickets)} tickets. Total in repository: {total}")
    for t in tickets:
        logger.info(
            f"Ticket: {t.id} - {t.title} - Status: {t.status} - Queue: {t.current_queue}"
        )

    return TicketListResponse(
        tickets=[t.to_dict() for t in tickets],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    request: ResolveTicketRequest,
    background_tasks: BackgroundTasks,
):
    """
    Mark a ticket as resolved and trigger webhook notification to respond to the user.
    
    This endpoint:
    1. Marks the ticket as RESOLVED
    2. Moves it to the RESOLUTION queue
    3. Sends a webhook to n8n with ticket data and source info
    4. n8n can then route the response back to the original source (Discord, Email, GitHub)
    """
    ticket = ticket_repository.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Import AutoResolveAction enum
    from app.models import AutoResolveAction

    # Map string action to enum
    action_map = {
        "MANUAL": AutoResolveAction.MANUAL,
        "FAQ_LINK": AutoResolveAction.FAQ_LINK,
        "AUTO_RESPONSE": AutoResolveAction.AUTO_RESPONSE,
        "REBOOT": AutoResolveAction.REBOOT,
        "CONFIG_CHANGE": AutoResolveAction.CONFIG_CHANGE,
        "NONE": AutoResolveAction.NONE,
    }
    
    action = action_map.get(
        request.resolution_action.upper() if request.resolution_action else "MANUAL",
        AutoResolveAction.MANUAL
    )

    # Mark as resolved
    old_queue = ticket.current_queue
    ticket.mark_resolved(action=action)
    
    # Move ticket to resolution queue if not already there
    if ticket.current_queue != QueueType.RESOLUTION:
        queue_manager.move_ticket(
            ticket_id=ticket_id,
            from_queue=old_queue,
            to_queue=QueueType.RESOLUTION,
            ticket=ticket,
            reason="manually resolved"
        )
    
    ticket_repository.save(ticket)

    # Publish resolution event (includes webhook to n8n)
    background_tasks.add_task(
        event_publisher.publish_ticket_resolved,
        ticket,
        request.resolution_message,
    )

    return {
        "ticket_id": ticket_id,
        "status": ticket.status.value,
        "queue": ticket.current_queue.value,
        "resolution_action": action.value,
        "message": "Ticket resolved. Notification will be sent to user via original channel.",
    }


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str, background_tasks: BackgroundTasks):
    """Delete a ticket by ID."""
    ticket = ticket_repository.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Remove from queue if present
    position = queue_manager.get_queue_position(ticket_id)
    if position:
        queue_name, _ = position
        queue_manager.remove_from_queue(ticket_id, queue_name)

    # Delete from repository
    deleted = ticket_repository.delete(ticket_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete ticket")

    return {
        "success": True,
        "ticket_id": ticket_id,
        "message": "Ticket deleted successfully",
    }
