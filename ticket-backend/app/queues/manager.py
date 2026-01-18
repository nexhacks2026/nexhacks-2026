"""Queue management system for ticket processing."""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from threading import Lock

from app.models import QueueType, Ticket


@dataclass
class QueueEntry:
    """Represents an entry in a queue with metadata."""

    ticket_id: str
    enqueued_at: datetime
    priority_score: int = 0  # Higher = more urgent


@dataclass
class QueueStats:
    """Statistics for a queue."""

    queue_type: QueueType
    count: int
    avg_wait_time_seconds: float
    oldest_ticket_age_seconds: float
    newest_ticket_age_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue": self.queue_type.value,
            "count": self.count,
            "avg_wait_time_seconds": round(self.avg_wait_time_seconds, 2),
            "oldest_ticket_age_seconds": round(self.oldest_ticket_age_seconds, 2),
            "newest_ticket_age_seconds": round(self.newest_ticket_age_seconds, 2),
        }


@dataclass
class AuditLogEntry:
    """Audit log entry for queue transitions."""

    timestamp: datetime
    ticket_id: str
    from_queue: Optional[QueueType]
    to_queue: QueueType
    reason: str
    actor: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "ticket_id": self.ticket_id,
            "from_queue": self.from_queue.value if self.from_queue else None,
            "to_queue": self.to_queue.value,
            "reason": self.reason,
            "actor": self.actor,
        }


