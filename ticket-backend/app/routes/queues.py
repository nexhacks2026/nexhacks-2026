"""Queue management API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models import QueueType, Ticket
from app.storage import ticket_repository
from app.queues import queue_manager
from app.events import event_publisher

router = APIRouter(prefix="/api/queues", tags=["queues"])


# Request/Response Models

class MoveTicketRequest(BaseModel):
    """Request to move a ticket between queues."""
    ticket_id: str
    from_queue: QueueType
    to_queue: QueueType
    reason: Optional[str] = None
    actor: Optional[str] = None


class DequeueResponse(BaseModel):
    """Response after dequeuing a ticket."""
    ticket_id: Optional[str]
    ticket: Optional[dict[str, Any]]
    queue: str


class QueueStatsResponse(BaseModel):
    """Response for queue statistics."""
    queue: str
    count: int
    avg_wait_time_seconds: float
    oldest_ticket_age_seconds: float
    newest_ticket_age_seconds: float


class AllQueuesResponse(BaseModel):
    """Response for all queue statistics."""
    queues: list[dict[str, Any]]
    total_tickets: int


class QueueDetailsResponse(BaseModel):
    """Response for detailed queue information."""
    queue: str
    stats: dict[str, Any]
    tickets: list[dict[str, Any]]


# Endpoints

@router.get("", response_model=AllQueuesResponse)
async def list_all_queues():
    """List all queues with their statistics."""
    stats = queue_manager.get_all_queue_stats()
    total = sum(s.count for s in stats)

    return AllQueuesResponse(
        queues=[s.to_dict() for s in stats],
        total_tickets=total,
    )


@router.get("/{queue_name}", response_model=QueueDetailsResponse)
async def get_queue_details(
    queue_name: str,
    limit: int = 20,
):
    """Get detailed information about a specific queue."""
    try:
        queue = QueueType(queue_name.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")

    stats = queue_manager.get_queue_stats(queue)
    ticket_ids = queue_manager.peek_queue(queue, limit=limit)

    # Get ticket details
    tickets = []
    for tid in ticket_ids:
        ticket = ticket_repository.get(tid)
        if ticket:
            ticket_dict = ticket.to_dict()
            position = queue_manager.get_queue_position(tid)
            if position:
                ticket_dict["queue_position"] = position[1]
            tickets.append(ticket_dict)

    return QueueDetailsResponse(
        queue=queue.value,
        stats=stats.to_dict(),
        tickets=tickets,
    )


@router.post("/{queue_name}/dequeue", response_model=DequeueResponse)
async def dequeue_ticket(
    queue_name: str,
    priority_based: bool = True,
):
    """
    Dequeue the next ticket from a queue.
    Returns the ticket that was dequeued.
    """
    try:
        queue = QueueType(queue_name.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")

    ticket_id = queue_manager.dequeue(queue, priority_based=priority_based)

    if not ticket_id:
        return DequeueResponse(
            ticket_id=None,
            ticket=None,
            queue=queue.value,
        )

    ticket = ticket_repository.get(ticket_id)
    ticket_dict = ticket.to_dict() if ticket else None

    return DequeueResponse(
        ticket_id=ticket_id,
        ticket=ticket_dict,
        queue=queue.value,
    )


@router.post("/move")
async def move_ticket(
    request: MoveTicketRequest,
    background_tasks: BackgroundTasks,
):
    """Move a ticket between queues."""
    ticket = ticket_repository.get(request.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Validate current queue
    current_queue = queue_manager.get_ticket_queue(request.ticket_id)
    if current_queue != request.from_queue:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket is not in {request.from_queue.value} queue"
        )

    try:
        # Update ticket state
        ticket.move_to_queue(request.to_queue)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Move in queue manager
    success = queue_manager.move_ticket(
        ticket_id=request.ticket_id,
        from_queue=request.from_queue,
        to_queue=request.to_queue,
        ticket=ticket,
        reason=request.reason or "manual move",
        actor=request.actor,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to move ticket in queue")

    ticket_repository.save(ticket)

    # Publish event
    background_tasks.add_task(
        event_publisher.publish_ticket_moved,
        ticket,
        request.from_queue,
        request.to_queue,
    )

    return {
        "ticket_id": request.ticket_id,
        "from_queue": request.from_queue.value,
        "to_queue": request.to_queue.value,
        "status": ticket.status.value,
    }


@router.get("/{queue_name}/peek")
async def peek_queue(
    queue_name: str,
    limit: int = 10,
    priority_based: bool = True,
):
    """Peek at the next N tickets in a queue without removing them."""
    try:
        queue = QueueType(queue_name.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")

    ticket_ids = queue_manager.peek_queue(
        queue,
        limit=limit,
        priority_based=priority_based,
    )

    tickets = []
    for i, tid in enumerate(ticket_ids):
        ticket = ticket_repository.get(tid)
        if ticket:
            tickets.append({
                "position": i + 1,
                "ticket_id": tid,
                "priority": ticket.priority.value,
                "category": ticket.category.value if ticket.category else None,
                "created_at": ticket.created_at.isoformat(),
                "sender": ticket.content.sender,
            })

    return {
        "queue": queue.value,
        "count": len(tickets),
        "tickets": tickets,
    }


@router.get("/{queue_name}/stats", response_model=QueueStatsResponse)
async def get_queue_stats(queue_name: str):
    """Get statistics for a specific queue."""
    try:
        queue = QueueType(queue_name.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")

    stats = queue_manager.get_queue_stats(queue)

    return QueueStatsResponse(
        queue=stats.queue_type.value,
        count=stats.count,
        avg_wait_time_seconds=stats.avg_wait_time_seconds,
        oldest_ticket_age_seconds=stats.oldest_ticket_age_seconds,
        newest_ticket_age_seconds=stats.newest_ticket_age_seconds,
    )
