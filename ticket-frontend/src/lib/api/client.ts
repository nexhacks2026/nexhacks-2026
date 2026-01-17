/**
 * API Client for the Ticket Management Backend
 */

const API_BASE_URL = '';

// Types matching backend models
export interface BackendTicket {
  id: string;
  created_at: string;
  updated_at: string;
  source: 'EMAIL' | 'DISCORD' | 'GITHUB' | 'FORM' | 'WEBHOOK';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  category: 'BILLING' | 'TECHNICAL_SUPPORT' | 'FEATURE_REQUEST' | 'BUG_REPORT' | 'ADMIN' | 'OTHER' | null;
  status: 'INBOX' | 'TRIAGE_PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
  current_queue: 'INBOX' | 'TRIAGE' | 'ASSIGNMENT' | 'ACTIVE' | 'RESOLUTION';
  title?: string;
  description?: string;
  content: {
    type: string;
    sender_email?: string;
    subject?: string;
    body?: string;
    message_text?: string;
    issue_title?: string;
    issue_body?: string;
    [key: string]: unknown;
  };
  assignee: string | null;
  tags: string[];
  ai_reasoning: {
    summary?: string;
    confidence?: number;
    category?: string;
    priority?: string;
    [key: string]: unknown;
  };
  resolution_action: string;
  suggested_assignee: string | null;
  queue_position?: number;
}

export interface QueueStats {
  queue: string;
  count: number;
  avg_wait_time_seconds: number;
  oldest_ticket_age_seconds: number;
  newest_ticket_age_seconds: number;
}

export interface ClaimResponse {
  success: boolean;
  ticket_id: string | null;
  ticket: BackendTicket | null;
  message: string;
}

export interface DistributionResponse {
  success: boolean;
  ticket_id: string;
  agent_id: string;
  status: string;
  queue: string;
  message: string;
}

// API Functions

export async function fetchTickets(filters?: {
  status?: string;
  queue?: string;
  priority?: string;
  assignee?: string;
  limit?: number;
  offset?: number;
}): Promise<BackendTicket[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.queue) params.set('queue', filters.queue);
  if (filters?.priority) params.set('priority', filters.priority);
  if (filters?.assignee) params.set('assignee', filters.assignee);
  if (filters?.limit) params.set('limit', String(filters.limit));
  if (filters?.offset) params.set('offset', String(filters.offset));

  const url = `${API_BASE_URL}/api/tickets${params.toString() ? '?' + params.toString() : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch tickets: ${response.statusText}`);
  }

  const data = await response.json();
  return data.tickets;
}

export async function fetchTicket(ticketId: string): Promise<BackendTicket> {
  const response = await fetch(`${API_BASE_URL}/api/tickets/${ticketId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch ticket: ${response.statusText}`);
  }

  const data = await response.json();
  return data.ticket;
}

export async function updateTicket(ticketId: string, updates: {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  category?: string;
  tags?: string[];
  assignee?: string;
}): Promise<BackendTicket> {
  const response = await fetch(`${API_BASE_URL}/api/tickets/${ticketId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update ticket: ${response.statusText}`);
  }

  const data = await response.json();
  return data.ticket;
}

export async function fetchQueues(): Promise<{ queues: QueueStats[]; total_tickets: number }> {
  const response = await fetch(`${API_BASE_URL}/api/queues`);

  if (!response.ok) {
    throw new Error(`Failed to fetch queues: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchQueueDetails(queueName: string, limit = 20): Promise<{
  queue: string;
  stats: QueueStats;
  tickets: BackendTicket[];
}> {
  const response = await fetch(`${API_BASE_URL}/api/queues/${queueName}?limit=${limit}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch queue details: ${response.statusText}`);
  }

  return response.json();
}

export async function moveTicket(
  ticketId: string,
  fromQueue: string,
  toQueue: string,
  reason?: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/queues/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ticket_id: ticketId,
      from_queue: fromQueue,
      to_queue: toQueue,
      reason,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to move ticket: ${response.statusText}`);
  }
}

// Distribution API

export async function claimTicket(agentId: string, options?: {
  preferred_categories?: string[];
  max_priority?: string;
}): Promise<ClaimResponse> {
  const response = await fetch(`${API_BASE_URL}/api/distribution/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_id: agentId,
      ...options,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to claim ticket: ${response.statusText}`);
  }

  return response.json();
}

export async function assignTicket(
  ticketId: string,
  agentId: string,
  reason?: string
): Promise<DistributionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/distribution/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ticket_id: ticketId,
      agent_id: agentId,
      reason,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to assign ticket: ${response.statusText}`);
  }

  return response.json();
}

export async function releaseTicket(
  ticketId: string,
  agentId: string,
  reason?: string
): Promise<DistributionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/distribution/release`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ticket_id: ticketId,
      agent_id: agentId,
      reason,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to release ticket: ${response.statusText}`);
  }

  return response.json();
}

export async function transferTicket(
  ticketId: string,
  fromAgentId: string,
  toAgentId: string,
  reason?: string
): Promise<DistributionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/distribution/transfer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ticket_id: ticketId,
      from_agent_id: fromAgentId,
      to_agent_id: toAgentId,
      reason,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to transfer ticket: ${response.statusText}`);
  }

  return response.json();
}

export async function getAvailableTickets(options?: {
  limit?: number;
  category?: string;
  priority?: string;
}): Promise<{ tickets: BackendTicket[]; count: number }> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.category) params.set('category', options.category);
  if (options?.priority) params.set('priority', options.priority);

  const url = `${API_BASE_URL}/api/distribution/available${params.toString() ? '?' + params.toString() : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to get available tickets: ${response.statusText}`);
  }

  return response.json();
}

export async function getMyTickets(agentId: string): Promise<{
  agent_id: string;
  tickets: BackendTicket[];
  count: number;
}> {
  const response = await fetch(`${API_BASE_URL}/api/distribution/my-tickets?agent_id=${agentId}`);

  if (!response.ok) {
    throw new Error(`Failed to get agent tickets: ${response.statusText}`);
  }

  return response.json();
}

export async function getAgentStats(agentId: string): Promise<{
  agent_id: string;
  stats: {
    total: number;
    by_priority: Record<string, number>;
    by_category: Record<string, number>;
    by_status: Record<string, number>;
  };
}> {
  const response = await fetch(`${API_BASE_URL}/api/distribution/agent-stats/${agentId}`);

  if (!response.ok) {
    throw new Error(`Failed to get agent stats: ${response.statusText}`);
  }

  return response.json();
}

export async function createTicket(ticketData: {
  source: 'EMAIL' | 'DISCORD' | 'GITHUB' | 'FORM' | 'WEBHOOK';
  content_type: string;
  payload: Record<string, any>;
  metadata?: Record<string, any>;
}): Promise<{
  ticket_id: string;
  status: string;
  queue: string;
  position_in_queue: number;
  estimated_time_to_triage: string;
  created_at: string;
}> {
  
  const response = await fetch(`${API_BASE_URL}/api/tickets/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticketData),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Create ticket failed:', response.status, errorText);
    throw new Error(`Failed to create ticket: ${response.statusText}`);
  }

  const result = await response.json();
  return result;
}

export async function deleteTicket(ticketId: string): Promise<{
  success: boolean;
  ticket_id: string;
  message: string;
}> {
  const response = await fetch(`${API_BASE_URL}/api/tickets/${ticketId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete ticket: ${response.statusText}`);
  }

  return response.json();
}
