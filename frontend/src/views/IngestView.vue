<template>
  <div class="page">
    <div class="content-card">
      <h3>录入资料</h3>
      <p class="card-desc">提交原始资料到知识库，系统会自动编译为 Wiki 并逐条验证</p>

      <el-form :model="form" label-position="top" class="ingest-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="主题">
              <el-input v-model="form.topic" placeholder="例如: python, agent, mcp" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="标题">
              <el-input v-model="form.title" placeholder="资料标题" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="10"
            placeholder="粘贴或输入资料内容..."
          />
        </el-form-item>
        <el-form-item label="来源 URL（可选）">
          <el-input v-model="form.source_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item>
          <el-button @click="submit" :loading="loading">
            提交录入
          </el-button>
          <el-button @click="resetForm">清空</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="result" class="content-card result-card">
      <h3>录入结果</h3>
      <el-descriptions :column="2" border size="large">
        <el-descriptions-item label="状态">
          <el-tag :type="result.status === 'completed' ? 'success' : 'warning'">
            {{ result.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Wiki 路径">{{ result.wiki_path }}</el-descriptions-item>
        <el-descriptions-item label="置信度">{{ result.confidence }}</el-descriptions-item>
        <el-descriptions-item label="已验证">{{ result.verified_claims }} 条声明</el-descriptions-item>
        <el-descriptions-item label="已标记">{{ result.flagged_claims }} 条待确认</el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { postIngest } from '../api'
import { ElMessage } from 'element-plus'

const form = reactive({
  topic: '',
  title: '',
  content: '',
  source_url: '',
})
const loading = ref(false)
const result = ref(null)

async function submit() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  loading.value = true
  result.value = null
  try {
    const res = await postIngest({ ...form })
    result.value = res.data
    ElMessage.success('录入完成')
  } catch (e) {
    ElMessage.error('录入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.topic = ''
  form.title = ''
  form.content = ''
  form.source_url = ''
  result.value = null
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
.ingest-form { margin-top: 4px; }
.result-card { margin-top: 16px; }
</style>
