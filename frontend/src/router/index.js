import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/query' },
  {
    path: '/query',
    name: 'Query',
    component: () => import('../views/QueryView.vue'),
  },
  {
    path: '/ingest',
    name: 'Ingest',
    component: () => import('../views/IngestView.vue'),
  },
  {
    path: '/lint',
    name: 'Lint',
    component: () => import('../views/LintView.vue'),
  },
  {
    path: '/archive',
    name: 'Archive',
    component: () => import('../views/ArchiveView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
