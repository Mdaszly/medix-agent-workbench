<template>
  <div class="orchestrator-bar" role="group" aria-label="编排模式选择">
    <div class="orchestrator-head">
      <strong>编排引擎</strong>
      <span class="orchestrator-hint">选择 Agent 工作流执行路径</span>
    </div>
    <div class="orchestrator-grid">
      <button
        v-for="item in options"
        :key="item.key"
        type="button"
        class="orchestrator-card"
        :class="{ active: modelValue === item.key }"
        :aria-pressed="modelValue === item.key"
        @click="$emit('update:modelValue', item.key)"
      >
        <span class="orchestrator-badge" :class="item.key">{{ item.short }}</span>
        <span class="orchestrator-title">{{ item.label }}</span>
        <span class="orchestrator-desc">{{ item.desc }}</span>
        <span class="orchestrator-meta">{{ item.meta }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: 'swarm' }
})

defineEmits(['update:modelValue'])

const options = [
  {
    key: 'swarm',
    short: 'SW',
    label: 'Swarm 多 Agent',
    desc: '自研编排，RAG + 联网 + 多 Agent 协作',
    meta: '默认生产链路 · 响应较快'
  },
  {
    key: 'langgraph',
    short: 'LG',
    label: 'LangGraph 状态机',
    desc: '显式状态图，高风险可 interrupt 确认',
    meta: '可观测 trace · 多轮记忆'
  },
  {
    key: 'dify',
    short: 'DF',
    label: 'Dify 云端编排',
    desc: '低代码工作流，失败自动降级',
    meta: '约 1–2 分钟 · 三级 fallback'
  }
]
</script>
