/**
 * Backoffice API — wrapper fetch dengan Bearer JWT
 */
import { authStore } from '../stores/auth'
import { config } from '../config'

const BASE = config.apiBaseUrl  // https://apps.syscloud.my.id/chatbot-api

function headers(extra = {}) {
  return {
    'Authorization': `Bearer ${authStore.token}`,
    ...extra,
  }
}

async function request(method, path, body = null, isFormData = false) {
  const opts = {
    method,
    headers: isFormData
      ? headers()  // jangan set Content-Type, biar browser set boundary
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

// Documents
export const docApi = {
  list:   ()           => request('GET',    '/v2/admin/documents'),
  upload: (formData)   => request('POST',   '/v2/admin/documents', formData, true),
  delete: (id)         => request('DELETE', `/v2/admin/documents/${id}`),
}

// FAQ
export const faqApi = {
  list:   ()             => request('GET',    '/v2/admin/faq'),
  create: (payload)      => request('POST',   '/v2/admin/faq', payload),
  update: (id, payload)  => request('PUT',    `/v2/admin/faq/${id}`, payload),
  delete: (id)           => request('DELETE', `/v2/admin/faq/${id}`),
}

// Feedback
export const feedbackApi = {
  list:   ()   => request('GET',    '/v2/admin/feedback'),
  create: (p)  => request('POST',   '/v2/admin/feedback', p),
  apply:  (id) => request('POST',   `/v2/admin/feedback/${id}/apply`),
  delete: (id) => request('DELETE', `/v2/admin/feedback/${id}`),
}
