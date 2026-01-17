<script lang="ts">
  import { slide, fade } from 'svelte/transition';
  import type { AIReasoning, ReasoningStep } from '$lib/stores/tickets';
  
  interface Props {
    reasoning: AIReasoning;
    onfoo?: () => void; // Example of callback prop for event handling
  }
  
  let { reasoning, onfoo }: Props = $props();
  let isExpanded = true;
  let visibleSteps = 0;
  
  $effect(() => {
    if (!isExpanded) {
      visibleSteps = 0;
    }
  });
  
  $effect(() => {
    if (isExpanded && visibleSteps < reasoning.steps.length) {
      const timer = setTimeout(() => {
        visibleSteps = visibleSteps + 1;
      }, 400);
      return () => clearTimeout(timer);
    }
  });
  
  type StepType = ReasoningStep['type'];
  
  const stepIcons: Record<StepType, string> = {
    analysis: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />',
    hypothesis: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />',
    recommendation: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />',
    context: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
  };
  
  const stepColors: Record<StepType, string> = {
    analysis: 'text-primary border-primary/30 bg-primary/5',
    hypothesis: 'text-accent border-accent/30 bg-accent/5',
    recommendation: 'text-success border-success/30 bg-success/5',
    context: 'text-muted-foreground border-border bg-muted/30'
  };

  function toggleExpanded(): void {
    isExpanded = !isExpanded;
    if (onfoo) {
      onfoo();
    }
  }
</script>

<div class="rounded-xl border border-border overflow-hidden">
  <button
    type="button"
    onclick={toggleExpanded}
    class="w-full flex items-center justify-between p-4 bg-gradient-to-r from-accent/10 to-primary/10 hover:from-accent/15 hover:to-primary/15 transition-colors"
  >
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-primary flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <div class="text-left">
        <span class="text-sm font-medium text-foreground block">AI Reasoning</span>
        <span class="text-xs text-muted-foreground">{reasoning.summary}</span>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-1.5">
        <div class="h-1.5 w-16 bg-muted rounded-full overflow-hidden">
          <div 
            class="h-full bg-gradient-to-r from-accent to-primary rounded-full transition-all duration-500"
            style="width: {reasoning.confidence * 100}%"
          ></div>
        </div>
        <span class="text-xs text-muted-foreground">{Math.round(reasoning.confidence * 100)}%</span>
      </div>
      
      <svg 
        class="w-5 h-5 text-muted-foreground transition-transform duration-200 {isExpanded ? 'rotate-180' : ''}"
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
  </button>
  
  {#if isExpanded}
    <div class="p-4 space-y-3 bg-card" transition:slide={{ duration: 200 }}>
      {#each reasoning.steps as step, index}
        {#if index < visibleSteps}
          <div 
            class="relative pl-6 pb-3 ml-3 {index < reasoning.steps.length - 1 ? 'border-l-2 border-border/50' : ''}"
            transition:fade={{ duration: 200, delay: index * 50 }}
          >
            <div class="absolute -left-3 top-0 w-6 h-6 rounded-full border-2 flex items-center justify-center {stepColors[step.type]}">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {@html stepIcons[step.type]}
              </svg>
            </div>
            
            <div class="ml-2">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-medium text-foreground">{step.title}</span>
                <span class="text-xs font-mono text-muted-foreground">{step.timestamp}</span>
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed">{step.content}</p>
            </div>
          </div>
        {/if}
      {/each}
      
      {#if visibleSteps < reasoning.steps.length}
        <div class="flex items-center gap-2 pl-9 py-2" transition:fade>
          <div class="flex gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style="animation-delay: 300ms"></span>
          </div>
          <span class="text-xs text-muted-foreground">Processing...</span>
        </div>
      {/if}
    </div>
  {/if}
</div>
