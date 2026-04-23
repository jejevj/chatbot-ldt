<template>
  <div class="min-h-screen bg-background flex">
    <!-- Sidebar - Chat History -->
    <aside
      class="w-80 border-r border-border bg-card flex flex-col transition-all duration-300 fixed left-0 top-0 bottom-0 z-10"
      :class="{ '-ml-80': !showSidebar }"
    >
      <!-- Sidebar Header -->
      <div class="p-4 border-b border-border">
        <button
          @click="createNewChat"
          class="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
        >
          <Plus class="w-5 h-5" />
          <span>Chat Baru</span>
        </button>
      </div>

      <!-- Sessions List -->
      <div class="flex-1 overflow-y-auto p-2">
        <div v-if="sessions.length === 0" class="text-center text-muted-foreground py-8 text-sm">
          Belum ada riwayat chat
        </div>
        <div v-else class="space-y-1">
          <button
            v-for="session in sessions"
            :key="session.session_id"
            @click="loadSession(session.session_id)"
            class="w-full text-left p-3 rounded-lg hover:bg-secondary transition-colors group relative"
            :class="{ 'bg-secondary': currentSessionId === session.session_id }"
          >
            <div class="flex items-start gap-2">
              <MessageSquare class="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div class="flex-1 min-w-0">
                <p class="text-sm truncate">{{ session.title }}</p>
                <p class="text-xs text-muted-foreground">
                  {{ formatDate(session.updated_at) }}
                </p>
              </div>
              <button
                @click.stop="deleteSession(session.session_id)"
                class="opacity-0 group-hover:opacity-100 p-1 hover:bg-destructive/10 rounded transition-opacity"
              >
                <Trash2 class="w-4 h-4 text-destructive" />
              </button>
            </div>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col fixed top-0 bottom-0 transition-all duration-300" :style="{ left: showSidebar ? '320px' : '0', right: '0' }">
      <!-- Header -->
      <header class="border-b border-border bg-card">
        <div class="px-4 py-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <button
              @click="showSidebar = !showSidebar"
              class="p-2 rounded-lg hover:bg-secondary transition-colors"
            >
              <Menu class="w-5 h-5" />
            </button>
            <div class="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <MessageSquare class="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 class="text-xl font-bold">RAG Chatbot</h1>
              <p class="text-sm text-muted-foreground">Data Terbuka Indonesia</p>
            </div>
          </div>
          
          <button
            @click="toggleDarkMode"
            class="p-2 rounded-lg hover:bg-secondary transition-colors"
          >
            <Sun v-if="isDark" class="w-5 h-5" />
            <Moon v-else class="w-5 h-5" />
          </button>
        </div>
      </header>

      <!-- Messages Area -->
      <main class="flex-1 overflow-y-auto px-4 py-6 pb-32">
        <div class="max-w-4xl mx-auto">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="text-center py-12">
            <div class="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles class="w-10 h-10 text-primary" />
            </div>
            <h2 class="text-2xl font-bold mb-2">Selamat Datang!</h2>
            <p class="text-muted-foreground mb-6">
              Tanyakan tentang data terbuka yang Anda butuhkan
            </p>
            
            <!-- Quick Questions -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              <button
                v-for="(q, i) in quickQuestions"
                :key="i"
                @click="sendMessage(q)"
                class="p-4 text-left border border-border rounded-lg hover:bg-secondary transition-colors"
              >
                <div class="flex items-start gap-2">
                  <HelpCircle class="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                  <span class="text-sm">{{ q }}</span>
                </div>
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-else class="space-y-6 mb-6">
            <div
              v-for="(msg, i) in messages"
              :key="i"
              class="flex gap-3"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <!-- Avatar -->
              <div
                v-if="msg.role === 'assistant'"
                class="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0"
              >
                <Bot class="w-5 h-5 text-primary-foreground" />
              </div>

              <!-- Message Content -->
              <div
                class="max-w-[80%] rounded-lg p-4"
                :class="
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card border border-border'
                "
              >
                <div v-if="msg.role === 'user'" class="text-sm">
                  {{ msg.content }}
                </div>
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                
                <!-- Sources -->
                <div v-if="msg.sources && msg.sources.length > 0" class="mt-4 pt-4 border-t border-border">
                  <p class="text-sm font-semibold mb-2 flex items-center gap-2">
                    <FileText class="w-4 h-4" />
                    Sumber Data:
                  </p>
                  <div class="space-y-2">
                    <a
                      v-for="(source, j) in msg.sources"
                      :key="j"
                      :href="source.url"
                      target="_blank"
                      class="block p-2 rounded bg-secondary hover:bg-secondary/80 transition-colors text-sm"
                    >
                      <div class="flex items-start gap-2">
                        <ExternalLink class="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <div class="flex-1 min-w-0">
                          <p class="font-medium truncate">{{ source.judul }}</p>
                          <p class="text-xs text-muted-foreground">
                            {{ source.kategori }} • {{ source.tipe }}
                          </p>
                        </div>
                      </div>
                    </a>
                  </div>
                </div>
              </div>

              <!-- User Avatar -->
              <div
                v-if="msg.role === 'user'"
                class="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0"
              >
                <User class="w-5 h-5" />
              </div>
            </div>

            <!-- Loading -->
            <div v-if="isLoading" class="flex gap-3">
              <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                <Bot class="w-5 h-5 text-primary-foreground" />
              </div>
              <div class="bg-card border border-border rounded-lg p-4">
                <div class="flex items-center gap-3">
                  <div class="flex gap-1">
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  </div>
                  <button
                    @click="cancelRequest"
                    class="text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Batalkan
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- Input Area -->
      <div class="fixed bottom-0 border-t border-border bg-background z-20" :style="{ left: showSidebar ? '320px' : '0', right: '0' }">
        <div class="px-4 py-4 max-w-4xl mx-auto">
          <form @submit.prevent="handleSubmit" class="flex gap-2">
            <input
              v-model="inputMessage"
              type="text"
              placeholder="Tanyakan tentang data terbuka..."
              class="flex-1 px-4 py-3 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              :disabled="isLoading"
            />
            <button
              type="submit"
              :disabled="!inputMessage.trim() || isLoading"
              class="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send class="w-5 h-5" />
              <span class="hidden sm:inline">Kirim</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDark } from '@vueuse/core'
