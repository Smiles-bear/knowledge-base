<template>
  <div class="query-layout">
    <ConversationList
      :conversations="conversations"
      :activeId="activeConvId"
      @select="selectConversation"
      @new-conversation="newConversation"
      @delete="removeConversation"
    />
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
              v-if="!loading"
              class="send-btn"
              :icon="Promotion"
              circle
              @click="sendMessage(input)"
              :disabled="!input.trim()"
            />
            <el-button
              v-else
              class="stop-btn"
              :icon="Close"
              circle
              @click="stopStreaming"
            />
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { Promotion, Close } from '@element-plus/icons-vue'
import { streamQuery, getConversations, createConversation, getConversation, deleteConversation } from '../api'
import ChatBubble from '../components/ChatBubble.vue'
import ConversationList from '../components/ConversationList.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const chatRef = ref(null)
const conversations = ref([])
const activeConvId = ref(null)
let abortController = null

const exampleQuestions = [
  '什么是 Transformer？',
  '知识库中有哪些内容？',
  '如何配置 MCP Server？',
]

onMounted(async () => {
  await loadConversations()
})

async function loadConversations() {
  try {
    const res = await getConversations()
    conversations.value = res.data
  } catch (_) { /* ignore */ }
}

async function newConversation() {
  try {
    const res = await createConversation({ title: '新对话' })
    conversations.value.unshift(res.data)
    activeConvId.value = res.data.id
    messages.value = []
  } catch (e) {
    ElMessage.error('创建对话失败')
  }
}

async function selectConversation(id) {
  activeConvId.value = id
  messages.value = []
  try {
    const res = await getConversation(id)
    messages.value = res.data.messages.map(m => ({
      text: m.content,
      role: m.role,
      meta: m.meta_json ? JSON.parse(m.meta_json) : null,
    }))
    scrollBottom()
  } catch (_) { /* ignore */ }
}

async function removeConversation(id) {
  try {
    await ElMessageBox.confirm('确定删除该对话？', '确认', { type: 'warning' })
    await deleteConversation(id)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeConvId.value === id) {
      activeConvId.value = null
      messages.value = []
    }
  } catch (_) { /* cancelled */ }
}

async function sendMessage(text) {
  const q = (text || input.value).trim()
  if (!q || loading.value) return

  if (!activeConvId.value) {
    await newConversation()
  }

  if (abortController) {
    abortController.abort()
    abortController = null
  }

  messages.value.push({ text: q, role: 'user' })
  input.value = ''
  loading.value = true
  await nextTick()
  scrollBottom()

  const assistantIndex = messages.value.length
  messages.value.push({ text: '', role: 'assistant', meta: null })

  abortController = streamQuery(q, {
    onToken(token) {
      messages.value[assistantIndex].text += token
      scrollBottom()
    },
    onMeta(meta) {
      messages.value[assistantIndex].meta = {
        route: meta.route,
        token_estimate: meta.token_estimate,
        sources: meta.sources,
      }
    },
    onDone() {
      loading.value = false
      abortController = null
      scrollBottom()
      loadConversations() // refresh titles
    },
    onError(err) {
      loading.value = false
      abortController = null
      messages.value[assistantIndex].text = '查询失败: ' + err
      ElMessage.error('查询失败: ' + err)
      scrollBottom()
    },
  })
}

function stopStreaming() {
  if (abortController) {
    abortController.abort()
    abortController = null
    loading.value = false
  }
}

function scrollBottom() {
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight
  }
}
</script>

<style scoped>
.query-layout {
  display: flex;
  height: calc(100vh - 56px);
  margin: -28px;
}
.query-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 750px;
  margin: 0 auto;
  padding: 28px 28px 0;
}
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}
.welcome {
  text-align: center;
  padding: 60px 20px 30px;
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
.stop-btn {
  background: #ef4444;
  border: none;
  color: #fff;
}
.stop-btn:hover {
  opacity: 0.9;
  color: #fff;
}
</style>
