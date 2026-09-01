<template>
  <section class="tool-panel">
    <div class="tool-panel-header">
      <div>
        <p class="tool-kicker">实时 Agent 轨迹</p>
        <h3>工具调用面板</h3>
      </div>
      <el-tag size="small" type="success">{{ toolEvents.length }} 条</el-tag>
    </div>

    <el-empty
      v-if="toolEvents.length === 0"
      description="发起一次聊天后，这里会出现思考与工具执行记录"
      :image-size="76"
    />

    <div v-else class="tool-event-list">
      <article
        v-for="event in toolEvents"
        :key="event.id"
        :class="['tool-event-card', event.type]"
      >
        <div class="tool-event-title">
          <span>{{ event.typeLabel }}</span>
          <span>{{ event.time }}</span>
        </div>
        <div v-if="event.toolName" class="tool-event-tool">{{ event.toolName }}</div>
        <pre class="tool-event-content">{{ event.content }}</pre>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  toolEvents: Array<{
    id: string
    type: string
    typeLabel: string
    toolName?: string
    content: string
    time: string
  }>
}>()
</script>

<style scoped>
.tool-panel {
  width: 360px;
  border-left: 1px solid var(--border-color);
  background: rgba(248, 250, 252, 0.92);
  display: flex;
  flex-direction: column;
}

.tool-panel-header {
  padding: 20px 18px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.tool-kicker {
  color: #0f766e;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.tool-panel h3 {
  color: #0f172a;
  font-size: 18px;
}

.tool-event-list {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-event-card {
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: #fff;
  padding: 14px;
}

.tool-event-card.thinking {
  border-left: 4px solid #0f766e;
}

.tool-event-card.tool_result {
  border-left: 4px solid #2563eb;
}

.tool-event-card.retry {
  border-left: 4px solid #ea580c;
}

.tool-event-title {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
  margin-bottom: 8px;
}

.tool-event-tool {
  color: #0f172a;
  font-weight: 600;
  margin-bottom: 8px;
}

.tool-event-content {
  white-space: pre-wrap;
  word-break: break-word;
  background: #f8fafc;
  border-radius: 12px;
  padding: 10px 12px;
  color: #334155;
  font-size: 13px;
  line-height: 1.6;
}
</style>