import { marked } from 'marked'
import hljs from 'highlight.js'
import axios from 'axios'
import { getDeviceId } from './utils/deviceFingerprint'
import {
  MessageSquare,
  Sun,
  Moon,
  Sparkles,
  HelpCircle,
  Bot,
  User,
  Send,
  FileText,
  ExternalLink,
  Menu,
  Plus,
  Trash2,
} from 'lucide-vue-next'

// Dark mode
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleDarkMode = () => {
  isDark.value = !isDark.value
}

// State
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const showSidebar = ref(true)
const sessions = ref([])
const currentSessionId = ref(null)
const deviceId = ref(null)
const quickQuestions = ref([
  'Data apa saja yang tersedia?',
  'Bagaimana cara mencari data?',
  'Kategori data apa yang ada?',
  'Apakah ada data terbaru?'
])
const abortController = ref(null) // For request cancellation

// Configure axios interceptor untuk menambahkan device ID header
axios.interceptors.request.use((config) => {
  if (deviceId.value) {
    config.headers['X-Device-ID'] = deviceId.value
  }
  return config
})

// Configure marked
marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true,
})

// Render markdown
const renderMarkdown = (text) => {
  return marked(text)
}

// Format date
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return 'Hari ini'
  if (days === 1) return 'Kemarin'
  if (days < 7) return `${days} hari lalu`
  return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}

// Load sessions
const loadSessions = async () => {
  try {
    const response = await axios.get('/api/chat/sessions')
    sessions.value = response.data
  } catch (error) {
    console.error('Error loading sessions:', error)
  }
}

// Load session messages
const loadSession = async (sessionId) => {
  try {
    const response = await axios.get(`/api/chat/sessions/${sessionId}`)
    currentSessionId.value = sessionId
    messages.value = response.data.messages
    
    // Scroll to bottom
    setTimeout(() => {
      window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth',
      })
    }, 100)
  } catch (error) {
    console.error('Error loading session:', error)
  }
}

