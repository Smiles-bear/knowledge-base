<template>
  <div class="page">
    <el-row :gutter="16" class="stat-row">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ health.wiki_articles }}</div>
          <div class="stat-label">Wiki 文章</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ health.raw_sources }}</div>
          <div class="stat-label">Raw 源文件</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">
            <el-tag :type="health.status === 'ok' ? 'success' : 'danger'" size="large">
              {{ health.status === 'ok' ? '正常' : '异常' }}
            </el-tag>
          </div>
          <div class="stat-label">服务状态</div>
        </div>
      </el-col>
    </el-row>

    <div class="content-card">
      <div class="card-header">
        <h3>Wiki 健康检查</h3>
        <el-button type="primary" @click="doLint" :loading="linting">
          <el-icon><Search /></el-icon> 运行检查
        </el-button>
      </div>

      <el-empty v-if="!lintResult && !linting" description="点击「运行检查」扫描 Wiki 健康状态" />

      <div v-if="lintResult">
        <p class="lint-summary">
          共 <strong>{{ lintResult.total_articles }}</strong> 篇文章，
          发现 <strong>{{ lintResult.issues?.length || 0 }}</strong> 个问题，
          自动修复 <strong>{{ lintResult.auto_fixed?.length || 0 }}</strong> 个
        </p>
        <el-table
          v-if="lintResult.issues?.length"
          :data="lintResult.issues"
          style="width: 100%"
          stripe
        >
          <el-table-column prop="type" label="类型" width="140" />
          <el-table-column prop="description" label="问题描述" min-width="200" />
          <el-table-column prop="file" label="文件" width="200" />
          <el-table-column label="修复状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.fixed ? 'success' : 'warning'" size="small">
                {{ row.fixed ? '已修复' : '待处理' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-result
          v-if="!lintResult.issues?.length"
          icon="success"
          title="未发现问题"
          sub-title="Wiki 状态良好，所有内容一致"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getHealth, postLint } from '../api'
import { ElMessage } from 'element-plus'

const health = ref({ status: 'loading', wiki_articles: '-', raw_sources: '-' })
const linting = ref(false)
const lintResult = ref(null)

onMounted(async () => {
  try {
    const res = await getHealth()
    health.value = res.data
  } catch {
    health.value = { status: 'error', wiki_articles: '-', raw_sources: '-' }
  }
})

async function doLint() {
  linting.value = true
  lintResult.value = null
  try {
    const res = await postLint()
    lintResult.value = res.data
    const h = await getHealth()
    health.value = h.data
  } catch (e) {
    ElMessage.error('检查失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    linting.value = false
  }
}
</script>

<style scoped>
.page { max-width: 900px; margin: 0 auto; }
.stat-row { margin-bottom: 16px; }
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
}
.stat-value { font-size: 30px; font-weight: 700; color: #6366f1; margin-bottom: 6px; }
.stat-label { font-size: 13px; color: #999; }
.content-card {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.card-header h3 { font-size: 18px; color: #333; margin: 0; font-weight: 600; }
.lint-summary { font-size: 14px; color: #666; margin-bottom: 16px; }
.lint-summary strong { color: #333; }
</style>
