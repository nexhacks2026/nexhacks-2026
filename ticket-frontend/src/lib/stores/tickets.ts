import { writable, derived, get, type Writable, type Readable } from "svelte/store"
import {
  fetchTickets,
  updateTicket as apiUpdateTicket,
  assignTicket,
  releaseTicket,
  createTicket as apiCreateTicket,
  deleteTicket as apiDeleteTicket,
  type BackendTicket
} from "../api/client"
import { websocket, type TicketEvent } from "../api/websocket"
import { currentUser } from "./users"

export interface Assignee {
  name: string
  avatar: string
  color: string
}

export interface ReasoningStep {
  type: "analysis" | "hypothesis" | "recommendation" | "context"
  title: string
  content: string
  timestamp: string
}

export interface AIReasoning {
  summary: string
  confidence: number
  steps: ReasoningStep[]
}

// Backend status types matching the backend enums
export type BackendTicketStatus = "INBOX" | "TRIAGE_PENDING" | "ASSIGNED" | "IN_PROGRESS" | "RESOLVED"

// Frontend status maps to backend status
export type TicketStatus = "inbox" | "triage_pending" | "assigned" | "in_progress" | "resolved"
export type TicketPriority = "low" | "medium" | "high" | "critical"

export interface Ticket {
  id: string
  title: string
  description: string
  status: TicketStatus
  priority: TicketPriority
  assignee: Assignee | null
  createdAt: string
  updatedAt: string
  aiReasoning: AIReasoning
  labels: string[]
  // Backend-specific fields
  source?: string
  category?: string
  currentQueue?: string
  suggestedAssignee?: string
}

// Map backend status to frontend status (lowercase)
function mapBackendStatusToFrontend(backendTicket: BackendTicket): TicketStatus {
  return backendTicket.status.toLowerCase() as TicketStatus
}

// Map frontend status to backend status (uppercase)
export function mapFrontendStatusToBackend(status: TicketStatus): BackendTicketStatus {
  return status.toUpperCase() as BackendTicketStatus
}

// Get display label for status
export function getStatusLabel(status: TicketStatus): string {
  switch (status) {
    case 'inbox':
      return 'Inbox'
    case 'triage_pending':
      return 'Triage Pending'
    case 'assigned':
      return 'Assigned'
    case 'in_progress':
      return 'In Progress'
    case 'resolved':
      return 'Resolved'
    default:
      return status
  }
}

// Get color class for status
export function getStatusColor(status: TicketStatus): string {
  switch (status) {
    case 'inbox':
      return 'bg-muted text-muted-foreground'
    case 'triage_pending':
      return 'bg-yellow-500/10 text-yellow-500'
    case 'assigned':
      return 'bg-blue-500/10 text-blue-500'
    case 'in_progress':
      return 'bg-purple-500/10 text-purple-500'
    case 'resolved':
      return 'bg-green-500/10 text-green-500'
    default:
      return 'bg-muted text-muted-foreground'
  }
}

// Map backend priority to frontend (lowercase)
function mapBackendPriority(priority: string): TicketPriority {
  return priority.toLowerCase() as TicketPriority
}

// Create new ticket
export async function addTicket(
  title: string,
  description: string,
  priority: TicketPriority = 'medium',
  category?: string,
  tags?: string[]
): Promise<string> {
  console.log("desc:", description);
  try {
    const metadata: any = {
      priority: priority.toUpperCase(),
      tags: tags || [],
    };
    
    // Add category if provided
    if (category) {
      metadata.category = category.toUpperCase();
    }
    
    const requestPayload = {
      source: 'FORM',
      content_type: 'form',
      payload: {
        fields: {
          title,
          description,
        },
        submission_time: new Date().toISOString(),
      },
      metadata,
    };
    
    console.log('Sending ticket creation request:', requestPayload);
    
    const response = await apiCreateTicket(requestPayload);
    
    console.log('Ticket creation response:', response);
    
    // Refresh tickets after creation
    console.log('Reloading tickets...');
    await loadTickets();
    console.log('Tickets reloaded successfully');
    
    return response.ticket_id;
  } catch (error) {
    console.error('Failed to create ticket:', error);
    throw error;
  }
}

// Generate a color from a string (for assignee avatars)
function stringToColor(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ec4899', '#06b6d4']
  return colors[Math.abs(hash) % colors.length]
}

