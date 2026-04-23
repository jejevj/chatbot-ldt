/**
 * API Service - Centralized API calls
 */
import axios from 'axios'
import config from '../config'

// Create axios instance
const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add device ID to headers
    const deviceId = localStorage.getItem('deviceId')
    if (deviceId) {
      config.headers['X-Device-ID'] = deviceId
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor with enhanced error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Create enhanced error object
    const enhancedError = {
      type: 'unknown',
      message: 'Terjadi kesalahan',
      originalError: error,
      statusCode: null,
      data: null,
    }

    if (error.response) {
      // Server responded with error status
      enhancedError.statusCode = error.response.status
      enhancedError.data = error.response.data

      switch (error.response.status) {
        case 400:
          enhancedError.type = 'validation'
          enhancedError.message = error.response.data?.detail || 'Data tidak valid'
          break
        case 401:
          enhancedError.type = 'unauthorized'
          enhancedError.message = 'Sesi Anda telah berakhir'
          break
        case 403:
          enhancedError.type = 'forbidden'
          enhancedError.message = 'Akses ditolak'
          break
        case 404:
          enhancedError.type = 'notfound'
          enhancedError.message = 'Data tidak ditemukan'
          break
        case 429:
          enhancedError.type = 'ratelimit'
          enhancedError.message = 'Terlalu banyak permintaan, coba lagi nanti'
          break
        case 500:
          enhancedError.type = 'server'
          enhancedError.message = 'Terjadi kesalahan pada server'
          break
        case 503:
          enhancedError.type = 'maintenance'
          enhancedError.message = 'Sistem sedang maintenance'
          break
        default:
          enhancedError.type = 'server'
          enhancedError.message = `Error ${error.response.status}: ${error.response.statusText}`
      }

      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // Request made but no response
      enhancedError.type = 'network'
      enhancedError.message = 'Tidak dapat terhubung ke server'
      console.error('Network Error:', error.message)
    } else {
      // Something else happened
      enhancedError.type = 'unknown'
      enhancedError.message = error.message || 'Terjadi kesalahan'
      console.error('Error:', error.message)
    }

    // Attach enhanced error to original error object
    error.enhanced = enhancedError
    
    return Promise.reject(error)
  }
)

/**
 * Device API
 */
export const deviceApi = {
  register: (fingerprint) => api.post('/device/register', { device_fingerprint: fingerprint }),
}

/**
 * Chat API
 */
export const chatApi = {
  sendMessage: (message, sessionId = null, signal = null) =>
    api.post('/chat/history', {
      pertanyaan: message,
      session_id: sessionId,
    }, { signal }),
  
  getQuickQuestions: () => api.get('/chat/quick-questions'),
  
  deleteMessagesAfterLastUser: (sessionId) => 
    api.delete(`/chat/messages/after-last-user/${sessionId}`),
}

/**
 * Session API
 */
export const sessionApi = {
  list: () => api.get('/chat/sessions'),
  
  get: (sessionId) => api.get(`/chat/sessions/${sessionId}`),
  
  delete: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
  
  updateTitle: (sessionId, title) =>
    api.put(`/chat/sessions/${sessionId}/title`, null, { params: { title } }),
}

/**
 * Health API
 */
export const healthApi = {
  check: () => api.get('/health'),
}

/**
 * Error handler helper
 */
export const handleApiError = (error, router = null) => {
  const enhanced = error.enhanced || {
    type: 'unknown',
    message: 'Terjadi kesalahan',
    statusCode: null,
  }

  // Navigate to error page for critical errors
  if (router && ['maintenance', 'server'].includes(enhanced.type)) {
    router.push({
      name: 'Error',
      params: { type: enhanced.statusCode === 503 ? 'maintenance' : '500' },
    })
  }

  return enhanced
}

export default api
