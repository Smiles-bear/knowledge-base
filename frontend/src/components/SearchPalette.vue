<template>
  <Teleport to="body">
    <div v-if="visible" class="search-overlay" @click.self="close">
      <div class="search-palette">
        <div class="search-input-row">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9b9b9b" stroke-width="1.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input ref="inputRef" v-model="query" placeholder="搜索文档或输入问题..." @keydown="onKeydown" class="search-input" />
          <kbd>Esc</kbd>
        </div>

        <div class="search-results" v-if="query.trim()">
          <div v-if="searching" class="search-status">搜索中...</div>
          <template v-else>
            <div v-if="results.length" class="result-group">
              <div class="result-label">文档</div>
              <div v-for="r in results" :key="r.path" class="result-item" @click="openDoc(r.path)" :class="{ highlighted: highlighted === r.path }">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                <span class="result-title">{{ r.title }}</span>
                <span class="result-path">{{ r.path }}</span>
              </div>
            </div>
            <div class="result-group">
              <div class="result-label">操作</div>
              <div class="result-item" @click="openPage('/ingest')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                <span class="result-title">录入文档</span>
              </div>
              <div class="result-item" @click="openPage('/lint')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                <span class="result-title">健康检查</span>
              </div>
              <div class="result-item" @click="openPage('/archive')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" stroke-width="1.5"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>
                <span class="result-title">归档管理</span>
              </div>
            </div>
          </template>
        </div>

        <div class="search-footer">
          <span>↑↓ 导航</span><span>↵ 打开</span><span>Esc 关闭</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const props = defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['close'])
const router = useRouter()
const query = ref('')
const results = ref([])
const searching = ref(false)
const highlighted = ref('')
const inputRef = ref(null)
let debounce = null

watch(() => props.visible, async (v) => {
  if (v) {
    query.value = ''
    results.value = []
    await nextTick()
    inputRef.value?.focus()
  }
})

watch(query, (v) => {
  clearTimeout(debounce)
  if (!v.trim()) { results.value = []; return }
  debounce = setTimeout(async () => {
    searching.value = true
    try {
      const res = await api.get('/search', { params: { q: v } })
      results.value = res.data.results || []
      if (results.value.length) highlighted.value = results.value[0].path
    } catch (_) { results.value = [] }
    finally { searching.value = false }
  }, 200)
})

function onKeydown(e) {
  if (e.key === 'Escape') { close() }
  if (e.key === 'Enter') {
    if (highlighted.value) { openDoc(highlighted.value) }
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const idx = results.value.findIndex(r => r.path === highlighted.value)
    if (idx < results.value.length - 1) highlighted.value = results.value[idx + 1].path
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    const idx = results.value.findIndex(r => r.path === highlighted.value)
    if (idx > 0) highlighted.value = results.value[idx - 1].path
  }
}

function openDoc(path) { router.push(`/wiki/${path}`); close() }
function openPage(path) { router.push(path); close() }
function close() { emit('close') }
</script>

<style scoped>
.search-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.3); z-index: 2000;
  display: flex; justify-content: center; padding-top: 15vh;
}
.search-palette {
  width: 560px; max-height: 420px;
  background: var(--bg-content); border-radius: 12px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.15); border: 1px solid var(--border-light);
  display: flex; flex-direction: column; overflow: hidden;
}
.search-input-row {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 20px; border-bottom: 1px solid var(--border-light);
}
.search-input-row kbd {
  background: var(--bg-hover); padding: 2px 8px; border-radius: 4px;
  font-size: 10px; color: var(--text-secondary);
}
.search-input {
  flex: 1; border: none; outline: none; font-size: 15px;
  color: var(--text-primary); background: transparent;
}
.search-results { flex: 1; overflow-y: auto; padding: 8px; }
.search-status { padding: 16px; text-align: center; color: var(--text-secondary); font-size: 13px; }
.result-label {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-secondary); padding: 6px 12px;
}
.result-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 6px; cursor: pointer;
  font-size: 13px; color: var(--text-primary);
}
.result-item:hover, .result-item.highlighted { background: var(--bg-hover); }
.result-path { margin-left: auto; font-size: 11px; color: var(--text-secondary); }
.search-footer {
  display: flex; gap: 16px; padding: 8px 16px;
  border-top: 1px solid var(--border-light);
  font-size: 10px; color: var(--text-secondary);
}
</style>
