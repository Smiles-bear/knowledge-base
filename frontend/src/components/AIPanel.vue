<template>
  <Teleport to="body">
    <div v-if="visible" class="ai-overlay" @click.self="close">
      <div class="ai-panel" :class="{ open: visible }">
        <div class="ai-panel-header">
          <h3>AI 问答</h3>
          <span class="ai-panel-context" v-if="contextDoc">{{ contextDoc }}</span>
          <button class="ai-panel-close" @click="close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <div class="ai-history-bar">
          <el-select v-model="activeConvId" placeholder="新对话" size="small" clearable style="width:100%"
            @change="switchConv" @clear="clearConv">
            <el-option v-for="c in conversations" :key="c.id" :label="c.title || '新对话'" :value="c.id" />
          </el-select>
          <el-button size="small" @click="newConv" :icon="Plus" circle />
        </div>

        <div class="ai-messages" ref="msgRef">
          <div v-if="messages.length === 0" class="ai-empty">
            <p>基于当前文档提问</p>
            <div class="ai-hints">
              <el-tag v-for="h in hints" :key="h" class="hint-tag" @click="sendMsg(h)">{{ h }}</el-tag>
            </div>
          </div>
          <ChatBubble v-for="(m, i) in messages" :key="i" :text="m.text" :role="m.role" :meta="m.meta" />
        </div>

        <div class="ai-input-bar">
          <el-input v-model="input" placeholder="输入问题，Enter 发送" @keyup.enter="sendMsg(input)"
            :disabled="loading" size="default" clearable>
            <template #suffix>
              <el-button v-if="!loading" @click="sendMsg(input)" :disabled="!input.trim()"
                style="background:var(--text-primary);border:none;color:#fff;" circle>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
              </el-button>
              <el-button v-else @click="stopStream" style="background:#ef4444;border:none;color:#fff;" circle>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { streamQuery, getConversations, createConversation, getConversation } from '../api'
import ChatBubble from './ChatBubble.vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: { type: Boolean, default: false },
  contextDoc: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const messages = ref([])
const input = ref('')
const loading = ref(false)
const msgRef = ref(null)
const conversations = ref([])
const activeConvId = ref(null)
let abortController = null

const hints = ['这篇文章的核心内容是什么？', '帮我总结要点', '有哪些关键概念？']

watch(() => props.visible, async (v) => {
  if (v) {
    await loadConvs()
    await nextTick()
    scrollBottom()
  }
})

async function loadConvs() {
  try { const res = await getConversations(); conversations.value = res.data } catch (_) {}
}

async function newConv() {
  try {
    const res = await createConversation({ title: '新对话' })
    conversations.value.unshift(res.data)
    activeConvId.value = res.data.id
    messages.value = []
  } catch (e) { ElMessage.error('创建对话失败') }
}

async function switchConv(id) {
  if (!id) return
  messages.value = []
  try {
    const res = await getConversation(id)
    messages.value = res.data.messages.map(m => ({
      text: m.content, role: m.role,
      meta: m.meta_json ? JSON.parse(m.meta_json) : null,
    }))
    scrollBottom()
  } catch (_) {}
}

function clearConv() { messages.value = []; activeConvId.value = null }

async function sendMsg(text) {
  const q = (text || input.value).trim()
  if (!q || loading.value) return
  if (!activeConvId.value) await newConv()
  if (abortController) { abortController.abort(); abortController = null }

  messages.value.push({ text: q, role: 'user' })
  input.value = ''
  loading.value = true
  await nextTick(); scrollBottom()

  const ai = messages.value.length
  messages.value.push({ text: '', role: 'assistant', meta: null })

  abortController = streamQuery(q, {
    onToken(t) { messages.value[ai].text += t; scrollBottom() },
    onMeta(m) { messages.value[ai].meta = { route: m.route, token_estimate: m.token_estimate, sources: m.sources } },
    onDone() { loading.value = false; abortController = null; scrollBottom(); loadConvs() },
    onError(e) { loading.value = false; abortController = null; messages.value[ai].text = 'Error: ' + e },
  })
}

function stopStream() {
  if (abortController) { abortController.abort(); abortController = null; loading.value = false }
}

function scrollBottom() {
  if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight
}

function close() { emit('close') }
</script>

<style scoped>
.ai-overlay {
  position: fixed; top: 0; right: 0; bottom: 0;
  z-index: 1000; display: flex;
}
.ai-panel {
  width: var(--ai-panel-width);
  height: 100%;
  background: var(--bg-content);
  border-left: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transform: translateX(100%); transition: transform 0.25s ease;
}
.ai-panel.open { transform: translateX(0); }
.ai-panel-header {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 20px; border-bottom: 1px solid var(--border-light);
}
.ai-panel-header h3 { font-size: 15px; font-weight: 600; margin: 0; color: var(--text-primary); }
.ai-panel-context { font-size: 11px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.ai-panel-close {
  background: none; border: none; cursor: pointer; padding: 4px;
  color: var(--text-secondary); border-radius: 4px;
}
.ai-panel-close:hover { background: var(--bg-hover); }
.ai-history-bar {
  display: flex; gap: 8px; padding: 10px 16px;
  border-bottom: 1px solid var(--border-light);
}
.ai-messages { flex: 1; overflow-y: auto; padding: 16px 20px; }
.ai-empty { text-align: center; padding: 40px 20px; color: var(--text-secondary); font-size: 13px; }
.ai-hints { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 12px; }
.hint-tag { cursor: pointer; }
.ai-input-bar { padding: 12px 16px; border-top: 1px solid var(--border-light); }
</style>
