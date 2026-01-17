<script lang="ts">
  import { fly } from 'svelte/transition';
  import { updateTicketStatus, updateTicketTitle, type Ticket, type TicketStatus, type TicketPriority } from '$lib/stores/tickets';
  import AiReasoningPanel from './ai-reasoning-panel.svelte';
  
  interface Props {
    ticket: Ticket;
    dismiss?: () => void;
  }
  
  let { ticket, dismiss }: Props = $props();
  
  let isEditingTitle = $state(false);
  let editedTitle = $state('');
  
  $effect(() => {
    editedTitle = ticket.title;
  });
  
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
  
  function handleEditTitle(): void {
    isEditingTitle = true;
  }
  
  async function handleSaveTitle(): Promise<void> {
    if (editedTitle.trim() && editedTitle !== ticket.title) {
      try {
        await updateTicketTitle(ticket.id, editedTitle.trim());
        // Don't mutate ticket directly - the store will reload tickets
      } catch (error) {
        console.error('Failed to save title:', error);
        alert('Failed to update ticket title');
        editedTitle = ticket.title;
      }
    }
    isEditingTitle = false;
  }
  
  function handleCancelEdit(): void {
    editedTitle = ticket.title;
    isEditingTitle = false;
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
        {#if isEditingTitle}
          <div class="flex items-center gap-2 mb-2">
            <input
              type="text"
              bind:value={editedTitle}
              class="flex-1 text-lg font-semibold bg-background border border-border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary"
              autofocus
            />
            <button
              type="button"
              onclick={handleSaveTitle}
              class="p-1.5 rounded hover:bg-muted text-primary"
              aria-label="Save"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              type="button"
              onclick={handleCancelEdit}
              class="p-1.5 rounded hover:bg-muted text-muted-foreground"
              aria-label="Cancel"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        {:else}
          <div class="flex items-start justify-between gap-2 mb-2">
            <h2 class="text-lg font-semibold text-foreground">{ticket.title}</h2>
            <button
              type="button"
              onclick={handleEditTitle}
              class="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Edit title"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
          </div>
        {/if}
        <p class="text-sm text-muted-foreground leading-relaxed">{ticket.description}</p>
      </div>
      
      <div class="space-y-4">
       
        <!-- Status Section -->
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
        
        <!-- Assignee Section -->
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
        
        <!-- Created Section -->
        <div class="flex items-center justify-between py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground">Created</span>
          <span class="text-sm text-foreground">{formatDate(ticket.createdAt)}</span>
        </div>
        
        <!-- Updated Section -->
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
      
      <!-- Ai Reasoning Part -->
      {#if ticket.aiReasoning}
        <AiReasoningPanel reasoning={ticket.aiReasoning} />
      {/if}
    </div>
  </div>
</aside>
