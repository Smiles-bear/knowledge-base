<template>
  <div class="app-layout">
    <WikiSidebar @open-search="showSearch" />
    <main class="main-content" :class="{ 'with-panel': aiPanelVisible }">
      <router-view />
    </main>

    <!-- AI浮动按钮 -->
    <button v-if="!aiPanelVisible" class="ai-fab" @click="aiPanelVisible = true" title="AI 问答">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
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
  position: fixed; bottom: 24px; right: 24px; z-index: 999;
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--text-primary); color: #fff; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  transition: transform 0.2s;
}
.ai-fab:hover { transform: scale(1.08); }
</style>
