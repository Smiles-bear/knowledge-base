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

export default api