// Create new chat
const createNewChat = () => {
  currentSessionId.value = null
  messages.value = []
  inputMessage.value = ''
}

// Delete session
const deleteSession = async (sessionId) => {
  if (!confirm('Hapus riwayat chat ini?')) return
  
  try {
    await axios.delete(`/api/chat/sessions/${sessionId}`)
    
    // Reload sessions
    await loadSessions()
    
    // Clear current chat if deleted
    if (currentSessionId.value === sessionId) {
      createNewChat()
    }
  } catch (error) {
    console.error('Error deleting session:', error)
  }
}

// Send message
const sendMessage = async (text) => {
  const message = text || inputMessage.value.trim()
  if (!message || isLoading.value) return

  // Cancel previous request if exists
  if (abortController.value) {
    abortController.value.abort()
  }

  // Create new abort controller
  abortController.value = new AbortController()

  // Add user message
  messages.value.push({
    role: 'user',
    content: message,
  })

  inputMessage.value = ''
  isLoading.value = true

  try {
    const response = await axios.post('/api/chat/history', {
      session_id: currentSessionId.value,
      pertanyaan: message,
    }, {
      signal: abortController.value.signal
    })

    // Update session ID
    if (!currentSessionId.value) {
      currentSessionId.value = response.data.session_id
      await loadSessions()
    }

    // Add assistant message
    messages.value.push({
      role: 'assistant',
      content: response.data.jawaban,
      sources: response.data.sumber,
    })

    // Scroll to bottom
    setTimeout(() => {
      window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth',
      })
    }, 100)
  } catch (error) {
    // Check if request was cancelled
    if (axios.isCancel(error) || error.name === 'CanceledError') {
      console.log('Request cancelled by user')
      // Remove the user message that was added
      messages.value.pop()
      return
    }
    
    console.error('Error:', error)
    
    // Friendly error message
    let errorMessage = 'Maaf, terjadi kesalahan saat memproses pertanyaan Anda.'
    
    if (error.response) {
      // Server responded with error
      if (error.response.status === 401) {
        errorMessage = 'Maaf, sesi Anda tidak valid. Silakan refresh halaman dan coba lagi.'
      } else if (error.response.status === 403) {
        errorMessage = 'Maaf, Anda tidak memiliki akses ke percakapan ini.'
      } else if (error.response.status >= 500) {
        errorMessage = 'Maaf, terjadi kesalahan pada server. Silakan coba beberapa saat lagi.'
      }
    } else if (error.request) {
      // No response from server
      errorMessage = 'Maaf, tidak dapat terhubung ke server. Silakan periksa koneksi internet Anda dan coba lagi.'
    }
    
    messages.value.push({
      role: 'assistant',
      content: errorMessage,
      sources: [],
    })
  } finally {
    isLoading.value = false
    abortController.value = null
  }
}

// Cancel current request
const cancelRequest = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
    isLoading.value = false
    
    // Remove last user message if loading
    if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'user') {
      messages.value.pop()
    }
  }
}

// Handle submit
const handleSubmit = () => {
  sendMessage()
}

// Load quick questions
const loadQuickQuestions = async () => {
  try {
    const response = await axios.get('/api/chat/quick-questions')
    if (response.data && response.data.length > 0) {
      quickQuestions.value = response.data
    }
  } catch (error) {
    console.error('Error loading quick questions:', error)
    // Keep default questions
  }
}

// Load on mount
onMounted(async () => {
  // Initialize device ID
  try {
    deviceId.value = await getDeviceId()
    console.log('Device ID:', deviceId.value)
    
    // Load sessions dan quick questions setelah device ID ready
    await Promise.all([
      loadSessions(),
      loadQuickQuestions()
    ])
  } catch (error) {
    console.error('Error initializing device:', error)
  }
  
  // Cancel request on page unload
  window.addEventListener('beforeunload', () => {
    if (abortController.value) {
      abortController.value.abort()
    }
  })
})
</script>
