/**
 * API generasi infografis SVG dari dokumen
 */
import { authStore } from '../stores/auth'
import { config } from '../config'

const BASE = config.apiBaseUrl

function headers(extra = {}) {
  return { 'Authorization': `Bearer ${authStore.token}`, ...extra }
}

async function request(method, path, body = null, isFormData = false) {
  const opts = {
    method,
    headers: isFormData
      ? headers()
      : headers({ 'Content-Type': 'application/json' }),
  }
  if (body) opts.body = isFormData ? body : JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, opts)

  if (res.status === 401) {
    authStore.logout()
    window.location.href = '/chatbot/backoffice/login'
    return
  }

  const data = res.headers.get('content-type')?.includes('application/json')
    ? await res.json()
    : await res.text()

  if (!res.ok) throw new Error(data?.detail || data || `HTTP ${res.status}`)
  return data
}

export const infografisApi = {
  generate: (docId) => request('POST', `/v2/admin/infografis/generate`, { document_id: docId }),
}
