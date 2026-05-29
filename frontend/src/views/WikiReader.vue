<template>
  <div class="wiki-reader">
    <div v-if="loading" class="wiki-loading">加载中...</div>
    <div v-else-if="error" class="wiki-error">
      <h2>文档不存在</h2>
      <p>{{ error }}</p>
      <router-link to="/wiki">返回首页</router-link>
    </div>
    <template v-else>
      <nav class="breadcrumb">
        <router-link to="/wiki">Wiki</router-link>
        <template v-for="(part, i) in breadcrumbs" :key="i">
          <span class="sep">/</span>
          <router-link v-if="i < breadcrumbs.length - 1" :to="'/wiki/' + part.path">
            {{ part.title }}
          </router-link>
          <span v-else class="current">{{ part.title }}</span>
        </template>
      </nav>

      <article class="wiki-article">
        <header class="article-header">
          <h1>{{ doc.title }}</h1>
          <div class="article-meta">
            <span :class="['confidence-tag', doc.confidence]">
              {{ confidenceLabel(doc.confidence) }}
            </span>
            <span>{{ formatDate(doc.updated_at) }}</span>
            <span>{{ doc.stats.statements }} 条声明</span>
            <span>{{ doc.stats.references }} 个引用</span>
          </div>
        </header>
        <div class="article-body" v-html="renderedContent"></div>
      </article>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import api from '../api'

marked.setOptions({ breaks: true, gfm: true })

const route = useRoute()
const doc = ref(null)
const loading = ref(true)
const error = ref('')

const wikiPath = computed(() => {
  const p = route.params.path
  if (Array.isArray(p)) return p.join('/')
  return p || ''
})

const breadcrumbs = computed(() => {
  if (!wikiPath.value) return []
  const parts = wikiPath.value.split('/').filter(Boolean)
  return parts.map((p, i) => ({
    title: p.replace(/-/g, ' ').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    path: parts.slice(0, i + 1).join('/'),
  }))
})

const renderedContent = computed(() => {
  if (!doc.value?.content) return ''
  return marked(doc.value.content)
})

function confidenceLabel(c) {
  return { verified: '已验证', inferred: '推断', unverified: '未验证' }[c] || c
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

watch(wikiPath, fetchDoc, { immediate: true })

async function fetchDoc() {
  loading.value = true
  error.value = ''
  try {
    if (wikiPath.value) {
      const res = await api.get(`/wiki/${wikiPath.value}`)
      doc.value = res.data
    } else {
      // Home: redirect to first document
      const treeRes = await api.get('/wiki/tree')
      const pages = treeRes.data.pages || []
      if (pages.length > 0) {
        const first = pages[0].children?.[0] || pages[0]
        doc.value = (await api.get(`/wiki/${first.path}`)).data
      } else {
        doc.value = {
          title: '欢迎',
          content: '# 欢迎使用知识库\n\n知识库中暂无文档，请先录入资料。',
          confidence: 'unverified',
          updated_at: '',
          stats: { statements: 0, references: 0 },
        }
      }
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.wiki-reader {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 40px 48px 80px;
}
.wiki-loading, .wiki-error { text-align: center; padding: 80px 20px; color: var(--text-secondary); }
.wiki-error h2 { color: var(--text-primary); margin-bottom: 8px; }
.wiki-error a { color: var(--text-link); }
.breadcrumb {
  font-size: var(--fs-aux);
  color: var(--text-secondary);
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.breadcrumb a { color: var(--text-secondary); text-decoration: none; }
.breadcrumb a:hover { color: var(--text-primary); }
.breadcrumb .sep { color: var(--text-secondary); }
.breadcrumb .current { color: var(--text-primary); }
.article-header { margin-bottom: 28px; }
.article-header h1 {
  font-size: var(--fs-title);
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}
.article-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: var(--fs-aux);
  color: var(--text-secondary);
}
.confidence-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 500;
}
.confidence-tag.verified { background: var(--color-verified-bg); color: var(--color-verified-text); }
.confidence-tag.inferred { background: var(--color-inferred-bg); color: var(--color-inferred-text); }
.confidence-tag.unverified { background: var(--color-unverified-bg); color: var(--color-unverified-text); }
.article-body {
  font-size: var(--fs-body);
  line-height: 1.7;
  color: var(--text-primary);
}
.article-body :deep(h2) { font-size: var(--fs-h2); font-weight: 600; margin: 32px 0 12px; }
.article-body :deep(h3) { font-size: 18px; font-weight: 600; margin: 24px 0 8px; }
.article-body :deep(p) { margin: 0 0 12px; }
.article-body :deep(code) {
  background: var(--bg-code);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 13px;
}
.article-body :deep(pre) {
  background: var(--bg-code);
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}
.article-body :deep(pre code) { padding: 0; background: none; }
.article-body :deep(blockquote) {
  border-left: 3px solid var(--border-medium);
  padding-left: 16px;
  margin: 12px 0;
  color: var(--text-secondary);
}
</style>
