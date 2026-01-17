"""Routes package for ticket management API."""

from .tickets import router as tickets_router
from .queues import router as queues_router
from .distribution import router as distribution_router

__all__ = [
    "tickets_router",
    "queues_router",
    "distribution_router",
]
