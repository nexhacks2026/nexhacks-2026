"""In-memory storage with PostgreSQL-ready interface."""

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Optional

from app.models import (
    Ticket,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    QueueType,
)


class TicketRepository:
    """In-memory ticket storage with CRUD operations."""

    def __init__(self):
        self._tickets: dict[str, Ticket] = {}
        self._lock = Lock()

    def save(self, ticket: Ticket) -> Ticket:
        """Save or update a ticket."""
        with self._lock:
            self._tickets[ticket.id] = ticket
            return ticket

    def get(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID."""
        with self._lock:
            return self._tickets.get(ticket_id)

    def get_all(self) -> list[Ticket]:
        """Get all tickets."""
        with self._lock:
            return list(self._tickets.values())

    def delete(self, ticket_id: str) -> bool:
        """Delete a ticket by ID."""
        with self._lock:
            if ticket_id in self._tickets:
                del self._tickets[ticket_id]
                return True
            return False

    def exists(self, ticket_id: str) -> bool:
        """Check if a ticket exists."""
        with self._lock:
            return ticket_id in self._tickets

    def count(self) -> int:
        """Get total ticket count."""
        with self._lock:
            return len(self._tickets)

    def find_by_status(self, status: TicketStatus) -> list[Ticket]:
        """Find tickets by status."""
        with self._lock:
            return [t for t in self._tickets.values() if t.status == status]

    def find_by_queue(self, queue: QueueType) -> list[Ticket]:
        """Find tickets by queue."""
        with self._lock:
            return [t for t in self._tickets.values() if t.current_queue == queue]

    def find_by_assignee(self, assignee: str) -> list[Ticket]:
        """Find tickets by assignee."""
        with self._lock:
            return [t for t in self._tickets.values() if t.assignee == assignee]

    def find_by_priority(self, priority: TicketPriority) -> list[Ticket]:
        """Find tickets by priority."""
        with self._lock:
            return [t for t in self._tickets.values() if t.priority == priority]

    def find_by_category(self, category: TicketCategory) -> list[Ticket]:
        """Find tickets by category."""
        with self._lock:
            return [t for t in self._tickets.values() if t.category == category]

    def find(
        self,
        status: Optional[TicketStatus] = None,
        queue: Optional[QueueType] = None,
        assignee: Optional[str] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """Find tickets with multiple filters."""
        with self._lock:
            results = list(self._tickets.values())

            if status:
                results = [t for t in results if t.status == status]
            if queue:
                results = [t for t in results if t.current_queue == queue]
            if assignee:
                results = [t for t in results if t.assignee == assignee]
            if priority:
                results = [t for t in results if t.priority == priority]
            if category:
                results = [t for t in results if t.category == category]

            # Sort by created_at descending (newest first)
            results.sort(key=lambda t: t.created_at, reverse=True)

            return results[offset : offset + limit]

    def get_unassigned_in_assignment_queue(self) -> list[Ticket]:
        """Get tickets in assignment queue that don't have an assignee yet."""
        with self._lock:
            return [
                t for t in self._tickets.values()
                if t.current_queue == QueueType.ASSIGNMENT and t.assignee is None
            ]


class AssignmentTracker:
    """Track ticket assignments per agent."""

    def __init__(self):
        self._assignments: dict[str, set[str]] = {}  # agent_id -> set of ticket_ids
        self._lock = Lock()

    def assign(self, agent_id: str, ticket_id: str) -> None:
        """Record an assignment."""
        with self._lock:
            if agent_id not in self._assignments:
                self._assignments[agent_id] = set()
            self._assignments[agent_id].add(ticket_id)

    def unassign(self, agent_id: str, ticket_id: str) -> None:
        """Remove an assignment."""
        with self._lock:
            if agent_id in self._assignments:
                self._assignments[agent_id].discard(ticket_id)

    def get_agent_tickets(self, agent_id: str) -> set[str]:
        """Get all ticket IDs assigned to an agent."""
        with self._lock:
            return self._assignments.get(agent_id, set()).copy()

    def get_agent_ticket_count(self, agent_id: str) -> int:
        """Get count of tickets assigned to an agent."""
        with self._lock:
            return len(self._assignments.get(agent_id, set()))

    def find_ticket_agent(self, ticket_id: str) -> Optional[str]:
        """Find which agent a ticket is assigned to."""
        with self._lock:
            for agent_id, tickets in self._assignments.items():
                if ticket_id in tickets:
                    return agent_id
            return None

    def get_all_assignments(self) -> dict[str, set[str]]:
        """Get all assignments."""
        with self._lock:
            return {k: v.copy() for k, v in self._assignments.items()}


# Global repository instances
ticket_repository = TicketRepository()
assignment_tracker = AssignmentTracker()
