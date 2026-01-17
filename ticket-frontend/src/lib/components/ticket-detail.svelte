<script lang="ts">
  import { fly } from 'svelte/transition';
  import { updateTicketStatus, type Ticket, type TicketStatus, type TicketPriority } from '$lib/stores/tickets';
  import AiReasoningPanel from './ai-reasoning-panel.svelte';
  
  interface Props {
    ticket: Ticket;
    dismiss?: () => void;
  }
  
  let { ticket, dismiss }: Props = $props();
  
  interface StatusOption {
    id: TicketStatus;
    label: string;
  }
  
  const statuses: StatusOption[] = [
    { id: 'open', label: 'Open' },
    { id: 'in_progress', label: 'In Progress' },
    { id: 'review', label: 'Review' },
    { id: 'done', label: 'Done' }
  ];
  
  const priorityStyles: Record<TicketPriority, string> = {
    critical: 'bg-destructive text-white',
    high: 'bg-warning text-black',
    medium: 'bg-primary text-white',
    low: 'bg-muted text-muted-foreground'
  };
  
  function handleStatusChange(newStatus: TicketStatus): void {
    updateTicketStatus(ticket.id, newStatus);
  }
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  function handleDismiss(): void {
    dismiss?.();
  }
</script>

<aside 
  class="fixed right-0 top-[60px] w-[480px] h-[calc(100vh-60px)] bg-card border-l border-border overflow-hidden flex flex-col"
  transition:fly={{ x: 480, duration: 300 }}
>
  <div class="flex items-center justify-between p-4 border-b border-border">
    <div class="flex items-center gap-3">
      <span class="text-sm font-mono text-muted-foreground">{ticket.id}</span>
      <span class="text-xs px-2 py-1 rounded-full capitalize {priorityStyles[ticket.priority]}">
        {ticket.priority}
      </span>
    </div>
    <button 
      type="button"
      onclick={handleDismiss}
      class="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
      aria-label="Close"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
  
  <div class="flex-1 overflow-y-auto">
    <div class="p-6 space-y-6">
      <div>
        <h2 class="text-lg font-semibold text-foreground mb-2">{ticket.title}</h2>
        <p class="text-sm text-muted-foreground leading-relaxed">{ticket.description}</p>
      </div>
      
      <div class="space-y-4">
        <div class="flex items-center justify-between py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground">Status</span>
          <div class="flex gap-1">
            {#each statuses as status}
              <button
                type="button"
                onclick={() => handleStatusChange(status.id)}
                class="text-xs px-2.5 py-1 rounded-md transition-all duration-200 {ticket.status === status.id ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-secondary'}"
                aria-label="Change status to {status.label}"
              >
                {status.label}
              </button>
            {/each}
          </div>
        </div>
        
        <div class="flex items-center justify-between py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground">Assignee</span>
          {#if ticket.assignee}
            <div class="flex items-center gap-2">
              <div 
                class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white"
                style="background-color: {ticket.assignee.color}"
              >
                {ticket.assignee.avatar}
              </div>
              <span class="text-sm text-foreground">{ticket.assignee.name}</span>
            </div>
          {:else}
            <span class="text-sm text-muted-foreground italic">Unassigned</span>
          {/if}
        </div>
        
        <div class="flex items-center justify-between py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground">Created</span>
          <span class="text-sm text-foreground">{formatDate(ticket.createdAt)}</span>
        </div>
        
        <div class="flex items-center justify-between py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground">Updated</span>
          <span class="text-sm text-foreground">{formatDate(ticket.updatedAt)}</span>
        </div>
        
        {#if ticket.labels && ticket.labels.length > 0}
          <div class="py-3">
            <span class="text-sm text-muted-foreground block mb-2">Labels</span>
            <div class="flex flex-wrap gap-2">
              {#each ticket.labels as label}
                <span class="text-xs px-2 py-1 rounded-md bg-secondary text-secondary-foreground">
                  {label}
                </span>
              {/each}
            </div>
          </div>
        {/if}
      </div>
      
      {#if ticket.aiReasoning}
        <AiReasoningPanel reasoning={ticket.aiReasoning} />
      {/if}
    </div>
  </div>
</aside>
