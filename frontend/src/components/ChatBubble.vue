<template>
  <div :class="['bubble', role]">
    <div class="bubble-content">{{ text }}</div>
    <div v-if="meta" class="bubble-meta">
      <el-tag v-if="meta.route" size="small" type="info" effect="plain">
        {{ routeLabel(meta.route) }}
      </el-tag>
      <span v-if="meta.token_estimate" class="token-info">
        ~{{ meta.token_estimate }} tokens
      </span>
    </div>
    <div v-if="meta?.sources?.length" class="bubble-sources">
      <span class="sources-label">参考来源：</span>
      <span v-for="(s, i) in meta.sources" :key="i" class="source-item">{{ s }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, required: true },
  role: { type: String, default: 'user' },
  meta: { type: Object, default: null },
})

function routeLabel(route) {
  const map = {
    wiki_direct: 'Wiki 直读',
    wiki_with_links: 'Wiki 关联',
    rag_search: 'RAG 检索',
    simple_chat: '简单对话',
  }
  return map[route] || route
}
</script>

<style scoped>
.bubble {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}
.bubble.user {
  align-items: flex-end;
}
.bubble.user .bubble-content {
  background: var(--text-primary);
  color: #fff;
  border-radius: 12px 12px 4px 12px;
  max-width: 75%;
}
.bubble.assistant {
  align-items: flex-start;
}
.bubble.assistant .bubble-content {
  background: var(--bg-code);
  border: none;
  color: var(--text-primary);
  border-radius: 12px 12px 12px 4px;
  max-width: 85%;
}
.bubble-content {
  padding: 14px 18px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble-meta {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}
.token-info {
  color: #aaa;
  font-size: 12px;
}
.bubble-sources {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.sources-label {
  font-size: 12px;
  color: #999;
}
.source-item {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 2px 8px;
  border-radius: 4px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
