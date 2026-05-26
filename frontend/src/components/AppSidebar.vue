<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1 class="logo">知识库</h1>
      <p class="subtitle">Enterprise Knowledge Base</p>
    </div>
    <nav class="nav-menu">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="nav-item--active"
      >
        <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <span class="version">v1.0.0</span>
    </div>
  </aside>
</template>

<script setup>
import { ChatDotRound, Upload, Monitor, Box } from '@element-plus/icons-vue'

const navItems = [
  { path: '/query', label: '问答', icon: ChatDotRound },
  { path: '/ingest', label: '录入', icon: Upload },
  { path: '/lint', label: '检查', icon: Monitor },
  { path: '/archive', label: '归档', icon: Box },
]
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  background: #1e1e2f;
  display: flex;
  flex-direction: column;
  color: #ccc;
  user-select: none;
}
.sidebar-header {
  padding: 28px 20px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.logo {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px 0;
  letter-spacing: 1px;
}
.subtitle {
  font-size: 11px;
  color: #777;
  margin: 0;
}
.nav-menu {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: #999;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #ddd;
}
.nav-item--active {
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
}
.nav-icon {
  font-size: 18px;
}
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.version {
  font-size: 12px;
  color: #555;
}
</style>
