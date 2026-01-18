import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.models import TicketStatus, QueueType
from app.storage import ticket_repository
from app.events import event_publisher

logger = logging.getLogger(__name__)


async def run_auto_close_task():
    """
    Background task to automatically close tickets that have been
    in RESOLVED state for more than 5 minutes.
    """
    logger.info("Starting auto-close background task")
    
    while True:
        try:
            # Check every minute
            await asyncio.sleep(60)
            
            logger.debug("Running auto-close check")
            
            # Get all resolved tickets
            resolved_tickets = ticket_repository.find(status=TicketStatus.RESOLVED)
            
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(minutes=5)
            
            for ticket in resolved_tickets:
                # Check if ticket was updated more than 5 minutes ago
                # We assume updated_at was updated when it moved to RESOLVED
                if ticket.updated_at < cutoff_time:
                    logger.info(f"Auto-closing ticket {ticket.id} (Resolved at {ticket.updated_at})")
                    
                    try:
                        old_queue = ticket.current_queue
                        
                        # Close the ticket
                        ticket.close()
                        ticket_repository.save(ticket)
                        
                        # Notify system
                        await event_publisher.publish_ticket_updated(
                            ticket, 
                            {"status": TicketStatus.CLOSED.value}
                        )
                        
                        # Also publish moved event so frontend updates queues if needed
                        # (Ticket stays in same queue conceptually or moves to archive, 
                        # but for now we just change status)
                        
                        logger.info(f"Successfully closed ticket {ticket.id}")
                        
                    except Exception as e:
                        logger.error(f"Error closing ticket {ticket.id}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error in auto-close task: {str(e)}")
            # prevent tight loop on error
            await asyncio.sleep(5)
