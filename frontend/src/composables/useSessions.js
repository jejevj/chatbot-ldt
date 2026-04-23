/**
 * Sessions composable - Session management
 */
import { ref } from 'vue'
import { sessionApi } from '../services/api'

export function useSessions() {
  const sessions = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  /**
   * Load sessions
   */
  const loadSessions = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await sessionApi.list()
      sessions.value = response.data
    } catch (err) {
      console.error('Failed to load sessions:', err)
      error.value = 'Gagal memuat riwayat chat.'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load session messages
   */
  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await sessionApi.get(sessionId)
      return response.data
    } catch (err) {
      console.error('Failed to load session messages:', err)
      throw new Error('Gagal memuat pesan.')
    }
  }

  /**
   * Delete session
   */
  const deleteSession = async (sessionId) => {
    try {
      await sessionApi.delete(sessionId)
      sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    } catch (err) {
      console.error('Failed to delete session:', err)
      throw new Error('Gagal menghapus sesi.')
    }
  }

  /**
   * Update session title
   */
  const updateSessionTitle = async (sessionId, title) => {
    try {
      await sessionApi.updateTitle(sessionId, title)
      const session = sessions.value.find(s => s.session_id === sessionId)
      if (session) {
        session.title = title
      }
    } catch (err) {
      console.error('Failed to update session title:', err)
      throw new Error('Gagal mengubah judul.')
    }
  }

  return {
    sessions,
    isLoading,
    error,
    loadSessions,
    loadSessionMessages,
    deleteSession,
    updateSessionTitle,
  }
}
