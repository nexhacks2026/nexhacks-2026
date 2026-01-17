<script lang="ts">
  import TicketCard from './ticket-card.svelte';
  import { tickets, updateTicketStatus, type Ticket, type TicketStatus } from '$lib/stores/tickets';
  
  interface Props {
    onselectTicket?: (event: { id: string }) => void;
    selectedTicketId?: string | null;
  }
  
  let { onselectTicket = () => {}, selectedTicketId = null }: Props = $props();
  
  interface Column {
    id: TicketStatus;
    label: string;
    color: string;
  }
  
  const columns: Column[] = [
    { id: 'inbox', label: 'Inbox', color: 'bg-gray-500' },
    { id: 'triage_pending', label: 'Triage', color: 'bg-yellow-500' },
    { id: 'assigned', label: 'Assigned', color: 'bg-blue-500' },
    { id: 'in_progress', label: 'In Progress', color: 'bg-purple-500' },
    { id: 'resolved', label: 'Resolved', color: 'bg-green-500' }
  ];
  
  let draggedTicket: Ticket | null = $state(null);
  let dragOverColumn: TicketStatus | null = $state(null);
  
  function getTicketsByStatus(status: TicketStatus): Ticket[] {
    return $tickets.filter(t => t.status === status);
  }
  
  function handleDragStart(ticket: Ticket): void {
    draggedTicket = ticket;
  }
  
  function handleDragOver(event: DragEvent, columnId: TicketStatus): void {
    event.preventDefault();
    dragOverColumn = columnId;
  }
  
  function handleDragLeave(): void {
    dragOverColumn = null;
  }
  
  function handleDrop(columnId: TicketStatus): void {
    if (draggedTicket && draggedTicket.status !== columnId) {
      updateTicketStatus(draggedTicket.id, columnId);
    }
    draggedTicket = null;
    dragOverColumn = null;
  }
  
  function handleSelectTicket(ticket: Ticket): void {
    onselectTicket({ id: ticket.id });
  }
</script>

<div class="h-full p-6 overflow-x-auto">
  <div class="flex gap-4 h-full min-w-max">
    {#each columns as column}
      {@const columnTickets = getTicketsByStatus(column.id)}
      <div 
        class="w-80 flex flex-col bg-card rounded-xl border border-border transition-all duration-200 {dragOverColumn === column.id ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}"
        ondragover={(e) => handleDragOver(e, column.id)}
        ondragleave={handleDragLeave}
        ondrop={() => handleDrop(column.id)}
        role="region"
        aria-label="{column.label} column"
      >
        <div class="p-4 border-b border-border">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full {column.color}"></span>
              <h3 class="font-medium text-foreground">{column.label}</h3>
            </div>
            <span class="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
              {columnTickets.length}
            </span>
          </div>
        </div>
        
        <div class="flex-1 p-3 overflow-y-auto space-y-3">
          {#each columnTickets as ticket (ticket.id)}
            <TicketCard 
              {ticket}
              isSelected={selectedTicketId === ticket.id}
              onselect={() => handleSelectTicket(ticket)}
              ondragstart={() => handleDragStart(ticket)}
            />
          {/each}
          
          {#if columnTickets.length === 0}
            <div class="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <svg class="w-8 h-8 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span class="text-sm">No tickets</span>
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>
