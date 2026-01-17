<script lang="ts">
  import type { Ticket, TicketPriority } from '$lib/stores/tickets';
  
  interface Props {
    ticket: Ticket;
    isSelected?: boolean;
    isDraggable?: boolean;
    onselect?: () => void;
    ondragstart?: () => void;
  }
  
  let { ticket, isSelected = false, isDraggable = true, onselect, ondragstart }: Props = $props();
  
  const priorityStyles: Record<TicketPriority, string> = {
    critical: 'bg-destructive/10 text-destructive border-destructive/30',
    high: 'bg-warning/10 text-warning border-warning/30',
    medium: 'bg-primary/10 text-primary border-primary/30',
    low: 'bg-muted text-muted-foreground border-border'
  };
  
  function formatTimeAgo(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'Just now';
  }
</script>

<button
  class="w-full text-left p-4 rounded-lg border transition-all duration-200 group relative overflow-hidden {isSelected ? 'bg-primary/5 border-primary ring-1 ring-primary/50' : 'bg-muted border-border hover:border-muted-foreground'} {isDraggable ? 'cursor-pointer' : 'cursor-default'}"
  draggable={isDraggable}
  ondragstart={ondragstart}
  onclick={onselect}
>
  {#if !isDraggable}
    <div class="absolute inset-0 triage-gradient pointer-events-none"></div>
  {/if}
  <div class="flex items-start justify-between gap-2 mb-2 relative z-10">
    <h4 class="font-medium text-foreground text-sm mb-2 line-clamp-2 group-hover:text-primary transition-colors relative z-10">
    {ticket.title}
    </h4>
    <span class="text-xs px-2 py-0.5 rounded-full border capitalize relative z-10 {priorityStyles[ticket.priority]}">
      {ticket.priority}
    </span>
  </div>
  
  
  
  <div class="flex items-center justify-between relative z-10">
    <div class="flex items-center gap-2">
      {#if ticket.assignee}
        <div 
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white"
          style="background-color: {ticket.assignee.color}"
          title={ticket.assignee.name}
        >
          {ticket.assignee.avatar}
        </div>
      {:else}
        <div class="w-6 h-6 rounded-full bg-muted border border-dashed border-muted-foreground flex items-center justify-center">
          <svg class="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      {/if}
    </div>
    
    <div class="flex items-center gap-2 text-xs text-muted-foreground relative z-10">
      {#if ticket.aiReasoning}
        <div class="flex items-center gap-1 text-accent" title="AI analysis available">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      {/if}
      <span>{formatTimeAgo(ticket.updatedAt)}</span>
    </div>
  </div>
  
  {#if ticket.labels && ticket.labels.length > 0}
    <div class="flex flex-wrap gap-1 mt-3">
      {#each ticket.labels.slice(0, 3) as label}
        <span class="text-xs px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">
          {label}
        </span>
      {/each}
      {#if ticket.labels.length > 3}
        <span class="text-xs px-1.5 py-0.5 rounded bg-secondary text-muted-foreground">
          +{ticket.labels.length - 3}
        </span>
      {/if}
    </div>
  {/if}
</button>

<style>
  @keyframes triageMove {
    0%, 100% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
  }

  .triage-gradient {
    background: linear-gradient(
      135deg,
      rgba(250, 204, 21, 0.35),
      rgba(234, 179, 8, 0.5),
      rgba(250, 204, 21, 0.35),
      rgba(225, 170, 5, 0.837)
    );
    background-size: 200% 200%;
    animation: triageMove 2s ease-in-out infinite;
    border: 2px solid rgba(234, 179, 8, 0.6);
    border-radius: 0.5rem;
  }
</style>
