<template>
  <aside class="wiki-sidebar">
    <div class="sidebar-search" @click="$emit('open-search')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9b9b9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <span>搜索...</span>
      <kbd>Ctrl+K</kbd>
    </div>

    <div class="page-tree">
      <div class="tree-label">Wiki 页面</div>
      <div v-if="loading" class="tree-loading">加载中...</div>
      <template v-else>
        <div v-for="page in pages" :key="page.path">
          <div
            :class="['tree-item', { active: isActive(page.path) }]"
            @click="navigate(page.path)"
          >
            <span class="tree-arrow" v-if="page.children?.length" @click.stop="toggle(page.path)">
              {{ expanded[page.path] ? '▾' : '▸' }}
            </span>
            <span v-else class="tree-arrow-placeholder"></span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            <span class="tree-title">{{ page.title }}</span>
          </div>
          <div v-if="page.children?.length && expanded[page.path]" class="tree-children">
            <div
              v-for="child in page.children"
              :key="child.path"
              :class="['tree-item', 'tree-child', { active: isActive(child.path) }]"
              @click="navigate(child.path)"
            >
              <span class="tree-arrow-placeholder"></span>
              <span class="tree-arrow-placeholder"></span>
              <span class="tree-title">{{ child.title }}</span>
            </div>
          </div>
        </div>
        <div v-if="!loading && pages.length === 0" class="tree-empty">暂无文档</div>
      </template>
    </div>

    <div class="sidebar-tools">
      <div class="tree-label">工具</div>
      <router-link to="/ingest" class="tool-item" :class="{ active: isToolRoute('/ingest') }">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        录入文档
      </router-link>
      <router-link to="/lint" class="tool-item" :class="{ active: isToolRoute('/lint') }">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
        </svg>
        健康检查
      </router-link>
      <router-link to="/archive" class="tool-item" :class="{ active: isToolRoute('/archive') }">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/>
        </svg>
        归档管理
      </router-link>
    </div>

    <div class="sidebar-footer">
      <span class="version">v1.0.0</span>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'

const router = useRouter()
const route = useRoute()
const pages = ref([])
const loading = ref(true)
const expanded = ref({})

defineEmits(['open-search'])

function isActive(path) {
  return route.params.path === path || route.params.path?.join?.('/') === path
}

function isToolRoute(path) {
  return route.path === path
}

function navigate(path) {
  router.push(`/wiki/${path}`)
}

function toggle(path) {
  expanded.value[path] = !expanded.value[path]
}

onMounted(async () => {
  try {
    const res = await api.get('/wiki/tree')
    pages.value = res.data.pages || []
    for (const p of pages.value) {
      if (p.children?.length) expanded.value[p.path] = true
    }
  } catch (_) { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.wiki-sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  user-select: none;
  font-size: var(--fs-sidebar);
}
.sidebar-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin: 8px;
  background: var(--bg-content);
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: var(--fs-sidebar);
}
.sidebar-search kbd {
  margin-left: auto;
  background: var(--bg-hover);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  color: var(--text-secondary);
}
.page-tree {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}
.tree-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  padding: 8px 8px 4px;
}
.tree-loading, .tree-empty {
  padding: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}
.tree-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-primary);
  transition: background 0.15s;
  font-size: 13px;
  min-height: 28px;
}
.tree-item:hover { background: var(--bg-hover); }
.tree-item.active { background: #e8e7e4; font-weight: 500; }
.tree-child { padding-left: 8px; }
.tree-arrow {
  width: 14px;
  font-size: 10px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.tree-arrow-placeholder { width: 14px; flex-shrink: 0; }
.tree-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sidebar-tools {
  border-top: 1px solid var(--border-light);
  padding: 8px;
}
.tool-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  color: var(--text-primary);
  text-decoration: none;
  font-size: 13px;
  transition: background 0.15s;
}
.tool-item:hover { background: var(--bg-hover); }
.tool-item.active { background: #e8e7e4; }
.sidebar-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--border-light);
}
.version { font-size: 11px; color: var(--text-secondary); }
</style>
