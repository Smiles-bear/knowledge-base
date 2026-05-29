<template>
  <div class="app-layout">
    <AppSidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppSidebar from './components/AppSidebar.vue'
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app {
  height: 100%;
  font-family: var(--font-sans);
  color: var(--text-primary);
  background: var(--bg-content);
}
.app-layout {
  display: flex;
  height: 100%;
}
.main-content {
  flex: 1;
  background: var(--bg-content);
  overflow-y: auto;
  padding: 0;
}
</style>
