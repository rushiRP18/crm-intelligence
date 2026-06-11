import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor for error normalizing
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.message || err.message || 'Request failed'
    console.error(`[API Error] ${err.config?.url}: ${msg}`)
    return Promise.reject(err)
  }
)

export const emailsApi = {
  list: (params) => api.get('/emails', { params }),
  get: (id) => api.get(`/emails/${id}`),
  process: (id, dryRun = false) => api.post(`/emails/${id}/process?dry_run=${dryRun}`),
  ingestBatch: (data) => api.post('/emails/ingest/batch', data),
  ingest: (data) => api.post('/emails/ingest', data),
}

export const threadsApi = {
  list: (params) => api.get('/threads', { params }),
  get: (threadId) => api.get(`/threads/${threadId}`),
}

export const contactsApi = {
  list: (params) => api.get('/contacts', { params }),
  get: (email) => api.get(`/contacts/${encodeURIComponent(email)}`),
  updateStatus: (email, status) =>
    api.patch(`/contacts/${encodeURIComponent(email)}/status`, { status }),
}

export const draftsApi = {
  list: () => api.get('/drafts'),
  edit: (id, body) => api.patch(`/drafts/${id}`, { body }),
  approve: (id) => api.post(`/drafts/${id}/approve`),
}

export const analyticsApi = {
  summary: () => api.get('/analytics/summary'),
  sentimentTrend: (params) => api.get('/analytics/sentiment-trend', { params }),
  categoryBreakdown: (params) => api.get('/analytics/category-breakdown', { params }),
}

export const ragApi = {
  search: (q, k = 3) => api.get('/rag/search', { params: { q, k } }),
}

export const agentApi = {
  dryRun: (emailId) => api.post(`/agent/dry-run/${emailId}`),
  getAgentRun: (emailId) => api.get(`/agent/runs/${emailId}`),
}

export const intelligenceApi = {
  reputation: () => api.get('/intelligence/reputation'),
}

export const ticketsApi = {
  list: (params) => api.get('/tickets', { params }),
}

export default api
