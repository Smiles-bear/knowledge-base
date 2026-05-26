<template>
  <aside class="conv-sidebar">
    <div class="conv-header">
      <el-button type="primary" size="small" @click="$emit('new-conversation')" :icon="Plus">
        新建对话
      </el-button>
    </div>
    <div class="conv-list">
      <div
        v-for="conv in conversations"
        :key="conv.id"
        :class="['conv-item', { active: conv.id === activeId }]"
        @click="$emit('select', conv.id)"
      >
        <div class="conv-title">{{ conv.title || '新对话' }}</div>
        <div class="conv-meta">{{ conv.message_count }} 条消息</div>
        <el-button
          class="conv-delete"
          :icon="Delete"
          circle
          size="small"
          text
          @click.stop="$emit('delete', conv.id)"
        />
      </div>
      <el-empty v-if="!conversations.length" description="暂无对话" :image-size="60" />
    </div>
  </aside>
</template>

<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'

defineProps({
  conversations: { type: Array, default: () => [] },
  activeId: { type: String, default: null },
})

defineEmits(['select', 'new-conversation', 'delete'])
</script>

<style scoped>
.conv-sidebar {
  width: 240px;
  min-width: 240px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}
.conv-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.conv-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
  margin-bottom: 2px;
}
.conv-item:hover {
  background: #f5f6f8;
}
.conv-item.active {
  background: rgba(99, 102, 241, 0.08);
}
.conv-title {
  font-size: 13px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 24px;
}
.conv-meta {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}
.conv-delete {
  position: absolute;
  top: 8px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}
.conv-item:hover .conv-delete {
  opacity: 1;
}
</style>
