import { writable, derived, get, type Writable, type Readable } from "svelte/store"
import {
  fetchTickets,
  updateTicket as apiUpdateTicket,
  assignTicket,
  releaseTicket,
  type BackendTicket
} from "../api/client"
import { websocket, type TicketEvent } from "../api/websocket"

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

// Frontend status maps to backend queue-based workflow
export type TicketStatus = "open" | "in_progress" | "review" | "done"
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

// Map backend queue/status to frontend status
function mapBackendStatusToFrontend(backendTicket: BackendTicket): TicketStatus {
  const queue = backendTicket.current_queue
  const status = backendTicket.status

  // Map based on queue primarily
  switch (queue) {
    case 'INBOX':
    case 'TRIAGE':
    case 'ASSIGNMENT':
      return 'open'
    case 'ACTIVE':
      return 'in_progress'
    case 'RESOLUTION':
      return status === 'CLOSED' ? 'done' : 'review'
    default:
      return 'open'
  }
}

// Map frontend status to backend queue
export function mapFrontendStatusToBackend(status: TicketStatus): { queue: string; backendStatus: string } {
  switch (status) {
    case 'open':
      return { queue: 'ASSIGNMENT', backendStatus: 'ASSIGNED' }
    case 'in_progress':
      return { queue: 'ACTIVE', backendStatus: 'IN_PROGRESS' }
    case 'review':
      return { queue: 'RESOLUTION', backendStatus: 'RESOLVED' }
    case 'done':
      return { queue: 'RESOLUTION', backendStatus: 'CLOSED' }
    default:
      return { queue: 'ASSIGNMENT', backendStatus: 'ASSIGNED' }
  }
}

// Map backend priority to frontend (lowercase)
function mapBackendPriority(priority: string): TicketPriority {
  return priority.toLowerCase() as TicketPriority
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

  // Extract title from content
  let title = 'Untitled Ticket'
  if (content.subject) {
    title = content.subject
  } else if (content.issue_title) {
    title = content.issue_title
  } else if (content.message_text) {
    title = content.message_text.slice(0, 100)
  }

  // Extract description from content
  let description = ''
  if (content.body) {
    description = content.body
  } else if (content.issue_body) {
    description = content.issue_body
  } else if (content.message_text) {
    description = content.message_text
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
export const tickets: Readable<Ticket[]> = { subscribe: ticketsWritable.subscribe }
export const loading: Readable<boolean> = { subscribe: loadingWritable.subscribe }
export const error: Readable<string | null> = { subscribe: errorWritable.subscribe }
export const currentAgent: Writable<string | null> = currentAgentWritable

// Derived stores
export const ticketsByStatus: Readable<Record<TicketStatus, Ticket[]>> = derived(ticketsWritable, ($tickets: Ticket[]) => {
  return {
    open: $tickets.filter((t: Ticket) => t.status === 'open'),
    in_progress: $tickets.filter((t: Ticket) => t.status === 'in_progress'),
    review: $tickets.filter((t: Ticket) => t.status === 'review'),
    done: $tickets.filter((t: Ticket) => t.status === 'done'),
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

export async function updateTicketStatus(ticketId: string, newStatus: TicketStatus): Promise<void> {
  const currentTickets = get(ticketsWritable)
  const ticket = currentTickets.find((t: Ticket) => t.id === ticketId)

  if (!ticket) return

  // Optimistically update local state
  ticketsWritable.update((items: Ticket[]) =>
    items.map((t: Ticket) =>
      t.id === ticketId
        ? { ...t, status: newStatus, updatedAt: new Date().toISOString() }
        : t
    )
  )

  // Note: Full status changes require queue moves which need backend coordination
  // For now, we just update locally - the backend sync will happen via WebSocket
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

    // Update local state
    ticketsWritable.update((items: Ticket[]) =>
      items.map((t: Ticket) => {
        if (t.id === ticketId) {
          return {
            ...t,
            assignee: {
              name: agentId,
              avatar: agentId.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2),
              color: stringToColor(agentId),
            },
            status: 'in_progress' as TicketStatus,
            updatedAt: new Date().toISOString(),
          }
        }
        return t
      })
    )
  } catch (e) {
    console.error('Failed to assign ticket:', e)
  }
}

export async function releaseTicketFromAgent(ticketId: string, agentId: string): Promise<void> {
  try {
    await releaseTicket(ticketId, agentId)

    ticketsWritable.update((items: Ticket[]) =>
      items.map((t: Ticket) =>
        t.id === ticketId
          ? { ...t, assignee: null, status: 'open' as TicketStatus, updatedAt: new Date().toISOString() }
          : t
      )
    )
  } catch (e) {
    console.error('Failed to release ticket:', e)
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
      // Reload tickets to get the new one
      loadTickets()
      break

    case 'ticket.updated':
      if (event.data.ticket_id) {
        // Reload the specific ticket or all tickets
        loadTickets()
      }
      break

    case 'ticket.moved':
      if (event.data.ticket_id) {
        loadTickets()
      }
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
