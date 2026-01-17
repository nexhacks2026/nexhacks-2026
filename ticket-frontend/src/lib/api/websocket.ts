/**
 * WebSocket client for real-time ticket updates
 */

import { writable, type Writable } from 'svelte/store';

const WS_URL = 'ws://localhost:8000/ws';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface TicketEvent {
    event: string;
    data: {
        ticket_id?: string;
        queue?: string;
        status?: string;
        priority?: string;
        from_queue?: string;
        to_queue?: string;
        assignee?: string;
        changes?: Record<string, unknown>;
        [key: string]: unknown;
    };
    timestamp: string;
}

export interface WebSocketStore {
    status: Writable<WebSocketStatus>;
    lastEvent: Writable<TicketEvent | null>;
    connect: (clientId: string) => void;
    disconnect: () => void;
    subscribe: (channel: string) => void;
    unsubscribe: (channel: string) => void;
    onEvent: (callback: (event: TicketEvent) => void) => () => void;
}

function createWebSocketStore(): WebSocketStore {
    let ws: WebSocket | null = null;
    let clientId: string | null = null;
    const eventCallbacks: Set<(event: TicketEvent) => void> = new Set();

    const status = writable<WebSocketStatus>('disconnected');
    const lastEvent = writable<TicketEvent | null>(null);

    function connect(id: string): void {
        if (ws && ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        clientId = id;
        status.set('connecting');

        try {
            ws = new WebSocket(`${WS_URL}?client_id=${clientId}`);

            ws.onopen = () => {
                console.log('WebSocket connected');
                status.set('connected');

                // Auto-subscribe to common channels
                subscribe('tickets.all');
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data) as TicketEvent;
                    lastEvent.set(data);

                    // Notify all callbacks
                    eventCallbacks.forEach(cb => cb(data));
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                status.set('error');
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                status.set('disconnected');
                ws = null;

                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    if (clientId) {
                        connect(clientId);
                    }
                }, 5000);
            };
        } catch (e) {
            console.error('Failed to create WebSocket:', e);
            status.set('error');
        }
    }

    function disconnect(): void {
        if (ws) {
            ws.close();
            ws = null;
        }
        clientId = null;
        status.set('disconnected');
    }

    function subscribe(channel: string): void {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'subscribe', channel }));
        }
    }

    function unsubscribe(channel: string): void {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'unsubscribe', channel }));
        }
    }

    function onEvent(callback: (event: TicketEvent) => void): () => void {
        eventCallbacks.add(callback);
        return () => {
            eventCallbacks.delete(callback);
        };
    }

    return {
        status,
        lastEvent,
        connect,
        disconnect,
        subscribe,
        unsubscribe,
        onEvent,
    };
}

// Export singleton instance
export const websocket = createWebSocketStore();
