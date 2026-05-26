import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export function postQuery(question) {
  return api.post('/query', { question })
}

export function postIngest(data) {
  return api.post('/ingest', data)
}

export function getHealth() {
  return api.get('/health')
}

export function postLint() {
  return api.post('/lint')
}

export function postArchive(data) {
  return api.post('/archive', data)
}

// Conversation endpoints
export function getConversations() {
  return api.get('/conversations')
}

export function createConversation(data) {
  return api.post('/conversations', data)
}

export function getConversation(id) {
  return api.get(`/conversations/${id}`)
}

export function deleteConversation(id) {
  return api.delete(`/conversations/${id}`)
}

// SSE streaming query
export function streamQuery(question, callbacks) {
  const controller = new AbortController()

  fetch('/api/v1/query/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }))
      callbacks.onError(err.detail || 'Stream failed')
      return
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            switch (event.type) {
              case 'token':
                callbacks.onToken(event.content)
                break
              case 'meta':
                callbacks.onMeta(event)
                break
              case 'done':
                callbacks.onDone()
                break
              case 'complete':
                if (callbacks.onToken) callbacks.onToken(event.data.answer)
                if (callbacks.onMeta) callbacks.onMeta(event.data)
                callbacks.onDone()
                break
              case 'error':
                callbacks.onError(event.message)
                break
            }
          } catch (_) { /* skip parse errors */ }
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      callbacks.onError(err.message)
    }
  })

  return controller
}

export default api
