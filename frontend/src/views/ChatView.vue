<template>
  <div class="h-screen flex" :class="{ 'dark': isDark }">
    <!-- Sidebar -->
    <Sidebar
      :is-open="sidebarOpen"
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :is-loading="sessionsLoading"
      @close="sidebarOpen = false"
      @new-chat="handleNewChat"
      @select-session="handleSelectSession"
      @delete-session="handleDeleteSession"
      @delete-all-sessions="handleDeleteAllSessions"
      class="w-80"
    />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col transition-all duration-300" :class="{ 'lg:ml-80': sidebarOpen }">
      <!-- Header -->
      <header class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            :title="sidebarOpen ? 'Tutup sidebar' : 'Buka sidebar'"
          >
            ☰
          </button>
          <img 
            src="/favicon.png" 
            alt="Logo Kemhan"
            class="w-8 h-8 object-contain"
          />
          <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">
            {{ config.appName }}
          </h1>
        </div>
        
        <button
          @click="toggleDark()"
          class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
        >
          {{ isDark ? '☀️' : '🌙' }}
        </button>
      </header>

      <!-- Messages Area -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 pb-32">
        <!-- Welcome Screen -->
        <div v-if="!hasMessages" class="py-12 px-6">
          <!-- Info & Warning Boxes - Almost Full Width -->
          <div class="max-w-[96%] mx-auto mb-8 space-y-4">
            <!-- Info Box -->
            <Transition
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="opacity-0 transform scale-95 -translate-y-2"
              enter-to-class="opacity-100 transform scale-100 translate-y-0"
              leave-active-class="transition-all duration-300 ease-in"
              leave-from-class="opacity-100 transform scale-100 translate-y-0"
              leave-to-class="opacity-0 transform scale-95 -translate-y-2"
            >
              <div v-if="showInfoBox" class="p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl relative">
                <button
                  @click="showInfoBox = false"
                  class="absolute top-4 right-4 w-6 h-6 flex items-center justify-center rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors text-blue-600 dark:text-blue-400"
                  title="Tutup informasi"
                >
                  ✕
                </button>
                <div class="flex items-start gap-3 pr-8">
                  <div class="flex-shrink-0 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                    ℹ️
                  </div>
                  <div class="flex-1">
                    <h3 class="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                      Tentang Asisten Ini
                    </h3>
                    <p class="text-sm text-blue-800 dark:text-blue-200 leading-relaxed">
                      Asisten virtual ini dirancang untuk membantu Anda menelusuri dan memahami data terbuka dari 
                      Kementerian Pertahanan Republik Indonesia. Seluruh jawaban dibatasi hanya pada informasi yang 
                      bersumber dari data dan metadata resmi yang telah melalui proses verifikasi sesuai dengan prinsip 
                      Satu Data Indonesia.
                    </p>
                  </div>
                </div>
              </div>
            </Transition>

            <!-- Warning Box -->
            <Transition
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="opacity-0 transform scale-95 -translate-y-2"
              enter-to-class="opacity-100 transform scale-100 translate-y-0"
              leave-active-class="transition-all duration-300 ease-in"
              leave-from-class="opacity-100 transform scale-100 translate-y-0"
              leave-to-class="opacity-0 transform scale-95 -translate-y-2"
            >
              <div v-if="showWarningBox" class="p-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl relative">
                <button
                  @click="showWarningBox = false"
                  class="absolute top-4 right-4 w-6 h-6 flex items-center justify-center rounded-full hover:bg-amber-200 dark:hover:bg-amber-800 transition-colors text-amber-600 dark:text-amber-400"
                  title="Tutup informasi"
                >
                  ✕
                </button>
                <div class="flex items-start gap-3 pr-8">
                  <div class="flex-shrink-0 text-2xl">
                    ⚠️
                  </div>
                  <div class="flex-1">
                    <h3 class="font-semibold text-amber-900 dark:text-amber-100 mb-2">
                      Batasan Informasi
                    </h3>
                    <p class="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                      Untuk menjamin akurasi dan mencegah kesalahan informasi, jawaban yang diberikan dibatasi hanya pada 
                      data dan metadata yang telah terverifikasi serta dipublikasikan secara resmi. Asisten ini tidak memberikan 
                      tanggapan di luar ruang lingkup data resmi, tidak menyampaikan opini, interpretasi pribadi, maupun prediksi 
                      yang tidak bersumber dari dokumen atau data valid.
                    </p>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Welcome Header & Quick Questions - Centered -->
          <div class="max-w-5xl mx-auto text-center">
            <!-- Header -->
            <div class="mb-8">
              <div class="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg overflow-hidden">
                <img 
                  src="/ai-profile.png" 
                  alt="AI Assistant"
                  class="w-full h-full object-cover"
                />
              </div>
              <h2 class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                Selamat Datang!
              </h2>
              <p class="text-lg text-gray-600 dark:text-gray-400">
                Asisten Virtual Satu Data Pertahanan Kementerian Pertahanan RI
              </p>
            </div>
            
            <!-- Quick Questions -->
            <div v-if="quickQuestions.length > 0" class="space-y-3">
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
                💡 Pertanyaan yang sering ditanyakan:
              </p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  v-for="(question, index) in quickQuestions"
                  :key="index"
                  @click="sendMessage(question)"
                  class="group p-4 text-left bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 hover:from-blue-50 hover:to-blue-100 dark:hover:from-blue-900/20 dark:hover:to-blue-800/20 rounded-xl transition-all duration-200 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md"
                >
                  <div class="flex items-start gap-2">
                    <span class="text-blue-500 dark:text-blue-400 mt-0.5">→</span>
                    <p class="text-sm text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {{ question }}
                    </p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div v-else class="max-w-4xl mx-auto space-y-4">
          <ChatMessage
            v-for="(message, index) in messages"
            :key="index"
            :message="message"
            :is-last-user-message="isLastUserMessage(index)"
            @edit-message="handleEditMessage"
          />
          
          <!-- Loading Indicator -->
          <div v-if="isLoading" class="py-4 flex justify-start">
            <div class="flex items-start gap-4 max-w-4xl">
              <!-- AI Avatar -->
              <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md bg-gradient-to-br from-purple-500 to-indigo-600 overflow-hidden">
                <img 
                  src="/ai-profile.png" 
                  alt="AI Assistant"
                  class="w-full h-full object-cover"
                />
              </div>
              
              <!-- Loading Content -->
              <div class="flex-1 min-w-0">
                <div class="mb-1">
                  <span class="text-xs font-medium text-purple-600 dark:text-purple-400">
                    Asisten
                  </span>
                </div>
                <div class="rounded-2xl px-4 py-3 shadow-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 inline-block">
                  <div class="flex items-center gap-2">
                    <div class="flex gap-1">
                      <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                      <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                      <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    </div>
                    <span class="text-sm text-gray-600 dark:text-gray-400">Sedang menyiapkan jawaban...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="fixed bottom-0 right-0 left-0 transition-all duration-300" :class="{ 'lg:left-80': sidebarOpen }">
        <ChatInput
          :is-loading="isLoading"
          :disabled="!isRegistered"
          :edit-value="editingMessage"
          @submit="handleSendMessage"
          @cancel="cancelRequest"
          @cancel-edit="editingMessage = null"
        />
      </div>
    </div>

    <!-- Overlay for mobile sidebar -->
    <div
      v-if="sidebarOpen"
      @click="sidebarOpen = false"
      class="lg:hidden fixed inset-0 bg-black/50 z-10"
    ></div>

    <!-- Delete Confirmation Modal -->
    <ConfirmModal
      :show="showDeleteModal"
      :title="sessionToDelete === 'all' ? 'Hapus Semua Riwayat' : 'Hapus Riwayat Chat'"
      :message="sessionToDelete === 'all' ? 'Apakah Anda yakin ingin menghapus SEMUA riwayat chat? Tindakan ini tidak dapat dibatalkan.' : 'Apakah Anda yakin ingin menghapus riwayat chat ini? Tindakan ini tidak dapat dibatalkan.'"
      confirm-text="Hapus"
      cancel-text="Batal"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import ChatMessage from '../components/ChatMessage.vue'
