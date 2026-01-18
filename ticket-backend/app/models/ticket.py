"""Concrete Ticket model implementation."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseTicket, TicketContent
from .content import content_from_dict
from .enums import (
    AutoResolveAction,
    QueueType,
    TicketCategory,
    TicketPriority,
    TicketSource,
    TicketStatus,
    VALID_TRANSITIONS,
    QUEUE_STATUS_MAP,
)


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    pass


class Ticket(BaseTicket):
    """Concrete ticket implementation."""

    def __init__(
        self,
        id: str,
        created_at: datetime,
        updated_at: datetime,
        source: TicketSource,
        content: TicketContent,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: Optional[TicketCategory] = None,
        status: TicketStatus = TicketStatus.INBOX,
        current_queue: QueueType = QueueType.INBOX,
        assignee: Optional[str] = None,
        tags: Optional[list[str]] = None,
        ai_reasoning: Optional[dict[str, Any]] = None,
        resolution_action: AutoResolveAction = AutoResolveAction.NONE,
        suggested_assignee: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self._id = id
        self._created_at = created_at
        self._updated_at = updated_at
        self._source = source
        self._content = content
        self._priority = priority
        self._category = category
        self._status = status
        self._current_queue = current_queue
        self._assignee = assignee
        self._tags = tags or []
        self._ai_reasoning = ai_reasoning or {}
        self._resolution_action = resolution_action
        self._suggested_assignee = suggested_assignee
        self._title = title
        self._description = description

    @classmethod
    def create(
        cls,
        source: TicketSource,
        content: TicketContent,
        priority: TicketPriority = TicketPriority.MEDIUM,
        tags: Optional[list[str]] = None,
    ) -> "Ticket":
        """Factory method to create a new ticket with generated ID and timestamps."""
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            source=source,
            content=content,
            priority=priority,
            tags=tags,
        )

    # Property implementations
    @property
    def id(self) -> str:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def source(self) -> TicketSource:
        return self._source

    @property
    def priority(self) -> TicketPriority:
        return self._priority

    @property
    def category(self) -> Optional[TicketCategory]:
        return self._category

    @property
    def status(self) -> TicketStatus:
        return self._status

    @property
    def current_queue(self) -> QueueType:
        return self._current_queue

    @property
    def content(self) -> TicketContent:
        return self._content

    @property
    def assignee(self) -> Optional[str]:
        return self._assignee

    @property
    def tags(self) -> list[str]:
        return self._tags

    @property
    def ai_reasoning(self) -> dict[str, Any]:
        return self._ai_reasoning

    @property
    def resolution_action(self) -> AutoResolveAction:
        return self._resolution_action

    @property
    def suggested_assignee(self) -> Optional[str]:
        return self._suggested_assignee

    @property
    def title(self) -> str:
        """Get ticket title, falling back to content-based title if not set."""
        if self._title:
            return self._title
        # Fallback to extracting from content
        content_dict = self._content.to_dict()
        if "subject" in content_dict:
            return content_dict["subject"]
        elif "issue_title" in content_dict:
            return content_dict["issue_title"]
        elif "message_text" in content_dict:
            return content_dict["message_text"][:100]
        return "Untitled Ticket"

    @property
    def description(self) -> str:
        """Get ticket description, falling back to content-based description if not set."""
        if self._description:
            return self._description
        # Fallback to extracting from content
        content_dict = self._content.to_dict()
        if "body" in content_dict:
            return content_dict["body"]
        elif "issue_body" in content_dict:
            return content_dict["issue_body"]
        elif "message_text" in content_dict:
            return content_dict["message_text"]
        return ""

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self._updated_at = datetime.now(timezone.utc)

    def _can_transition_to(self, new_status: TicketStatus) -> bool:
        """Check if transition to new status is valid."""
        return new_status in VALID_TRANSITIONS.get(self._status, [])

    def move_to_queue(self, queue: QueueType) -> None:
        """Move ticket to a different queue with state validation."""
        new_status = QUEUE_STATUS_MAP[queue]

        # Allow moving to INBOX from any state (reset/escalation)
        if queue == QueueType.INBOX:
            self._status = TicketStatus.INBOX
            self._current_queue = queue
            self._touch()
            return

        if not self._can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self._status.value} to {new_status.value}"
            )

        self._status = new_status
        self._current_queue = queue
        self._touch()

    def assign(self, assignee: str) -> None:
        """Assign ticket to a user."""
        self._assignee = assignee
        # Move from INBOX/TRIAGE_PENDING to ASSIGNED when first assigned
        if self._status in (TicketStatus.INBOX, TicketStatus.TRIAGE_PENDING):
            self._status = TicketStatus.ASSIGNED
            self._current_queue = QueueType.ASSIGNMENT
        # Keep current status when reassigning (e.g., ASSIGNED stays ASSIGNED, IN_PROGRESS stays IN_PROGRESS)
        self._touch()

    def unassign(self) -> None:
        """Remove assignment from ticket."""
        self._assignee = None
        # Always move back to INBOX when unassigned (regardless of current status)
        self._status = TicketStatus.INBOX
        self._current_queue = QueueType.INBOX
        self._touch()

    def update_priority(self, priority: TicketPriority) -> None:
        """Update the ticket priority."""
        self._priority = priority
        self._touch()

    def update_status(self, status: TicketStatus) -> None:
        """Update the ticket status directly (bypasses transition validation)."""
        self._status = status
        self._touch()

    def update_title(self, title: str) -> None:
        """Update the ticket title."""
        self._title = title
        self._touch()

    def update_description(self, description: str) -> None:
        """Update the ticket description."""
        self._description = description
        self._touch()

    def set_category(self, category: TicketCategory) -> None:
        """Set the ticket category."""
        self._category = category
        self._touch()

    def log_reasoning(self, reasoning: dict[str, Any]) -> None:
        """Log AI reasoning/classification data."""
        self._ai_reasoning.update(reasoning)
        self._touch()

    def set_suggested_assignee(self, assignee: str) -> None:
        """Set the AI-suggested assignee."""
        self._suggested_assignee = assignee
        self._touch()

    def mark_resolved(self, action: AutoResolveAction = AutoResolveAction.NONE) -> None:
        """Mark ticket as resolved."""
        if not self._can_transition_to(TicketStatus.RESOLVED):
            raise InvalidStateTransitionError(
                f"Cannot mark as resolved from {self._status.value}"
            )
        self._status = TicketStatus.RESOLVED
        self._current_queue = QueueType.RESOLUTION
        self._resolution_action = action
        self._touch()

    def close(self) -> None:
        """Close the ticket (terminal state)."""
        if self._status != TicketStatus.RESOLVED:
            raise InvalidStateTransitionError(
                f"Cannot close ticket from {self._status.value}, must be RESOLVED first"
            )
        self._status = TicketStatus.CLOSED
        self._touch()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the ticket."""
        if tag not in self._tags:
            self._tags.append(tag)
            self._touch()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the ticket."""
        if tag in self._tags:
            self._tags.remove(tag)
            self._touch()

    def add_ai_response(self, response: str, source_docs: list[str] = None) -> None:
        """Store AI-generated response for auto-resolved tickets."""
        self._ai_reasoning["auto_response"] = response
        self._ai_reasoning["auto_resolved"] = True
        self._ai_reasoning["source_docs"] = source_docs or []
        self._touch()

    def clear_ai_data(self) -> None:
        """Clear all AI reasoning, response data, category, and priority (used when re-triaging)."""
        self._ai_reasoning = {}
        self._category = None
        self._priority = None
        self._suggested_assignee = None
        self._touch()

    def validate(self) -> bool:
        """Validate the ticket data."""
        if not self._id:
            return False
        if not self._created_at or not self._updated_at:
            return False
        if not self._content:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert ticket to dictionary representation."""
        return {
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "source": self._source.value,
            "priority": self._priority.value,
            "category": self._category.value if self._category else None,
            "status": self._status.value,
            "current_queue": self._current_queue.value,
            "content": self._content.to_dict(),
            "assignee": self._assignee,
            "tags": self._tags,
            "ai_reasoning": self._ai_reasoning,
            "resolution_action": self._resolution_action.value,
            "suggested_assignee": self._suggested_assignee,
            "title": self.title,
            "description": self.description,
        }

    def to_json(self) -> str:
        """Convert ticket to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Ticket":
        """Create ticket instance from dictionary."""
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            created_at=created_at,
            updated_at=updated_at,
            source=TicketSource(data["source"]),
            content=content_from_dict(data["content"]),
            priority=TicketPriority(data.get("priority", "MEDIUM")),
            category=TicketCategory(data["category"]) if data.get("category") else None,
            status=TicketStatus(data.get("status", "INBOX")),
            current_queue=QueueType(data.get("current_queue", "INBOX")),
            assignee=data.get("assignee"),
            tags=data.get("tags", []),
            ai_reasoning=data.get("ai_reasoning", {}),
            resolution_action=AutoResolveAction(data.get("resolution_action", "NONE")),
            suggested_assignee=data.get("suggested_assignee"),
            title=data.get("title"),
            description=data.get("description"),
        )

    def __repr__(self) -> str:
        return (
            f"Ticket(id={self._id!r}, status={self._status.value}, "
            f"queue={self._current_queue.value}, priority={self._priority.value})"
        )