// Convert backend ticket to frontend format
function transformBackendTicket(backendTicket: BackendTicket): Ticket {
  const content = backendTicket.content

  // Use the title field from backend if available, otherwise extract from content
  let title = backendTicket.title || 'Untitled Ticket'
  if (!backendTicket.title) {
    if (content.subject) {
      title = content.subject
    } else if (content.issue_title) {
      title = content.issue_title
    } else if (content.message_text) {
      title = content.message_text.slice(0, 100)
    }
  }

  // Extract description from content
  let description = backendTicket.description || ""
  if (!description) {
    if (content.body) {
      description = content.body
    } else if (content.issue_body) {
      description = content.issue_body
    } else if (content.message_text) {
      description = content.message_text
    } else if ('form_fields' in content && typeof content.form_fields === 'object' && content.form_fields !== null) {
      const formFields = content.form_fields as Record<string, any>
      if ('description' in formFields && typeof formFields.description === 'string') {
        description = formFields.description
      }
    }
  }

  // Build assignee object if present
  let assignee: Assignee | null = null
  if (backendTicket.assignee) {
    const name = backendTicket.assignee
    assignee = {
      name,
      avatar: name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2),
      color: stringToColor(name),
    }
  }

  // Build AI reasoning from backend data
  const aiReasoning: AIReasoning = {
    summary: backendTicket.ai_reasoning?.summary || `Ticket from ${backendTicket.source}`,
    confidence: backendTicket.ai_reasoning?.confidence || 0.5,
    steps: [],
  }

  // Add reasoning steps if available
  if (backendTicket.ai_reasoning) {
    if (backendTicket.category) {
      aiReasoning.steps.push({
        type: 'analysis',
        title: 'Category Classification',
        content: `Classified as ${backendTicket.category}`,
        timestamp: new Date(backendTicket.updated_at).toLocaleTimeString(),
      })
    }
    if (backendTicket.ai_reasoning.priority) {
      aiReasoning.steps.push({
        type: 'recommendation',
        title: 'Priority Assessment',
        content: `Set priority to ${backendTicket.priority}`,
        timestamp: new Date(backendTicket.updated_at).toLocaleTimeString(),
      })
    }
    if (backendTicket.suggested_assignee) {
      aiReasoning.steps.push({
        type: 'recommendation',
        title: 'Suggested Assignee',
        content: `Recommend assigning to ${backendTicket.suggested_assignee}`,
        timestamp: new Date(backendTicket.updated_at).toLocaleTimeString(),
      })
    }
  }

  return {
    id: backendTicket.id,
    title,
    description,
    status: mapBackendStatusToFrontend(backendTicket),
    priority: mapBackendPriority(backendTicket.priority),
    assignee,
    createdAt: backendTicket.created_at,
    updatedAt: backendTicket.updated_at,
    aiReasoning,
    labels: backendTicket.tags,
    source: backendTicket.source,
    category: backendTicket.category || undefined,
    currentQueue: backendTicket.current_queue,
    suggestedAssignee: backendTicket.suggested_assignee || undefined,
  }
}

// Store state
const ticketsWritable: Writable<Ticket[]> = writable<Ticket[]>([])
const loadingWritable: Writable<boolean> = writable<boolean>(false)
const errorWritable: Writable<string | null> = writable<string | null>(null)
const currentAgentWritable: Writable<string | null> = writable<string | null>(null)

// Exported stores
export const allTickets: Readable<Ticket[]> = { subscribe: ticketsWritable.subscribe }
export const loading: Readable<boolean> = { subscribe: loadingWritable.subscribe }
export const error: Readable<string | null> = { subscribe: errorWritable.subscribe }
export const currentAgent: Writable<string | null> = currentAgentWritable

// Filtered tickets based on current user
// Admin (user-0) sees all tickets, other users only see their assigned tickets
export const tickets: Readable<Ticket[]> = derived(
  [ticketsWritable, currentUser],
  ([$tickets, $currentUser]) => {
    // Admin sees all tickets
    if ($currentUser?.id === 'user-0') {
      return $tickets
    }
    
    // Regular users only see tickets assigned to them
    return $tickets.filter(t => t.assignee?.name === $currentUser?.name)
  }
)

// Derived stores
export const ticketsByStatus: Readable<Record<TicketStatus, Ticket[]>> = derived(tickets, ($tickets: Ticket[]) => {
  return {
    inbox: $tickets.filter((t: Ticket) => t.status === 'inbox'),
    triage_pending: $tickets.filter((t: Ticket) => t.status === 'triage_pending'),
    assigned: $tickets.filter((t: Ticket) => t.status === 'assigned'),
    in_progress: $tickets.filter((t: Ticket) => t.status === 'in_progress'),
    resolved: $tickets.filter((t: Ticket) => t.status === 'resolved'),
  }
})

// Actions

export async function loadTickets(): Promise<void> {
  loadingWritable.set(true)
  errorWritable.set(null)

  try {
    const backendTickets = await fetchTickets({ limit: 100 })
    const frontendTickets = backendTickets.map(transformBackendTicket)
    ticketsWritable.set(frontendTickets)
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Failed to load tickets'
    errorWritable.set(message)
    console.error('Failed to load tickets:', e)
  } finally {
    loadingWritable.set(false)
  }
}

