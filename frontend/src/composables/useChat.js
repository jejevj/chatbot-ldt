/**
 * Chat composable - Chat logic and state management
 */
import { ref, computed } from 'vue'
import { chatApi } from '../services/api'

export function useChat() {
  const messages = ref([])
  const currentSessionId = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const abortController = ref(null)

  const hasMessages = computed(() => messages.value.length > 0)

  /**
   * Send a message
   */
  const sendMessage = async (text) => {
    if (!text.trim() || isLoading.value) return

    // Cancel previous request if any
    if (abortController.value) {
      abortController.value.abort()
    }

    // Add user message
    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(userMessage)

    // Create abort controller
    abortController.value = new AbortController()
    isLoading.value = true
    error.value = null

    try {
      const response = await chatApi.sendMessage(
        text,
        currentSessionId.value,
        abortController.value.signal
      )

      // Update session ID
      if (response.data.session_id) {
        currentSessionId.value = response.data.session_id
      }

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: response.data.jawaban,
        sources: response.data.sumber || [],
        timestamp: new Date().toISOString(),
      }
      messages.value.push(assistantMessage)
    } catch (err) {
      if (err.name === 'CanceledError') {
        // Request was cancelled
        messages.value.pop() // Remove user message
      } else {
        error.value = getErrorMessage(err)
        
        // Add error message
        messages.value.push({
          role: 'assistant',
          content: error.value,
          isError: true,
          timestamp: new Date().toISOString(),
        })
      }
    } finally {
      isLoading.value = false
      abortController.value = null
    }
  }

  /**
   * Cancel current request
   */
  const cancelRequest = () => {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
      isLoading.value = false
      
      // Remove last user message
      if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'user') {
        messages.value.pop()
      }
    }
  }

  /**
   * Clear chat
   */
  const clearChat = () => {
    messages.value = []
    currentSessionId.value = null
    error.value = null
  }

  /**
   * Load session messages
   */
  const loadSession = (sessionMessages) => {
    // Sort messages by created_at to ensure correct order
    const sortedMessages = [...sessionMessages].sort((a, b) => {
      const dateA = new Date(a.created_at)
      const dateB = new Date(b.created_at)
      return dateA - dateB
    })
    
    messages.value = sortedMessages.map(msg => ({
      role: msg.role,
      content: msg.content,
      sources: msg.sources || [],
      timestamp: msg.created_at,
    }))
  }

  /**
   * Get error message
   */
  const getErrorMessage = (err) => {
    if (err.response) {
      const status = err.response.status
      if (status === 401) {
        return 'Sesi Anda telah berakhir. Silakan refresh halaman.'
      } else if (status === 403) {
        return 'Anda tidak memiliki akses ke sesi ini.'
      } else if (status >= 500) {
        return 'Terjadi kesalahan pada server. Silakan coba lagi.'
      }
    } else if (err.request) {
      return 'Tidak dapat terhubung ke server. Periksa koneksi internet Anda.'
    }
    return 'Terjadi kesalahan yang tidak terduga. Silakan coba lagi.'
  }

  return {
    messages,
    currentSessionId,
    isLoading,
    error,
    hasMessages,
    sendMessage,
    cancelRequest,
    clearChat,
    loadSession,
  }
}