class QueueManager:
    """Manages the five ticket queues with atomic operations."""

    def __init__(self):
        self._queues: dict[QueueType, deque[QueueEntry]] = {
            queue_type: deque() for queue_type in QueueType
        }
        self._ticket_queue_map: dict[str, QueueType] = {}
        self._audit_log: list[AuditLogEntry] = []
        self._lock = Lock()

    def enqueue(
        self,
        ticket: Ticket,
        queue: QueueType,
        reason: str = "enqueued",
        actor: Optional[str] = None,
    ) -> int:
        """
        Add ticket to queue with timestamp.
        Returns the position in the queue (1-indexed).
        """
        with self._lock:
            entry = QueueEntry(
                ticket_id=ticket.id,
                enqueued_at=datetime.now(timezone.utc),
                priority_score=self._calculate_priority_score(ticket),
            )

            # Add to queue
            self._queues[queue].append(entry)
            self._ticket_queue_map[ticket.id] = queue

            # Log the transition
            self._audit_log.append(
                AuditLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    ticket_id=ticket.id,
                    from_queue=None,
                    to_queue=queue,
                    reason=reason,
                    actor=actor,
                )
            )

            # Trigger AI Triage if enqueued to INBOX
            if queue == QueueType.INBOX:

                try:
                    import asyncio
                    from app.services.ai_client import ai_client

                    async def run_triage_task():
                        # Simple background task wrapper
                        result = await ai_client.analyze_triage(ticket)
                        if result:
                            self._apply_triage_result(ticket, result)

                    # Get or create event loop to run background task
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    loop.create_task(run_triage_task())
                except Exception as e:
                    print(f"Failed to trigger AI triage: {e}")

            return len(self._queues[queue])

    def _apply_triage_result(self, ticket: Ticket, result: dict) -> None:
        """
        Apply AI triage results to ticket and move to appropriate queue.
        This runs in the background, so we must be careful with state.
        """
        from app.models import TicketStatus

        # Update ticket fields
        ticket.log_reasoning(result)

        # Update Priority
        if result.get("priority"):
            from app.models import TicketPriority

            try:
                ticket.update_priority(TicketPriority(result["priority"]))
            except ValueError:
                pass

        # Update Category
        if result.get("category"):
            from app.models import TicketCategory

            try:
                ticket.set_category(TicketCategory(result["category"]))
            except ValueError:
                pass

        # Set suggested assignee if provided
        suggested_assignee = result.get("suggested_assignee")
        if suggested_assignee:
            ticket.set_suggested_assignee(suggested_assignee)

        # Add AI-suggested tags (merge with existing)
        ai_tags = result.get("tags", [])
        for tag in ai_tags:
            ticket.add_tag(tag)

        # Determine queue move based on confidence
        conf = result.get("confidence", 0)

        # >= 0.8: High confidence -> Auto-assign (move to ASSIGNMENT)
        if conf >= 0.8:
            # Actually assign the ticket if AI suggested an assignee
            if suggested_assignee:
                ticket.assign(suggested_assignee)
            else:
                # No assignee suggestion, just update status
                ticket.update_status(TicketStatus.ASSIGNED)
            self.move_ticket(
                ticket.id,
                QueueType.INBOX,
                QueueType.ASSIGNMENT,
                ticket,
                reason=f"AI Auto-Triage (Confidence: {conf})",
            )
        else:
            # < 0.8: Low confidence -> Manual Triage (move to TRIAGE)
            self.move_ticket(
                ticket.id,
                QueueType.INBOX,
                QueueType.TRIAGE,
                ticket,
                reason=f"AI Triage Needed (Confidence: {conf})",
            )

    def dequeue(self, queue: QueueType, priority_based: bool = True) -> Optional[str]:
        """
        Get next ticket ID from queue.
        If priority_based is True, returns highest priority ticket.
        Otherwise, returns FILO.
        """
        with self._lock:
            if not self._queues[queue]:
                return None

            if priority_based and len(self._queues[queue]) > 1:
                # Find highest priority entry
                entries = list(self._queues[queue])
                entries.sort(key=lambda e: e.priority_score, reverse=True)
                entry = entries[0]
                self._queues[queue].remove(entry)
            else:
                entry = self._queues[
                    queue
                ].pop()  # FILO is pop(), FIFO would be popleft()

            del self._ticket_queue_map[entry.ticket_id]
            return entry.ticket_id

    def move_ticket(
        self,
        ticket_id: str,
        from_queue: QueueType,
        to_queue: QueueType,
        ticket: Ticket,
        reason: str = "moved",
        actor: Optional[str] = None,
    ) -> bool:
        """
        Atomically move ticket between queues with audit logging.
        Returns True if successful, False if ticket not found in source queue.
        """
        with self._lock:
            # Find and remove from source queue
            source_queue = self._queues[from_queue]
            entry_to_move = None

            for entry in source_queue:
                if entry.ticket_id == ticket_id:
                    entry_to_move = entry
                    break

            if not entry_to_move:
                return False

            source_queue.remove(entry_to_move)

            # Add to destination queue with updated timestamp
            new_entry = QueueEntry(
                ticket_id=ticket_id,
                enqueued_at=datetime.now(timezone.utc),
                priority_score=self._calculate_priority_score(ticket),
            )
            self._queues[to_queue].append(new_entry)
            self._ticket_queue_map[ticket_id] = to_queue

            # Log the transition
            self._audit_log.append(
                AuditLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    ticket_id=ticket_id,
                    from_queue=from_queue,
                    to_queue=to_queue,
                    reason=reason,
                    actor=actor,
                )
            )

            return True

    def remove_from_queue(self, ticket_id: str, queue: QueueType) -> bool:
        """Remove a ticket from a queue without moving it elsewhere."""
        with self._lock:
            queue_deque = self._queues[queue]
            for entry in queue_deque:
                if entry.ticket_id == ticket_id:
                    queue_deque.remove(entry)
                    if ticket_id in self._ticket_queue_map:
                        del self._ticket_queue_map[ticket_id]
                    return True
            return False

    def get_queue_stats(self, queue: QueueType) -> QueueStats:
        """Return count, avg wait time, age of oldest/newest ticket."""
        with self._lock:
            entries = list(self._queues[queue])
            now = datetime.now(timezone.utc)

            if not entries:
                return QueueStats(
                    queue_type=queue,
                    count=0,
                    avg_wait_time_seconds=0.0,
                    oldest_ticket_age_seconds=0.0,
                    newest_ticket_age_seconds=0.0,
                )

            wait_times = [(now - e.enqueued_at).total_seconds() for e in entries]

            return QueueStats(
                queue_type=queue,
                count=len(entries),
                avg_wait_time_seconds=sum(wait_times) / len(wait_times),
                oldest_ticket_age_seconds=max(wait_times),
                newest_ticket_age_seconds=min(wait_times),
            )

    def get_all_queue_stats(self) -> list[QueueStats]:
        """Get stats for all queues."""
        return [self.get_queue_stats(queue) for queue in QueueType]

    def peek_queue(
        self,
        queue: QueueType,
        limit: int = 10,
        priority_based: bool = True,
    ) -> list[str]:
        """View next N ticket IDs without removing them."""
        with self._lock:
            entries = list(self._queues[queue])

            if priority_based:
                entries.sort(key=lambda e: e.priority_score, reverse=True)

            return [e.ticket_id for e in entries[:limit]]

    def get_queue_position(self, ticket_id: str) -> Optional[tuple[QueueType, int]]:
        """Get the queue and position of a ticket."""
        with self._lock:
            queue = self._ticket_queue_map.get(ticket_id)
            if not queue:
                return None

            entries = list(self._queues[queue])
            for i, entry in enumerate(entries):
                if entry.ticket_id == ticket_id:
                    return (queue, i + 1)

            return None

    def get_ticket_queue(self, ticket_id: str) -> Optional[QueueType]:
        """Get which queue a ticket is in."""
        return self._ticket_queue_map.get(ticket_id)

    def estimate_wait_time(self, queue: QueueType, position: int) -> float:
        """
        Estimate wait time in seconds based on queue and position.
        Uses average processing time per queue.
        """
        # Average processing times per queue (in seconds)
        avg_processing_times = {
            QueueType.INBOX: 5,  # Quick ingestion
            QueueType.TRIAGE: 30,  # AI processing
            QueueType.ASSIGNMENT: 60,  # Human review
            QueueType.ACTIVE: 300,  # Active work
            QueueType.RESOLUTION: 60,  # Closure verification
        }

        return position * avg_processing_times.get(queue, 60)

    def get_audit_log(
        self,
        ticket_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get audit log entries, optionally filtered by ticket."""
        with self._lock:
            entries = self._audit_log

            if ticket_id:
                entries = [e for e in entries if e.ticket_id == ticket_id]

            return entries[-limit:]

    def _calculate_priority_score(self, ticket: Ticket) -> int:
        """Calculate priority score for queue ordering."""
        from app.models import TicketPriority

        priority_scores = {
            TicketPriority.LOW: 1,
            TicketPriority.MEDIUM: 2,
            TicketPriority.HIGH: 3,
            TicketPriority.CRITICAL: 4,
        }

        base_score = priority_scores.get(ticket.priority, 2) * 100

        # Add age bonus (older tickets get higher priority)
        age_seconds = (datetime.now(timezone.utc) - ticket.created_at).total_seconds()
        age_bonus = min(int(age_seconds / 60), 50)  # Cap at 50 points

        return base_score + age_bonus


# Global queue manager instance
queue_manager = QueueManager()