export async function updateTicketTitle(ticketId: string, newTitle: string): Promise<void> {
  try {
    await apiUpdateTicket(ticketId, { title: newTitle })
    await loadTickets()
  } catch (error) {
    console.error('Failed to update ticket title:', error)
    throw error
  }
}

export async function updateTicketDescription(ticketId: string, newDescription: string): Promise<void> {
  try {
    await apiUpdateTicket(ticketId, { description: newDescription })
    await loadTickets()
  } catch (error) {
    console.error('Failed to update ticket description:', error)
    throw error
  }
}

export async function updateTicketStatus(ticketId: string, newStatus: TicketStatus): Promise<void> {
  const currentTickets = get(ticketsWritable)
  const ticket = currentTickets.find((t: Ticket) => t.id === ticketId)

  if (!ticket) return

  const oldStatus = ticket.status

  // Optimistically update local state
  ticketsWritable.update((items: Ticket[]) =>
    items.map((t: Ticket) =>
      t.id === ticketId
        ? { ...t, status: newStatus, updatedAt: new Date().toISOString() }
        : t
    )
  )

  try {
    // Sync to backend - convert to uppercase for backend enum format
    await apiUpdateTicket(ticketId, { status: newStatus.toUpperCase() })
  } catch (e) {
    console.error('Failed to update status:', e)
    // Rollback on failure
    ticketsWritable.update((items: Ticket[]) =>
      items.map((t: Ticket) =>
        t.id === ticketId
          ? { ...t, status: oldStatus, updatedAt: new Date().toISOString() }
          : t
      )
    )
  }
}

export async function updateTicketPriority(ticketId: string, newPriority: TicketPriority): Promise<void> {
  try {
    await apiUpdateTicket(ticketId, { priority: newPriority.toUpperCase() })

    ticketsWritable.update((items: Ticket[]) =>
      items.map((t: Ticket) =>
        t.id === ticketId
          ? { ...t, priority: newPriority, updatedAt: new Date().toISOString() }
          : t
      )
    )
  } catch (e) {
    console.error('Failed to update priority:', e)
  }
}

export async function assignTicketToAgent(ticketId: string, agentId: string): Promise<void> {
  try {
    await assignTicket(ticketId, agentId)
    
    // Reload tickets to get the backend's status update
    await loadTickets()
  } catch (e) {
    console.error('Failed to assign ticket:', e)
  }
}

export async function releaseTicketFromAgent(ticketId: string, agentId: string): Promise<void> {
  try {
    await releaseTicket(ticketId, agentId)
    
    // Reload tickets to get the backend's status update
    await loadTickets()
  } catch (e) {
    console.error('Failed to release ticket:', e)
  }
}

export async function deleteTicket(ticketId: string): Promise<void> {
  try {
    await apiDeleteTicket(ticketId)

    // Remove from local state
    ticketsWritable.update((items: Ticket[]) =>
      items.filter((t: Ticket) => t.id !== ticketId)
    )
  } catch (e) {
    console.error('Failed to delete ticket:', e)
    throw e
  }
}

// WebSocket integration
let wsUnsubscribe: (() => void) | null = null

export function connectWebSocket(agentId: string): void {
  currentAgentWritable.set(agentId)
  websocket.connect(agentId)

  // Listen for ticket events
  wsUnsubscribe = websocket.onEvent(handleWebSocketEvent)
}

export function disconnectWebSocket(): void {
  if (wsUnsubscribe) {
    wsUnsubscribe()
    wsUnsubscribe = null
  }
  websocket.disconnect()
  currentAgentWritable.set(null)
}

function handleWebSocketEvent(event: TicketEvent): void {
  console.log('WebSocket event:', event)

  switch (event.event) {
    case 'ticket.created':
    case 'ticket.triage_pending':
    case 'ticket.updated':
    case 'ticket.moved':
      // Reload tickets to reflect changes
      loadTickets()
      break

    case 'ticket.assigned':
      if (event.data.ticket_id && event.data.assignee) {
        ticketsWritable.update((items: Ticket[]) =>
          items.map((t: Ticket) => {
            if (t.id === event.data.ticket_id) {
              const name = event.data.assignee as string
              return {
                ...t,
                assignee: {
                  name,
                  avatar: name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2),
                  color: stringToColor(name),
                },
              }
            }
            return t
          })
        )
      }
      break

    case 'subscribed':
    case 'unsubscribed':
    case 'pong':
      // Ignore these
      break

    default:
      console.log('Unhandled WebSocket event:', event.event)
  }
}

// Initialize - try to load tickets on module load
// But don't block if backend is not available
loadTickets().catch(() => {
  console.log('Backend not available, using empty ticket list')
})
