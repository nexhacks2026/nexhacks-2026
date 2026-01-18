"""Enum definitions for the ticket management system."""

from enum import Enum


class TicketStatus(str, Enum):
    """Status of a ticket in the system."""

    INBOX = "INBOX"
    TRIAGING = "TRIAGING"
    TRIAGE_PENDING = "TRIAGE_PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(str, Enum):
    """Priority level of a ticket."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketCategory(str, Enum):
    """Category classification of a ticket."""

    BILLING = "BILLING"
    TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    BUG_REPORT = "BUG_REPORT"
    ADMIN = "ADMIN"
    OTHER = "OTHER"


class QueueType(str, Enum):
    """Types of queues in the ticket processing system."""

    INBOX = "INBOX"
    TRIAGE = "TRIAGE"
    ASSIGNMENT = "ASSIGNMENT"
    ACTIVE = "ACTIVE"
    RESOLUTION = "RESOLUTION"


class TicketSource(str, Enum):
    """Source of the ticket ingestion."""

    EMAIL = "EMAIL"
    DISCORD = "DISCORD"
    GITHUB = "GITHUB"
    FORM = "FORM"
    WEBHOOK = "WEBHOOK"


class AutoResolveAction(str, Enum):
    """Actions that can be taken for auto-resolution."""

    MANUAL = "MANUAL"
    FAQ_LINK = "FAQ_LINK"
    AUTO_RESPONSE = "AUTO_RESPONSE"
    REBOOT = "REBOOT"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    DUPLICATE_CLOSE = "DUPLICATE_CLOSE"
    SELF_SERVICE_REDIRECT = "SELF_SERVICE_REDIRECT"
    NONE = "NONE"


# Valid state transitions for tickets
VALID_TRANSITIONS: dict[TicketStatus, list[TicketStatus]] = {
    TicketStatus.INBOX: [TicketStatus.TRIAGING, TicketStatus.TRIAGE_PENDING],
    TicketStatus.TRIAGING: [
        TicketStatus.TRIAGE_PENDING,
        TicketStatus.ASSIGNED,
        TicketStatus.RESOLVED,
    ],
    TicketStatus.TRIAGE_PENDING: [
        TicketStatus.ASSIGNED,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    ],
    TicketStatus.ASSIGNED: [
        TicketStatus.IN_PROGRESS,
        TicketStatus.RESOLVED,
        TicketStatus.INBOX,
        TicketStatus.CLOSED,
    ],
    TicketStatus.IN_PROGRESS: [
        TicketStatus.RESOLVED,
        TicketStatus.ASSIGNED,
        TicketStatus.INBOX,
        TicketStatus.CLOSED,
    ],
    TicketStatus.RESOLVED: [
        TicketStatus.IN_PROGRESS,
        TicketStatus.CLOSED,
    ],  # Can reopen if needed
    TicketStatus.CLOSED: [TicketStatus.INBOX],  # Can reopen
}


# Queue to status mapping
QUEUE_STATUS_MAP: dict[QueueType, TicketStatus] = {
    QueueType.INBOX: TicketStatus.INBOX,
    QueueType.TRIAGE: TicketStatus.TRIAGE_PENDING,
    QueueType.ASSIGNMENT: TicketStatus.ASSIGNED,
    QueueType.ACTIVE: TicketStatus.IN_PROGRESS,
    QueueType.RESOLUTION: TicketStatus.RESOLVED,
}