import ChatInput from '../components/ChatInput.vue'
import Sidebar from '../components/Sidebar.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import { useChat } from '../composables/useChat'
import { useDevice } from '../composables/useDevice'
import { useSessions } from '../composables/useSessions'
import { chatApi } from '../services/api'
import config from '../config'

// Dark mode
const isDark = useDark()
const toggleDark = useToggle(isDark)

// UI State
const sidebarOpen = ref(window.innerWidth >= 1024) // Open by default on desktop
const messagesContainer = ref(null)
const quickQuestions = ref([])
const showInfoBox = ref(true)
const showWarningBox = ref(true)
const showDeleteModal = ref(false)
const sessionToDelete = ref(null)
const editingMessage = ref(null)

// Composables
const { deviceId, isRegistered } = useDevice()
const {
  messages,
  currentSessionId,
  isLoading,
  hasMessages,
  sendMessage: sendChatMessage,
  cancelRequest,
  clearChat,
  loadSession,
} = useChat()

const {
  sessions,
  isLoading: sessionsLoading,
  loadSessions,
  loadSessionMessages,
  deleteSession,
} = useSessions()

// Load quick questions
const loadQuickQuestions = async () => {
  try {
    const response = await chatApi.getQuickQuestions()
    quickQuestions.value = response.data
  } catch (err) {
    console.error('Failed to load quick questions:', err)
  }
}

