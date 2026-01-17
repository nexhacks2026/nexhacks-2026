"""Queues package for ticket management."""

from .manager import QueueManager, QueueStats, QueueEntry, AuditLogEntry, queue_manager

__all__ = [
    "QueueManager",
    "QueueStats",
    "QueueEntry",
    "AuditLogEntry",
    "queue_manager",
]
