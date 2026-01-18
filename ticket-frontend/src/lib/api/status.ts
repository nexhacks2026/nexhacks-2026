import { writable } from 'svelte/store';

export type ServiceStatus = 'connected' | 'connecting' | 'error' | 'disconnected' | 'unknown';

export interface SystemStatus {
    database: ServiceStatus;
    ai: ServiceStatus;
    n8n: ServiceStatus;
}

const POLL_INTERVAL = 30000; // 30 seconds

function createStatusStore() {
    const { subscribe, set, update } = writable<SystemStatus>({
        database: 'connecting',
        ai: 'connecting',
        n8n: 'unknown'
    });

    let pollInterval: ReturnType<typeof setInterval>;

    async function checkServiceHealth() {
        // Check Ticket Backend (Database)
        try {
            const dbRes = await fetch('/api/health'); // Proxied to ticket-backend/health
            if (dbRes.ok) {
                update((s: SystemStatus) => ({ ...s, database: 'connected' }));
            } else {
                update((s: SystemStatus) => ({ ...s, database: 'error' }));
            }
        } catch (e) {
            update((s: SystemStatus) => ({ ...s, database: 'disconnected' }));
        }

        // Check AI Backend
        try {
            const aiRes = await fetch('/ai/health'); // Proxied to ai-service/health
            if (aiRes.ok) {
                update((s: SystemStatus) => ({ ...s, ai: 'connected' }));
            } else {
                update((s: SystemStatus) => ({ ...s, ai: 'error' }));
            }
        } catch (e) {
            update((s: SystemStatus) => ({ ...s, ai: 'disconnected' }));
        }

        // n8n status is currently unknown as we don't have a direct health endpoint exposed similarly
        // We can leave it as 'unknown' or set it to match one of the others if desired, 
        // but for now 'unknown' is the most honest state.
        // If we want to simulate it being alive when others are, we could:
        // update(s => ({ ...s, n8n: 'connected' })); 
        // But per instructions, we want "actual" connection. 
        // Since we can't check it easily yet without an endpoint, we'll leave it as unknown or assume connected if we want to be optimistic.
        // Let's default to 'unknown' to indicate it's not actually being checked yet.
    }

    function startPolling() {
        checkServiceHealth(); // Check immediately
        pollInterval = setInterval(checkServiceHealth, POLL_INTERVAL);
    }

    function stopPolling() {
        if (pollInterval) clearInterval(pollInterval);
    }

    return {
        subscribe,
        startPolling,
        stopPolling,
        checkNow: checkServiceHealth
    };
}

export const serviceStatus = createStatusStore();