// Send message
const sendMessage = async (text) => {
  await sendChatMessage(text)
  scrollToBottom()
  
  // Reload sessions to update sidebar
  await loadSessions()
}

// Handle new chat
const handleNewChat = () => {
  clearChat()
  // Only close sidebar on mobile
  if (window.innerWidth < 1024) {
    sidebarOpen.value = false
  }
  loadQuickQuestions()
}

// Handle select session
const handleSelectSession = async (sessionId) => {
  try {
    const sessionData = await loadSessionMessages(sessionId)
    loadSession(sessionData.messages)
    currentSessionId.value = sessionId
    // Only close sidebar on mobile
    if (window.innerWidth < 1024) {
      sidebarOpen.value = false
    }
    scrollToBottom()
  } catch (err) {
    console.error('Failed to load session:', err)
  }
}

// Handle delete session
const handleDeleteSession = async (sessionId) => {
  sessionToDelete.value = sessionId
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!sessionToDelete.value) return
  
  try {
    if (sessionToDelete.value === 'all') {
      // Delete all sessions
      for (const session of sessions.value) {
        await deleteSession(session.session_id)
      }
      handleNewChat()
    } else {
      // Delete single session
      await deleteSession(sessionToDelete.value)
      if (currentSessionId.value === sessionToDelete.value) {
        handleNewChat()
      }
    }
  } catch (err) {
    console.error('Failed to delete session:', err)
  } finally {
    showDeleteModal.value = false
    sessionToDelete.value = null
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
  sessionToDelete.value = null
}

// Handle delete all sessions
const handleDeleteAllSessions = () => {
  sessionToDelete.value = 'all'
  showDeleteModal.value = true
}

// Check if message is last user message
const isLastUserMessage = (index) => {
  // Find last user message index
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') {
      return i === index
    }
  }
  return false
}

// Handle edit message
const handleEditMessage = (message) => {
  editingMessage.value = message.content
}

// Handle send message (new or edited)
const handleSendMessage = async (text) => {
  if (editingMessage.value) {
    // Edit mode: delete messages after last user message
    await deleteMessagesAfterLastUser()
    editingMessage.value = null
  }
  
  await sendMessage(text)
}

// Delete messages after last user message
const deleteMessagesAfterLastUser = async () => {
  if (!currentSessionId.value) return
  
  try {
    // Call backend to delete from database
    await chatApi.deleteMessagesAfterLastUser(currentSessionId.value)
    
    // Find last user message index
    let lastUserIndex = -1
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') {
        lastUserIndex = i
        break
      }
    }
    
    if (lastUserIndex !== -1) {
      // Remove messages from UI
      messages.value.splice(lastUserIndex)
    }
  } catch (err) {
    console.error('Failed to delete messages:', err)
  }
}

// Scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Watch messages for auto-scroll
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// Initialize
onMounted(async () => {
  await loadSessions()
  await loadQuickQuestions()
  
  // Handle page unload
  window.addEventListener('beforeunload', () => {
    if (isLoading.value) {
      cancelRequest()
    }
  })
})
</script>
