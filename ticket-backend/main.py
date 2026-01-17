"""Ticket Management System - FastAPI Backend.

Run with: uvicorn main:app --reload
"""

import json
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app import create_app
from app.routes import tickets_router, queues_router, distribution_router
from app.websockets import connection_manager

# Create the application
app = create_app()


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with: ws://localhost:8000/ws?client_id=your-client-id
    
    Send messages to subscribe/unsubscribe from channels:
    - {"action": "subscribe", "channel": "queue.TRIAGE"}
    - {"action": "unsubscribe", "channel": "queue.TRIAGE"}
    
    Available channels:
    - "all" - All events (auto-subscribed)
    - "tickets.all" - All ticket events
    - "ticket.{ticket_id}" - Events for a specific ticket
    - "queue.{queue_name}" - Events for a specific queue (INBOX, TRIAGE, ASSIGNMENT, ACTIVE, RESOLUTION)
    - "agent.{agent_id}" - Events for assignments to a specific agent
    """
    if not client_id:
        client_id = f"client-{id(websocket)}"

    await connection_manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")
                channel = message.get("channel")

                if action == "subscribe" and channel:
                    await connection_manager.subscribe(client_id, channel)
                elif action == "unsubscribe" and channel:
                    await connection_manager.unsubscribe(client_id, channel)
                elif action == "ping":
                    await connection_manager.send_personal_message(
                        client_id,
                        {"event": "pong", "timestamp": "now"}
                    )
                else:
                    await connection_manager.send_personal_message(
                        client_id,
                        {"event": "error", "message": f"Unknown action: {action}"}
                    )

            except json.JSONDecodeError:
                await connection_manager.send_personal_message(
                    client_id,
                    {"event": "error", "message": "Invalid JSON"}
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ticket-management-system"}


# WebSocket stats endpoint
@app.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return connection_manager.get_stats()


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Ticket Management System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws?client_id=your-id",
        "endpoints": {
            "tickets": "/api/tickets",
            "queues": "/api/queues",
            "distribution": "/api/distribution",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
