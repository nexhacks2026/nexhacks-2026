"""Abstract base classes for the ticket management system."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from .enums import (
    TicketStatus,
    TicketPriority,
    TicketCategory,
    TicketSource,
    QueueType,
    AutoResolveAction,
)


class TicketContent(ABC):
    """Abstract base class for different input types (email, message, form submission)."""

    @property
    @abstractmethod
    def raw_content(self) -> str:
        """The raw content of the ticket input."""
        pass

    @property
    @abstractmethod
    def sender(self) -> str:
        """The sender/author of the content."""
        pass

    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """When the content was created/received."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Additional metadata about the content."""
        pass

    @abstractmethod
    def extract_body(self) -> str:
        """Extract the main body/text content."""
        pass

    @abstractmethod
    def extract_attachments(self) -> list[dict[str, Any]]:
        """Extract any attachments from the content."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "TicketContent":
        """Create instance from dictionary."""
        pass


class BaseTicket(ABC):
    """Abstract base class defining the interface all tickets must follow."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the ticket (UUID)."""
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Timestamp when the ticket was created."""
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """Timestamp when the ticket was last updated."""
        pass

    @property
    @abstractmethod
    def source(self) -> TicketSource:
        """Source of the ticket (email, discord, etc.)."""
        pass

    @property
    @abstractmethod
    def priority(self) -> TicketPriority:
        """Priority level of the ticket."""
        pass

    @property
    @abstractmethod
    def category(self) -> Optional[TicketCategory]:
        """Category of the ticket (may be None until triaged)."""
        pass

    @property
    @abstractmethod
    def status(self) -> TicketStatus:
        """Current status of the ticket."""
        pass

    @property
    @abstractmethod
    def current_queue(self) -> QueueType:
        """Current queue the ticket is in."""
        pass

    @property
    @abstractmethod
    def content(self) -> TicketContent:
        """The content of the ticket."""
        pass

    @property
    @abstractmethod
    def assignee(self) -> Optional[str]:
        """Currently assigned user (if any)."""
        pass

    @property
    @abstractmethod
    def tags(self) -> list[str]:
        """List of tags associated with the ticket."""
        pass

    @property
    @abstractmethod
    def ai_reasoning(self) -> dict[str, Any]:
        """AI classification reasoning and metadata."""
        pass

    @property
    @abstractmethod
    def resolution_action(self) -> AutoResolveAction:
        """Auto-resolution action if applicable."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the ticket data."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert ticket to dictionary representation."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseTicket":
        """Create ticket instance from dictionary."""
        pass
