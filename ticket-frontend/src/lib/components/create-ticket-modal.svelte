<script lang="ts">
  import { addTicket, assignTicketToAgent } from '../stores/tickets.ts';
  import { users, currentUser } from '../stores/users.ts';
  import { toast } from '../stores/toast.ts';
  
  let { show = $bindable(false) } = $props();
  
  let ticketForm = $state({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    category: '' as string,
    assignee: '' as string,
    tags: ''
  });
  
  function closeModal() {
    show = false;
    // Reset form
    ticketForm = {
      title: '',
      description: '',
      priority: 'medium',
      category: '',
      assignee: '',
      tags: ''
    };
  }
  
  async function handleSubmitTicket() {
    if (!ticketForm.title.trim() || !ticketForm.description.trim()) {
      alert('Please fill in title and description');
      return;
    }
    
    try {
      
      // Parse tags from comma-separated string
      const tags = ticketForm.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);
      
      const ticketId = await addTicket(
        ticketForm.title,
        ticketForm.description,
        ticketForm.priority,
        ticketForm.category || undefined,
        tags.length > 0 ? tags : undefined
      );
      
      // Assign user if selected
      if (ticketForm.assignee) {
        await assignTicketToAgent(ticketId, ticketForm.assignee);
      }
      
      // Show success toast
      toast.success('Ticket created successfully!');
      
      closeModal();
    } catch (error) {
      console.error('Error creating ticket:', error);
      alert('Failed to create ticket: ' + (error instanceof Error ? error.message : String(error)));
    }
  }
</script>

<!-- Add Ticket Modal -->
{#if show}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={(e) => e.target === e.currentTarget && closeModal()} onkeydown={(e) => e.key === 'Escape' && closeModal()} role="button" tabindex="0">
    <div class="bg-card rounded-lg shadow-lg p-6 max-w-lg w-full mx-4" role="dialog" aria-modal="true" tabindex="-1">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-foreground">Create New Ticket</h2>
        <button onclick={closeModal} class="text-muted-foreground hover:text-foreground" aria-label="Close modal">
          <svg class="w-5 h-5 cursor-pointer" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            <option value="">None (optional)</option>
            <option value="bug_report">Bug Report</option>
            <option value="feature_request">Feature Request</option>
            <option value="technical_support">Technical Support</option>
            <option value="billing">Billing</option>
            <option value="admin">Admin</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <!-- Assignee -->
        <div>
          <label for="ticket-assignee" class="block text-sm font-medium text-foreground mb-1">Assign To</label>
          <select
            id="ticket-assignee"
            bind:value={ticketForm.assignee}
            disabled={$currentUser?.id !== 'user-0'}
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="">Unassigned (optional)</option>
            {#each users.filter(u => u.id !== 'user-0') as user}
              <option value={user.id}>{user.name}</option>
            {/each}
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
            onclick={closeModal}
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
