import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/wiki' },
  {
    path: '/wiki/:path(.*)*',
    name: 'Wiki',
    component: () => import('../views/WikiReader.vue'),
  },
  {
    path: '/ingest',
    name: 'Ingest',
    component: () => import('../views/IngestView.vue'),
    meta: { tool: true },
  },
  {
    path: '/lint',
    name: 'Lint',
    component: () => import('../views/LintView.vue'),
    meta: { tool: true },
  },
  {
    path: '/archive',
    name: 'Archive',
    component: () => import('../views/ArchiveView.vue'),
    meta: { tool: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
