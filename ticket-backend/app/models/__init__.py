"""Models package for the ticket management system."""

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
from .base import BaseTicket, TicketContent
from .content import (
    EmailContent,
    DiscordContent,
    GitHubContent,
    FormContent,
    content_from_dict,
)
from .ticket import Ticket, InvalidStateTransitionError

__all__ = [
    # Enums
    "AutoResolveAction",
    "QueueType",
    "TicketCategory",
    "TicketPriority",
    "TicketSource",
    "TicketStatus",
    "VALID_TRANSITIONS",
    "QUEUE_STATUS_MAP",
    # Base classes
    "BaseTicket",
    "TicketContent",
    # Content types
    "EmailContent",
    "DiscordContent",
    "GitHubContent",
    "FormContent",
    "content_from_dict",
    # Ticket
    "Ticket",
    "InvalidStateTransitionError",
]
