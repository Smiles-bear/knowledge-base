<template>
  <div class="app-layout">
    <WikiSidebar @open-search="showSearch" />
    <main class="main-content" :class="{ 'with-panel': aiPanelVisible }">
      <router-view />
    </main>

    <!-- AI问答浮动按钮 -->
    <button v-if="!aiPanelVisible" class="ai-fab" @click="aiPanelVisible = true">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span>AI 问答</span>
    </button>

    <AIPanel
      :visible="aiPanelVisible"
      :context-doc="currentDocTitle"
      @close="aiPanelVisible = false"
    />

    <SearchPalette
      :visible="searchVisible"
      @close="searchVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import WikiSidebar from './components/WikiSidebar.vue'
import AIPanel from './components/AIPanel.vue'
import SearchPalette from './components/SearchPalette.vue'

const route = useRoute()
const aiPanelVisible = ref(false)
const searchVisible = ref(false)

const currentDocTitle = computed(() => {
  const p = route.params.path
  if (!p) return ''
  const path = Array.isArray(p) ? p.join('/') : p
  return path.split('/').pop()?.replace(/-/g, ' ').replace(/_/g, ' ') || ''
})

function showSearch() { searchVisible.value = true }

function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    searchVisible.value = true
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: var(--font-sans); color: var(--text-primary); background: var(--bg-content); }
.app-layout { display: flex; height: 100%; position: relative; }
.main-content { flex: 1; overflow-y: auto; background: var(--bg-content); }
.with-panel { margin-right: var(--ai-panel-width); transition: margin-right 0.25s ease; }
.ai-fab {
  position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); z-index: 999;
  height: 48px; padding: 0 28px; border-radius: 24px;
  background: var(--text-primary); color: #fff; border: none;
  display: flex; align-items: center; gap: 10px;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0,0,0,0.25), 0 0 0 4px rgba(55,53,47,0.08);
  transition: box-shadow 0.2s;
  font-size: 15px; font-weight: 600;
  letter-spacing: 0.5px;
  animation: ai-fab-pulse 2s ease-in-out 1;
}
.ai-fab:hover {
  box-shadow: 0 6px 28px rgba(0,0,0,0.35), 0 0 0 8px rgba(55,53,47,0.12);
}
@keyframes ai-fab-pulse {
  0% { box-shadow: 0 4px 20px rgba(0,0,0,0.25), 0 0 0 4px rgba(55,53,47,0.08); }
  50% { box-shadow: 0 4px 30px rgba(0,0,0,0.4), 0 0 0 16px rgba(55,53,47,0.15); }
  100% { box-shadow: 0 4px 20px rgba(0,0,0,0.25), 0 0 0 4px rgba(55,53,47,0.08); }
}
</style>
