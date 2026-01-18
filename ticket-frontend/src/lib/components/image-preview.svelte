<script lang="ts">
  /**
   * ImagePreview component for displaying images from URLs
   * Includes error handling, loading states, and click-to-expand functionality
   */
  
  interface Props {
    urls: string[];
    maxHeight?: number;
  }
  
  let { urls, maxHeight = 300 }: Props = $props();
  
  interface ImageState {
    url: string;
    loading: boolean;
    error: boolean;
    expanded: boolean;
  }
  
  let images = $state<ImageState[]>([]);
  let expandedIndex = $state<number | null>(null);
  
  // Initialize image states when URLs change
  $effect(() => {
    images = urls.map(url => ({
      url,
      loading: true,
      error: false,
      expanded: false
    }));
  });
  
  function handleImageLoad(index: number) {
    images[index].loading = false;
    images[index].error = false;
  }
  
  function handleImageError(index: number) {
    images[index].loading = false;
    images[index].error = true;
  }
  
  function toggleExpand(index: number) {
    expandedIndex = expandedIndex === index ? null : index;
  }
  
  function closeExpanded() {
    expandedIndex = null;
  }
  
  // Close expanded view on Escape key
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && expandedIndex !== null) {
      closeExpanded();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if images.length > 0}
  <div class="space-y-3 mt-3">
    <div class="flex items-center gap-2 text-xs text-muted-foreground">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <span>Detected {images.length} {images.length === 1 ? 'image' : 'images'}</span>
    </div>
    
    <div class="grid grid-cols-1 gap-3">
      {#each images as image, i}
        <div class="relative rounded-lg border border-border overflow-hidden bg-muted/30">
          {#if image.loading}
            <div 
              class="flex items-center justify-center bg-muted/50"
              style="height: {maxHeight}px"
            >
              <div class="flex flex-col items-center gap-2">
                <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                <span class="text-xs text-muted-foreground">Loading image...</span>
              </div>
            </div>
          {/if}
          
          {#if image.error}
            <div 
              class="flex items-center justify-center bg-destructive/5"
              style="height: {maxHeight}px"
            >
              <div class="flex flex-col items-center gap-2 p-4 text-center">
                <svg class="w-10 h-10 text-destructive/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span class="text-xs text-destructive">Failed to load image</span>
                <a 
                  href={image.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="text-xs text-primary hover:underline break-all"
                >
                  Open in new tab
                </a>
              </div>
            </div>
          {:else}
            <button
              type="button"
              onclick={() => toggleExpand(i)}
              class="w-full cursor-zoom-in hover:opacity-90 transition-opacity"
              style="display: {image.loading ? 'none' : 'block'}"
            >
              <img
                src={image.url}
                alt="Ticket attachment"
                onload={() => handleImageLoad(i)}
                onerror={() => handleImageError(i)}
                class="w-full h-auto object-contain"
                style="max-height: {maxHeight}px"
              />
            </button>
            
            <!-- Image URL caption -->
            <div class="px-3 py-2 bg-muted/50 border-t border-border">
              <a 
                href={image.url} 
                target="_blank" 
                rel="noopener noreferrer"
                class="text-xs text-primary hover:underline break-all flex items-center gap-1"
              >
                <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <span class="truncate">{image.url}</span>
              </a>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
{/if}

<!-- Expanded Image Modal -->
{#if expandedIndex !== null && !images[expandedIndex].error}
  <div 
    class="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
    onclick={closeExpanded}
    role="button"
    tabindex="0"
    aria-label="Close expanded image"
  >
    <button
      type="button"
      onclick={closeExpanded}
      class="absolute top-4 right-4 p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
      aria-label="Close"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
    
    <div class="max-w-7xl max-h-[90vh] overflow-auto" onclick={(e) => e.stopPropagation()}>
      <img
        src={images[expandedIndex].url}
        alt="Expanded ticket attachment"
        class="w-auto h-auto max-w-full max-h-[90vh] object-contain"
      />
    </div>
    
    <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-lg text-sm">
      Click anywhere to close • ESC to exit
    </div>
  </div>
{/if}

<style>
  /* Smooth loading animation */
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>
