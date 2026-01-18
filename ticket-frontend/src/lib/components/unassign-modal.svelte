<script lang="ts">
  interface Props {
    show: boolean;
    ticketId: string;
    currentAssignee: string;
    onconfirm: (reason: string) => void;
    oncancel: () => void;
  }
  
  let { show = false, ticketId, currentAssignee, onconfirm, oncancel }: Props = $props();
  
  let reason = $state('');
  
  function handleConfirm() {
    onconfirm(reason.trim());
    reason = '';
  }
  
  function handleCancel() {
    oncancel();
    reason = '';
  }
</script>

{#if show}
  <div 
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" 
    onclick={(e) => e.target === e.currentTarget && handleCancel()}
    onkeydown={(e) => e.key === 'Escape' && handleCancel()} 
    role="button" 
    tabindex="0"
  >
    <div class="bg-card rounded-lg shadow-lg p-6 max-w-lg w-full mx-4" role="dialog" aria-modal="true">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-foreground">Unassign Ticket</h2>
        <button onclick={handleCancel} class="text-muted-foreground hover:text-foreground" aria-label="Close modal">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="mb-4">
        <p class="text-sm text-muted-foreground mb-2">
          You are unassigning <span class="font-medium text-foreground">{currentAssignee}</span> from this ticket.
        </p>
        <p class="text-sm text-muted-foreground">
          Please provide a reason to help the AI understand why this assignment didn't work and improve future suggestions.
        </p>
      </div>
      
      <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); handleConfirm(); }}>
        <div>
          <label for="unassign-reason" class="block text-sm font-medium text-foreground mb-2">
            Reason for Unassignment
          </label>
          <textarea
            id="unassign-reason"
            bind:value={reason}
            rows="4"
            class="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="e.g., Wrong expertise area, workload too high, requires different skill set..."
            autofocus
          ></textarea>
        </div>
        
        <div class="flex gap-3">
          <button
            type="button"
            onclick={handleCancel}
            class="flex-1 px-4 py-2 border border-border rounded-lg text-foreground hover:bg-muted transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Unassign
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
