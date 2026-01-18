"""Ticket distribution API for assigning and claiming tickets."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models import QueueType, Ticket
from app.storage import ticket_repository, assignment_tracker
from app.queues import queue_manager
from app.events import event_publisher

router = APIRouter(prefix="/api/distribution", tags=["distribution"])


# Request/Response Models


class ClaimRequest(BaseModel):
    """Request to claim the next available ticket."""

    agent_id: str
    preferred_categories: Optional[list[str]] = None
    max_priority: Optional[str] = None


class AssignRequest(BaseModel):
    """Request to assign a specific ticket to an agent."""

    ticket_id: str
    agent_id: str
    reason: Optional[str] = None


class ReleaseRequest(BaseModel):
    """Request to release a ticket back to the assignment queue."""

    ticket_id: str
    agent_id: str
    reason: Optional[str] = None
    retriage: Optional[bool] = False  # If true, send back to INBOX for AI re-triage


class TransferRequest(BaseModel):
    """Request to transfer a ticket to another agent."""

    ticket_id: str
    from_agent_id: str
    to_agent_id: str
    reason: Optional[str] = None


class ClaimResponse(BaseModel):
    """Response after claiming a ticket."""

    success: bool
    ticket_id: Optional[str]
    ticket: Optional[dict[str, Any]]
    message: str


class AssignmentResponse(BaseModel):
    """Response for assignment operations."""

    success: bool
    ticket_id: str
    agent_id: str
    status: str
    queue: str
    message: str


class AvailableTicketsResponse(BaseModel):
    """Response for available tickets."""

    tickets: list[dict[str, Any]]
    count: int


class AgentTicketsResponse(BaseModel):
    """Response for agent's assigned tickets."""

    agent_id: str
    tickets: list[dict[str, Any]]
    count: int


# Endpoints


@router.post("/claim", response_model=ClaimResponse)
async def claim_ticket(
    request: ClaimRequest,
    background_tasks: BackgroundTasks,
):
    """
    Agent claims the next available ticket from the assignment queue.
    Uses priority-based selection by default.
    """
    # Get available tickets
    ticket_ids = queue_manager.peek_queue(
        QueueType.ASSIGNMENT,
        limit=20,
        priority_based=True,
    )

    if not ticket_ids:
        return ClaimResponse(
            success=False,
            ticket_id=None,
            ticket=None,
            message="No tickets available for claiming",
        )

    # Find best match based on preferences
    claimed_ticket: Optional[Ticket] = None

    for tid in ticket_ids:
        ticket = ticket_repository.get(tid)
        if not ticket:
            continue

        # Skip if already assigned
        if ticket.assignee:
            continue

        # Apply category filter if specified
        if request.preferred_categories:
            from app.models import TicketCategory

            if ticket.category:
                if ticket.category.value not in request.preferred_categories:
                    continue

        # Apply priority filter if specified
        if request.max_priority:
            from app.models import TicketPriority

            priority_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            max_idx = priority_order.index(request.max_priority.upper())
            ticket_idx = priority_order.index(ticket.priority.value)
            if ticket_idx > max_idx:
                continue

        claimed_ticket = ticket
        break

    if not claimed_ticket:
        return ClaimResponse(
            success=False,
            ticket_id=None,
            ticket=None,
            message="No matching tickets available",
        )

    # Assign the ticket
    old_queue = claimed_ticket.current_queue
    claimed_ticket.assign(request.agent_id)
    claimed_ticket.move_to_queue(QueueType.ACTIVE)

    # Update queue
    queue_manager.move_ticket(
        ticket_id=claimed_ticket.id,
        from_queue=QueueType.ASSIGNMENT,
        to_queue=QueueType.ACTIVE,
        ticket=claimed_ticket,
        reason=f"claimed by agent {request.agent_id}",
        actor=request.agent_id,
    )

    # Track assignment
    assignment_tracker.assign(request.agent_id, claimed_ticket.id)

    # Save ticket
    ticket_repository.save(claimed_ticket)

    # Publish events
    background_tasks.add_task(
        event_publisher.publish_ticket_assigned,
        claimed_ticket,
        request.agent_id,
        None,
    )
    background_tasks.add_task(
        event_publisher.publish_ticket_moved,
        claimed_ticket,
        old_queue,
        QueueType.ACTIVE,
    )

    return ClaimResponse(
        success=True,
        ticket_id=claimed_ticket.id,
        ticket=claimed_ticket.to_dict(),
        message=f"Ticket claimed successfully",
    )


