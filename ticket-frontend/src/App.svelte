<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import TicketBoard from '$lib/components/ticket-board.svelte';
  import TicketDetail from '$lib/components/ticket-detail.svelte';
  import Header from '$lib/components/header.svelte';
  import { 
    tickets, 
    loading, 
    error, 
    loadTickets, 
    connectWebSocket, 
    disconnectWebSocket,
    type Ticket 
  } from '$lib/stores/tickets';
  import { websocket } from '$lib/api/websocket';

  let selectedTicketId: string | null = $state(null);
  let selectedTicket: Ticket | null = $state(null);
  let agentId = $state('agent-' + Math.random().toString(36).substring(7));

  // Subscribe to WebSocket status for UI feedback
  let wsStatus = $state('disconnected');
  const unsubscribeWs = websocket.status.subscribe(s => wsStatus = s);

  onMount(() => {
    // Connect to WebSocket for real-time updates
    connectWebSocket(agentId);
    
    // Load tickets from backend
    loadTickets();
    
    // Listen for search ticket selection
    const handleSearchSelection = (e: CustomEvent) => {
      handleSelectTicket({ id: e.detail.ticketId });
    };
    window.addEventListener('select-ticket', handleSearchSelection as EventListener);
    
    return () => {
      window.removeEventListener('select-ticket', handleSearchSelection as EventListener);
    };
  });

  onDestroy(() => {
    disconnectWebSocket();
    unsubscribeWs();
  });

  function handleSelectTicket(event: { id: string }) {
    // Toggle: if clicking the same ticket, close the detail panel
    if (selectedTicketId === event.id) {
      handleCloseDetail();
    } else {
      selectedTicketId = event.id;
      selectedTicket = $tickets.find(t => t.id === selectedTicketId) || null;
    }
  }

  function handleCloseDetail() {
    selectedTicketId = null;
    selectedTicket = null;
  }

  // Keep selected ticket in sync with store updates
  $effect(() => {
    if (selectedTicketId) {
      selectedTicket = $tickets.find(t => t.id === selectedTicketId) || null;
    }
  });
</script>

<div class="min-h-screen bg-background">
  <Header />
  
  <!-- Connection status indicators -->
  <div class="fixed bottom-4 right-4">

    <!-- Database Live Indicator -->
    <div class="z-50 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
      {wsStatus === 'connected' ? 'bg-green-500/20 text-green-400' : 
      wsStatus === 'connecting' ? 'bg-yellow-500/20 text-yellow-400' : 
      'bg-red-500/20 text-red-400'}">
      <span class="w-2 h-2 rounded-full 
        {wsStatus === 'connected' ? 'bg-green-500' : 
        wsStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
        'bg-red-500'}"></span>
      {wsStatus === 'connected' ? 'DB Live' : wsStatus === 'DB connecting' ? 'DB Connecting...' : 'DB Offline'}
    </div>

    <!-- n8n live indicator (NO FUNCTIONALITY YET) -->
    <div class="mt-2 z-50 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
      {wsStatus === 'connected' ? 'bg-pink-500/20 text-pink-400' : 
      wsStatus === 'connecting' ? 'bg-yellow-500/20 text-yellow-400' : 
      'bg-red-500/20 text-red-400'}">
      <span class="w-2 h-2 rounded-full 
        {wsStatus === 'connected' ? 'bg-pink-500' : 
        wsStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
        'bg-red-500'}"></span>
      {wsStatus === 'connected' ? 'n8n Live' : wsStatus === 'n8n connecting' ? 'n8n Connecting...' : 'n8n Offline'}
    </div>

  </div>
  
  <main class="flex h-[calc(100vh-60px)]">
    {#if $loading}
      <div class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-4">
          <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
          <span class="text-muted-foreground">Loading tickets...</span>
        </div>
      </div>
    {:else if $error}
      <div class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-4 text-center px-4">
          <div class="w-12 h-12 rounded-full bg-destructive/20 flex items-center justify-center">
            <svg class="w-6 h-6 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <p class="text-foreground font-medium">Failed to load tickets</p>
            <p class="text-sm text-muted-foreground mt-1">{$error}</p>
          </div>
          <button 
            onclick={() => loadTickets()}
            class="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    {:else}
      <div class="flex-1 overflow-hidden transition-all duration-300 {selectedTicket ? 'pr-[480px]' : ''}">
        <TicketBoard 
          {selectedTicketId}
          onselectTicket={handleSelectTicket}
        />
      </div>
      
      {#if selectedTicket}
        <TicketDetail 
          ticket={selectedTicket} 
          dismiss={handleCloseDetail}
        />
      {/if}
    {/if}
  </main>
</div>
