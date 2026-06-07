<template>
  <div v-if="metrics && Object.keys(metrics).length" class="orchestrator-metrics" aria-live="polite">
    <span class="metric-chip primary">
      {{ orchestratorLabel }}
    </span>
    <span v-if="metrics.fallback" class="metric-chip warn">
      已降级
      <template v-if="chain.length"> → {{ chain.join(' → ') }}</template>
    </span>
    <span v-if="metrics.interrupted" class="metric-chip danger">待确认高风险</span>
    <span v-if="metrics.dify_used" class="metric-chip ok">Dify 直连</span>
    <span v-if="metrics.elapsed_ms" class="metric-chip muted">{{ (metrics.elapsed_ms / 1000).toFixed(1) }}s</span>
    <span v-if="metrics.trace_count" class="metric-chip muted">{{ metrics.trace_count }} 步 trace</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  metrics: { type: Object, default: () => ({}) }
})

const labels = {
  swarm: 'Swarm',
  langgraph: 'LangGraph',
  dify: 'Dify'
}

const orchestratorLabel = computed(() => labels[props.metrics?.orchestrator] || props.metrics?.orchestrator || '未知')
const chain = computed(() => props.metrics?.fallback_chain || [])
</script>