@router.post("/assign", response_model=AssignmentResponse)
async def assign_ticket(
    request: AssignRequest,
    background_tasks: BackgroundTasks,
):
    """Assign a specific ticket to a specific agent."""
    ticket = ticket_repository.get(request.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_assignee = ticket.assignee
    old_queue = ticket.current_queue

    # Assign ticket (this will set status to ASSIGNED and queue to ASSIGNMENT)
    ticket.assign(request.agent_id)

    # Update queue manager
    if old_queue != ticket.current_queue:
        queue_manager.move_ticket(
            ticket_id=request.ticket_id,
            from_queue=old_queue,
            to_queue=ticket.current_queue,
            ticket=ticket,
            reason=request.reason or f"assigned to {request.agent_id}",
            actor=request.agent_id,
        )

    # Track assignment
    assignment_tracker.assign(request.agent_id, ticket.id)

    ticket_repository.save(ticket)

    # Publish events
    background_tasks.add_task(
        event_publisher.publish_ticket_assigned,
        ticket,
        request.agent_id,
        old_assignee,
    )

    if old_queue != ticket.current_queue:
        background_tasks.add_task(
            event_publisher.publish_ticket_moved,
            ticket,
            old_queue,
            ticket.current_queue,
        )

    return AssignmentResponse(
        success=True,
        ticket_id=ticket.id,
        agent_id=request.agent_id,
        status=ticket.status.value,
        queue=ticket.current_queue.value,
        message="Ticket assigned successfully",
    )


@router.post("/release", response_model=AssignmentResponse)
async def release_ticket(
    request: ReleaseRequest,
    background_tasks: BackgroundTasks,
):
    """Release a ticket back to the assignment queue or inbox for re-triage."""
    ticket = ticket_repository.get(request.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.assignee != request.agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only release tickets assigned to you",
        )

    old_queue = ticket.current_queue
    old_assignee = ticket.assignee

    # Unassign (this will set status and queue appropriately)
    ticket.unassign()

    # Determine target queue based on retriage flag
    if request.retriage:
        # Send back to INBOX for AI re-triage
        from app.models import TicketStatus
        ticket.update_status(TicketStatus.TRIAGE_PENDING)
        target_queue = QueueType.INBOX
        
        # Clear old AI reasoning and response data for fresh re-triage
        ticket.clear_ai_data()
    else:
        # Use the queue set by unassign() (typically ASSIGNMENT)
        target_queue = ticket.current_queue

    if old_queue == QueueType.ACTIVE:
        queue_manager.move_ticket(
            ticket_id=request.ticket_id,
            from_queue=QueueType.ACTIVE,
            to_queue=target_queue,
            ticket=ticket,
            reason=request.reason or ("re-triage requested" if request.retriage else "released by agent"),
            actor=request.agent_id,
        )
    else:
        # Enqueue to target queue (INBOX will trigger AI triage)
        queue_manager.enqueue(
            ticket=ticket,
            queue=target_queue,
            reason=request.reason or ("re-triage requested" if request.retriage else "released by agent"),
            actor=request.agent_id,
        )

    # Remove from assignment tracker
    assignment_tracker.unassign(request.agent_id, ticket.id)

    ticket_repository.save(ticket)

    # Publish events
    background_tasks.add_task(
        event_publisher.publish_ticket_moved,
        ticket,
        old_queue,
        target_queue,
    )
    
    # If re-triaging, publish unassigned event
    if request.retriage:
        background_tasks.add_task(
            event_publisher.publish_ticket_assigned,
            ticket,
            None,  # No new assignee
            old_assignee,
        )

    return AssignmentResponse(
        success=True,
        ticket_id=ticket.id,
        agent_id=request.agent_id,
        status=ticket.status.value,
        queue=target_queue.value,
        message="Ticket released for re-triage" if request.retriage else "Ticket released successfully",
    )


@router.post("/transfer", response_model=AssignmentResponse)
async def transfer_ticket(
    request: TransferRequest,
    background_tasks: BackgroundTasks,
):
    """Transfer a ticket from one agent to another."""
    ticket = ticket_repository.get(request.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.assignee != request.from_agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only transfer tickets assigned to you",
        )

    # Update assignment
    old_assignee = ticket.assignee
    ticket.assign(request.to_agent_id)

    # Update tracker
    assignment_tracker.unassign(request.from_agent_id, ticket.id)
    assignment_tracker.assign(request.to_agent_id, ticket.id)

    ticket_repository.save(ticket)

    # Publish event
    background_tasks.add_task(
        event_publisher.publish_ticket_assigned,
        ticket,
        request.to_agent_id,
        old_assignee,
    )

    return AssignmentResponse(
        success=True,
        ticket_id=ticket.id,
        agent_id=request.to_agent_id,
        status=ticket.status.value,
        queue=ticket.current_queue.value,
        message=f"Ticket transferred from {request.from_agent_id} to {request.to_agent_id}",
    )


@router.get("/available", response_model=AvailableTicketsResponse)
async def get_available_tickets(
    limit: int = 50,
    category: Optional[str] = None,
    priority: Optional[str] = None,
):
    """List available tickets for claiming."""
    ticket_ids = queue_manager.peek_queue(
        QueueType.ASSIGNMENT,
        limit=limit * 2,  # Fetch more to account for filtering
        priority_based=True,
    )

    tickets = []
    for tid in ticket_ids:
        ticket = ticket_repository.get(tid)
        if not ticket or ticket.assignee:
            continue

        # Apply filters
        if category and ticket.category:
            if ticket.category.value != category.upper():
                continue

        if priority:
            if ticket.priority.value != priority.upper():
                continue

        ticket_dict = ticket.to_dict()
        position = queue_manager.get_queue_position(tid)
        if position:
            ticket_dict["queue_position"] = position[1]

        tickets.append(ticket_dict)

        if len(tickets) >= limit:
            break

    return AvailableTicketsResponse(
        tickets=tickets,
        count=len(tickets),
    )


@router.get("/my-tickets", response_model=AgentTicketsResponse)
async def get_agent_tickets(agent_id: str):
    """Get all tickets assigned to an agent."""
    ticket_ids = assignment_tracker.get_agent_tickets(agent_id)

    tickets = []
    for tid in ticket_ids:
        ticket = ticket_repository.get(tid)
        if ticket:
            tickets.append(ticket.to_dict())

    # Sort by priority (critical first) and then by created_at
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    tickets.sort(
        key=lambda t: (
            priority_order.get(t["priority"], 4),
            t["created_at"],
        )
    )

    return AgentTicketsResponse(
        agent_id=agent_id,
        tickets=tickets,
        count=len(tickets),
    )


@router.get("/agent-stats/{agent_id}")
async def get_agent_stats(agent_id: str):
    """Get statistics for an agent's workload."""
    ticket_ids = assignment_tracker.get_agent_tickets(agent_id)

    stats = {
        "total": len(ticket_ids),
        "by_priority": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        "by_category": {},
        "by_status": {},
    }

    for tid in ticket_ids:
        ticket = ticket_repository.get(tid)
        if ticket:
            stats["by_priority"][ticket.priority.value] += 1

            cat = ticket.category.value if ticket.category else "UNCATEGORIZED"
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

            stats["by_status"][ticket.status.value] = (
                stats["by_status"].get(ticket.status.value, 0) + 1
            )

    return {
        "agent_id": agent_id,
        "stats": stats,
    }
