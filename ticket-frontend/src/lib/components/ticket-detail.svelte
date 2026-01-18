<script lang="ts">
  import { fly } from 'svelte/transition';
  import { updateTicketStatus, updateTicketTitle, updateTicketDescription, deleteTicket, assignTicketToAgent, releaseTicketFromAgent, type Ticket, type TicketStatus, type TicketPriority } from '$lib/stores/tickets';
  import { users, currentUser } from '$lib/stores/users.ts';
  import AiReasoningPanel from './ai-reasoning-panel.svelte';
  import UnassignModal from './unassign-modal.svelte';
  
  interface Props {
    ticket: Ticket;
    dismiss?: () => void;
  }
  
  let { ticket, dismiss }: Props = $props();
  
  let isEditingTitle = $state(false);
  let editedTitle = $state('');
  
  let isEditingDescription = $state(false);
  let editedDescription = $state('');
  
  let showUnassignModal = $state(false);
  let pendingUnassignUser = $state<string | null>(null);

  $effect(() => {
    editedTitle = ticket.title;
    editedDescription = ticket.description;
  });
  
  interface StatusOption {
    id: TicketStatus;
    label: string;
  }
  
  const allStatuses: StatusOption[] = [
    { id: 'inbox', label: 'Inbox' },
    { id: 'triage_pending', label: 'Triage' },
    { id: 'assigned', label: 'Assigned' },
    { id: 'in_progress', label: 'In Progress' },
    { id: 'resolved', label: 'Resolved' }
  ];
  
  // Filter statuses based on user role
  let availableStatuses = $derived(
    $currentUser?.id === 'user-0'
      ? allStatuses.filter(s => s.id !== 'triage_pending') // Admin can't set triage
      : allStatuses.filter(s => s.id !== 'inbox' && s.id !== 'triage_pending') // Non-admin can't set inbox or triage
  );
  
  // Check if status changes should be disabled (for triage tickets)
  let isStatusLocked = $derived(ticket.status === 'triage_pending' || ticket.status === 'triaging');
  
  // Check if coding agent is working on this ticket
  let isCodingAgentWorking = $derived(
    ticket.assignee?.id === 'coding-agent' && ticket.status === 'assigned'
  );
  
  // Only admin can delete tickets
  let canDelete = $derived($currentUser?.id === 'user-0');
  
  // When ticket is in triage or coding agent is working, admin can only delete (all other actions disabled)
  let canEdit = $derived(!isStatusLocked && !isCodingAgentWorking);
  
  const priorityStyles: Record<TicketPriority, string> = {
    critical: 'bg-destructive text-white',
    high: 'bg-warning text-black',
    medium: 'bg-primary text-white',
    low: 'bg-muted text-muted-foreground'
  };
  
  function handleStatusChange(newStatus: TicketStatus): void {
    updateTicketStatus(ticket.id, newStatus);
  }
  
  async function handleAssigneeChange(userId: string): Promise<void> {
    try {
      if (userId) {
        // If reassigning, just assign directly (backend handles reassignment)
        await assignTicketToAgent(ticket.id, userId);
      } else {
        // If unassigning, show modal to get reason (admin only)
        if (ticket.assignee && $currentUser?.id === 'user-0') {
          pendingUnassignUser = ticket.assignee.id;
          showUnassignModal = true;
        }
      }
    } catch (error) {
      console.error('Failed to update assignee:', error);
      alert('Failed to update assignee');
    }
  }
  
  async function handleUnassignConfirm(reason: string): Promise<void> {
    showUnassignModal = false;
    
    if (!pendingUnassignUser) return;
    
    try {
      // Append the unassignment reason to the description
      if (reason) {
        const timestamp = new Date().toLocaleString();
        const appendText = `\n\n---\n**Unassignment Note** (${timestamp}):\nPreviously assigned to ${ticket.assignee?.name}. Reason: ${reason}`;
        await updateTicketDescription(ticket.id, ticket.description + appendText);
      }
      
      // Release the ticket with retriage flag to send it back to AI
      await releaseTicketFromAgent(
        ticket.id, 
        pendingUnassignUser,
        reason ? `Admin unassigned: ${reason}` : undefined,
        true  // Set retriage=true to send back to INBOX for AI re-triage
      );
      
      pendingUnassignUser = null;
    } catch (error) {
      console.error('Failed to unassign:', error);
      alert('Failed to unassign ticket');
    }
  }
  
  function handleUnassignCancel(): void {
    showUnassignModal = false;
    pendingUnassignUser = null;
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
  
  // 
  // Editing the Title
  // 
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
  
  function handleCancelEditTitle(): void {
    editedTitle = ticket.title;
    isEditingTitle = false;
  }

  // 
  // Editing the Description
  // 
  function handleEditDescription(): void {
    isEditingDescription = true;
  }
  
  async function handleSaveDescription(): Promise<void> {
    const newDescription = editedDescription.trim();
    if (newDescription !== ticket.description) {
      try {
        await updateTicketDescription(ticket.id, newDescription);
        // Don't mutate ticket directly - the store will reload tickets
      } catch (error) {
        console.error('Failed to save description:', error);
        alert('Failed to update ticket description');
        editedDescription = ticket.description;
      }
    }
    isEditingDescription = false;
  }
  
  function handleCancelEditDescription(): void {
    editedDescription = ticket.description;
    isEditingDescription = false;
  }
  
  let isDeleting = $state(false);
  
  async function handleDelete(): Promise<void> {
    if (!confirm('Are you sure you want to delete this ticket? This action cannot be undone.')) {
      return;
    }
    
    isDeleting = true;
    try {
      await deleteTicket(ticket.id);
      dismiss?.();
    } catch (error) {
      console.error('Failed to delete ticket:', error);
      alert('Failed to delete ticket');
    } finally {
      isDeleting = false;
    }
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
      <svg class="w-5 h-5 cursor-pointer" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
  
  <div class="flex-1 overflow-y-auto">
    <div class="p-6 space-y-6">

      <!-- Title + Edit Title -->
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
              onclick={handleCancelEditTitle}
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
            
            <!-- Edit Title Button -->
            {#if canEdit}
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
            {/if}
          </div>
        {/if}
      </div>
      
      <!-- Lowe Stuff -->
      <div class="space-y-4">
       
        <!-- Status Section -->
        {#if canEdit}
          <div class="flex items-center justify-between py-3 border-b border-border/50">
            <span class="text-sm text-muted-foreground">Status</span>
            <div class="flex gap-1">
              {#each availableStatuses as status}
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
        {:else if isCodingAgentWorking}
          <!-- Show locked status for coding agent tickets -->
          <div class="flex items-center justify-between py-3 border-b border-border/50">
            <span class="text-sm text-muted-foreground">Status</span>
            <div class="text-xs px-2.5 py-1 rounded-md bg-purple-500/20 text-purple-500 flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Coding Agent (Locked)
            </div>
          </div>
        {:else}
          <!-- Show locked status for triage tickets -->
          <div class="flex items-center justify-between py-3 border-b border-border/50">
            <span class="text-sm text-muted-foreground">Status</span>
            <div class="text-xs px-2.5 py-1 rounded-md bg-yellow-500/20 text-yellow-500 flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Triage (Locked)
            </div>
          </div>
        {/if}
        
        <!-- Description + Edit Desc Section -->
        <div class="flex flex-col py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground mb-2">Description</span>
          {#if isEditingDescription}
          <div class="flex flex-col gap-2 mb-2">
            <textarea
              bind:value={editedDescription}
              class="w-full text-sm text-foreground leading-relaxed bg-background border border-border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary resize-none min-h-[80px]"
              rows="4"
              autofocus
            ></textarea>
            <div class="flex justify-end gap-2">
              <button
                type="button"
                onclick={handleCancelEditDescription}
                class="p-1.5 rounded hover:bg-muted text-muted-foreground"
                aria-label="Cancel"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <button
                type="button"
                onclick={handleSaveDescription}
                class="p-1.5 rounded hover:bg-muted text-primary"
                aria-label="Save"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </div>
          {:else}
            <div class="flex items-start justify-between gap-2 mb-2">
              {#if ticket.description}
                <p class="text-sm text-foreground leading-relaxed">{ticket.description}</p>
              {:else}
                <p class="text-sm text-foreground leading-relaxed">Empty</p>
              {/if}
              
              <!-- Edit Description Button -->
              {#if canEdit}
                <button
                  type="button"
                  onclick={handleEditDescription}
                  class="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Edit description"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
              {/if}
            </div>
          {/if}
          
        </div>

        <!-- Assignee Section -->
        {#if canEdit}
          <div class="py-3 border-b border-border/50">
            <span class="text-sm text-muted-foreground block mb-2">Assigned To</span>
            <select
              value={ticket.assignee?.id || ''}
              onchange={(e) => handleAssigneeChange(e.currentTarget.value)}
              disabled={$currentUser?.id !== 'user-0'}
              class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">Unassigned</option>
              {#each users.filter(u => u.id !== 'user-0') as user}
                <option value={user.id}>{user.name}</option>
              {/each}
            </select>
          </div>
        {/if}
        
        <!-- Category Section -->
        <div class="flex items-center justify-between py-3 border-b border-border/50">
          <span class="text-sm text-muted-foreground">Category</span>
          {#if ticket.category}
            <span class="text-sm px-2.5 py-1 rounded-md bg-accent/10 text-accent capitalize">
              {ticket.category.toLowerCase().replace(/_/g, ' ')}
            </span>
          {:else}
            <span class="text-sm text-muted-foreground italic">None</span>
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
        
        <!-- Delete Button -->
        {#if canDelete}
          <div class="py-4 border-t border-border/50">
            <button
              type="button"
              onclick={handleDelete}
              disabled={isDeleting}
              class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive hover:text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              {#if isDeleting}
                Deleting...
              {:else}
                Delete Ticket
              {/if}
            </button>
          </div>
        {/if}
      </div>
      
      <!-- Ai Reasoning Part -->
      {#if ticket.aiReasoning}
        <AiReasoningPanel reasoning={ticket.aiReasoning} status={ticket.status} />
      {/if}
    </div>
  </div>
</aside>

<UnassignModal 
  show={showUnassignModal} 
  ticketId={ticket.id} 
  currentAssignee={ticket.assignee?.name || ''} 
  onconfirm={handleUnassignConfirm}
  oncancel={handleUnassignCancel}
/>
