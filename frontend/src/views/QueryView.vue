<template>
  <div class="query-page">
    <div class="chat-container">
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon">?</div>
        <h2>知识库问答</h2>
        <p class="welcome-hint">
          向企业知识库提问，系统会根据问题类型自动选择最优检索策略
        </p>
        <div class="example-questions">
          <el-tag
            v-for="q in exampleQuestions"
            :key="q"
            class="example-tag"
            @click="sendMessage(q)"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>
      <div class="chat-messages" ref="chatRef">
        <ChatBubble
          v-for="(msg, i) in messages"
          :key="i"
          :text="msg.text"
          :role="msg.role"
          :meta="msg.meta"
        />
        <div v-if="loading" class="loading-row">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span>思考中...</span>
        </div>
      </div>
    </div>
    <div class="chat-input-bar">
      <el-input
        v-model="input"
        placeholder="输入问题，按 Enter 发送"
        @keyup.enter="sendMessage(input)"
        :disabled="loading"
        size="large"
        clearable
      >
        <template #suffix>
          <el-button
            class="send-btn"
            :icon="Promotion"
            circle
            @click="sendMessage(input)"
            :disabled="loading || !input.trim()"
          />
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Promotion, Loading } from '@element-plus/icons-vue'
import { postQuery } from '../api'
import ChatBubble from '../components/ChatBubble.vue'
import { ElMessage } from 'element-plus'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const chatRef = ref(null)

const exampleQuestions = [
  '什么是 Transformer？',
  '知识库中有哪些内容？',
  '如何配置 MCP Server？',
]

async function sendMessage(text) {
  const q = (text || input.value).trim()
  if (!q || loading.value) return

  messages.value.push({ text: q, role: 'user' })
  input.value = ''
  loading.value = true
  await nextTick()
  scrollBottom()

  try {
    const res = await postQuery(q)
    const data = res.data
    messages.value.push({
      text: data.answer,
      role: 'assistant',
      meta: {
        route: data.route,
        token_estimate: data.token_estimate,
        sources: data.sources,
      },
    })
  } catch (e) {
    ElMessage.error('查询失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
    await nextTick()
    scrollBottom()
  }
}

function scrollBottom() {
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight
  }
}
</script>

<style scoped>
.query-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px);
  max-width: 800px;
  margin: 0 auto;
}
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}
.welcome {
  text-align: center;
  padding: 80px 20px 40px;
}
.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}
.welcome h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
  font-weight: 600;
}
.welcome-hint {
  color: #999;
  font-size: 14px;
  margin-bottom: 28px;
}
.example-questions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}
.example-tag {
  cursor: pointer;
  font-size: 13px;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}
.example-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}
.chat-messages {
  padding: 8px 0;
}
.loading-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 4px;
  color: #6366f1;
  font-size: 14px;
}
.chat-input-bar {
  padding: 16px 0 8px;
  background: #f5f6f8;
}
.send-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: #fff;
}
.send-btn:hover {
  opacity: 0.9;
  color: #fff;
}
.send-btn:disabled {
  background: #ccc;
}
</style>
