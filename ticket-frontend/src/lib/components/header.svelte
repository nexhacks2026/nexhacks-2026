<script lang="ts">
  import { tickets, type Ticket } from '../stores/tickets.ts';
  import { currentUser, users, setCurrentUser, getUserInitials } from '../stores/users.ts';
  import CreateTicketModal from './create-ticket-modal.svelte';
  
  let ticketList: Ticket[] = $tickets;
  let showUserModal = $state(false);
  let showTicketModal = $state(false);
  
  let stats: { total: number; inbox: number; assigned: number; inProgress: number; critical: number } = {
    total: ticketList.length,
    inbox: ticketList.filter(t => t.status === 'inbox' || t.status === 'triage_pending').length,
    assigned: ticketList.filter(t => t.status === 'assigned').length,
    inProgress: ticketList.filter(t => t.status === 'in_progress').length,
    critical: ticketList.filter(t => t.priority === 'critical').length
  };
  
  function handleSwitchUser(user: typeof users[0]) {
    setCurrentUser(user);
    showUserModal = false;
  }
  
  function openUserModal(e: MouseEvent) {
    e.stopPropagation();
    console.log('Opening user modal');
    showUserModal = true;
  }
  
  function closeUserModal() {
    console.log('Closing user modal');
    showUserModal = false;
  }
</script>

<header class="h-[60px] border-b border-border bg-card px-6 flex items-center justify-between">
  <div class="flex items-center gap-4">
    <div class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
        <img 
          src="/logo-white.svg"
          alt="logo"
          class="w-5 h-5"
        >
      </div>
      <span class="font-semibold text-foreground" style="font-family: monospace; font-size: 1.125rem;">narr0w</span>
    </div>
  </div>
  
  <div class="flex items-center gap-6">
    <div class="flex items-center gap-4 text-sm">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-muted-foreground"></span>
        <span class="text-muted-foreground">{stats.inbox} Inbox</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-primary"></span>
        <span class="text-muted-foreground">{stats.assigned} Assigned</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-accent"></span>
        <span class="text-muted-foreground">{stats.inProgress} In Progress</span>
      </div>
      {#if stats.critical > 0}
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-destructive animate-pulse"></span>
          <span class="text-destructive">{stats.critical} Critical</span>
        </div>
      {/if}
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-muted-foreground"></span>
        <span class="text-muted-foreground">{stats.total} Total</span>
      </div>
    </div>
    
    <!-- Search and Plus Icon -->
    <div class="flex items-center gap-2">

      <!-- Search Button -->
      <button class="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground cursor-pointer" aria-label="Search">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>

      <!-- Plus Button -->
      <button onclick={openTicketModal} class="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground cursor-pointer" aria-label="Add ticket">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      </button>

      <!-- Switch User Button/Logo & Display as two letters i.e 'AS'-->
      <button 
        onclick={openUserModal}
        aria-label="Switch User" 
        class="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-sm font-medium text-secondary-foreground hover:bg-secondary/80 transition-colors cursor-pointer"
      >
        {#if $currentUser}
          {getUserInitials($currentUser.name)}
        {:else}
          ?
        {/if}
      </button>
    </div>
  </div>
</header>

<!-- User Switcher Modal -->
{#if showUserModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={closeUserModal} onkeydown={(e) => e.key === 'Escape' && closeUserModal()} role="button" tabindex="0">
    <div class="bg-card rounded-lg shadow-lg p-6 max-w-md w-full mx-4" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="dialog" aria-modal="true" tabindex="-1">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-foreground">Switch User</h2>
        <button onclick={closeUserModal} class="text-muted-foreground hover:text-foreground" aria-label="Close modal">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="space-y-2">
        {#each users as user}
          <button
            onclick={() => handleSwitchUser(user)}
            class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted transition-colors {$currentUser?.id === user.id ? 'bg-muted ring-2 ring-primary' : ''}"
          >
            <div class="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-sm font-medium text-secondary-foreground">
              {getUserInitials(user.name)}
            </div>
            <div class="flex-1 text-left">
              <div class="font-medium text-foreground">{user.name}</div>
              <div class="text-xs text-muted-foreground">{user.id}</div>
            </div>
            {#if $currentUser?.id === user.id}
              <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  </div>
{/if}

<!-- Add Ticket Modal -->
{#if showTicketModal}
  <CreateTicketModal bind:show={showTicketModal} />
{/if}
