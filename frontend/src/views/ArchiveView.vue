<template>
  <div class="page">
    <div class="content-card">
      <h3>归档回答</h3>
      <p class="card-desc">将有价值的 Q&A 写回知识库 Wiki，供后续查询使用</p>

      <el-form :model="form" label-position="top" class="archive-form">
        <el-form-item label="问题">
          <el-input v-model="form.question" placeholder="用户提出的问题" />
        </el-form-item>
        <el-form-item label="回答">
          <el-input
            v-model="form.answer"
            type="textarea"
            :rows="8"
            placeholder="AI 给出的回答内容"
          />
        </el-form-item>
        <el-form-item label="归档主题">
          <el-input v-model="form.topic" placeholder="例如: agent-basics, python-tips" />
        </el-form-item>
        <el-form-item>
          <el-button @click="submit" :loading="loading">
            提交归档
          </el-button>
          <el-button @click="resetForm">清空</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="archiveResult" class="content-card">
      <el-result icon="success" title="归档成功">
        <template #sub-title>
          已归档至 {{ archiveResult.path }}
        </template>
        <template #extra>
          <el-button @click="clearResult">继续归档</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { postArchive } from '../api'
import { ElMessage } from 'element-plus'

const form = reactive({ question: '', answer: '', topic: '' })
const loading = ref(false)
const archiveResult = ref(null)

async function submit() {
  if (!form.question.trim() || !form.answer.trim()) {
    ElMessage.warning('问题和回答不能为空')
    return
  }
  loading.value = true
  archiveResult.value = null
  try {
    const res = await postArchive({ ...form })
    archiveResult.value = res.data
    ElMessage.success('归档成功')
  } catch (e) {
    ElMessage.error('归档失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.question = ''
  form.answer = ''
  form.topic = ''
  archiveResult.value = null
}

function clearResult() {
  archiveResult.value = null
  form.question = ''
  form.answer = ''
  form.topic = ''
}
</script>

<style scoped>
.page { max-width: 800px; margin: 40px auto; padding: 0 48px; }
.content-card {
  background: var(--bg-content);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 32px;
  margin-bottom: 16px;
}
.content-card h3 { font-size: 18px; color: var(--text-primary); margin: 0 0 8px 0; font-weight: 600; }
.card-desc { color: var(--text-secondary); font-size: 13px; margin-bottom: 20px; }
.archive-form { margin-top: 4px; }
</style>
