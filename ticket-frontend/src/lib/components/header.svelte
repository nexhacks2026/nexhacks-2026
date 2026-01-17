<script lang="ts">
  import { tickets, type Ticket, addTicket } from '../stores/tickets.ts';
  import { currentUser, users, setCurrentUser, getUserInitials } from '../stores/users.ts';
  
  let ticketList: Ticket[] = $tickets;
  let showUserModal = $state(false);
  let showTicketModal = $state(false);
  
  let ticketForm = $state({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    category: '' as '' | 'billing' | 'technical_support' | 'feature_request' | 'bug_report' | 'admin' | 'other',
    tags: ''
  });
  
  function openTicketModal() {
    showTicketModal = true;
  }
  
  function closeTicketModal() {
    showTicketModal = false;
    // Reset form
    ticketForm = {
      title: '',
      description: '',
      priority: 'medium',
      category: '',
      tags: ''
    };
  }
  
  async function handleSubmitTicket() {
    if (!ticketForm.title.trim() || !ticketForm.description.trim()) {
      alert('Please fill in title and description');
      return;
    }
    
    try {
      await addTicket(ticketForm.title, ticketForm.description, ticketForm.priority);
      closeTicketModal();
      alert('Ticket created successfully!');
    } catch (error) {
      alert('Failed to create ticket: ' + error);
    }
  }
  
  let stats: { total: number; open: number; inProgress: number; critical: number } = {
    total: ticketList.length,
    open: ticketList.filter(t => t.status === 'open').length,
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
        <span class="w-2 h-2 rounded-full bg-foreground"></span>
        <span class="text-muted-foreground">{stats.open} Open</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-primary"></span>
        <span class="text-muted-foreground">{stats.inProgress} Assigned</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-warning"></span>
        <span class="text-muted-foreground">{stats.inProgress} In Progress</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-muted-foreground"></span>
        <span class="text-muted-foreground">{stats.total} Total</span>
      </div>
      {#if stats.critical > 0}
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-destructive animate-pulse"></span>
          <span class="text-destructive">{stats.critical} Critical</span>
        </div>
      {/if}
    </div>
    
    <!-- Search and Plus Icon -->
    <div class="flex items-center gap-2">

      <!-- Search Button -->
      <button class="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground" aria-label="Search">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>

      <!-- Plus Button -->
      <button onclick={openTicketModal} class="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground" aria-label="Add ticket">
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
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={closeTicketModal} onkeydown={(e) => e.key === 'Escape' && closeTicketModal()} role="button" tabindex="0">
    <div class="bg-card rounded-lg shadow-lg p-6 max-w-lg w-full mx-4" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="dialog" aria-modal="true" tabindex="-1">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-foreground">Create New Ticket</h2>
        <button onclick={closeTicketModal} class="text-muted-foreground hover:text-foreground" aria-label="Close modal">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); handleSubmitTicket(); }}>
        <!-- Title -->
        <div>
          <label for="ticket-title" class="block text-sm font-medium text-foreground mb-1">Title *</label>
          <input
            id="ticket-title"
            type="text"
            bind:value={ticketForm.title}
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Enter ticket title"
            required
          />
        </div>
        
        <!-- Description -->
        <div>
          <label for="ticket-description" class="block text-sm font-medium text-foreground mb-1">Description *</label>
          <textarea
            id="ticket-description"
            bind:value={ticketForm.description}
            rows="4"
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="Describe the issue or request"
            required
          ></textarea>
        </div>
        
        <!-- Priority -->
        <div>
          <label for="ticket-priority" class="block text-sm font-medium text-foreground mb-1">Priority</label>
          <select
            id="ticket-priority"
            bind:value={ticketForm.priority}
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        
        <!-- Category -->
        <div>
          <label for="ticket-category" class="block text-sm font-medium text-foreground mb-1">Category</label>
          <select
            id="ticket-category"
            bind:value={ticketForm.category}
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Select category (optional)</option>
            <option value="billing">Billing</option>
            <option value="technical_support">Technical Support</option>
            <option value="feature_request">Feature Request</option>
            <option value="bug_report">Bug Report</option>
            <option value="admin">Admin</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <!-- Tags -->
        <div>
          <label for="ticket-tags" class="block text-sm font-medium text-foreground mb-1">Tags</label>
          <input
            id="ticket-tags"
            type="text"
            bind:value={ticketForm.tags}
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Comma-separated tags (optional)"
          />
        </div>
        
        <!-- Buttons -->
        <div class="flex gap-3 pt-2">
          <button
            type="button"
            onclick={closeTicketModal}
            class="flex-1 px-4 py-2 border border-border rounded-lg text-foreground hover:bg-muted transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Create Ticket
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
