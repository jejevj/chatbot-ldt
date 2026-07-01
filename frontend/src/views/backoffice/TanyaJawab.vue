<template>
  <BackofficeLayout>
    <div class="space-y-4">
      <!-- Info banner kalau belum ada dokumen ready -->
      <div v-if="!hasReadyDoc && !loadingDocs" class="bo-glass-card p-4 flex items-start gap-3">
        <Info :size="16" class="text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <p class="text-sm text-bo-100 font-medium">Belum ada dokumen yang siap</p>
          <p class="text-xs text-bo-400 mt-0.5">Upload dokumen rujukan terlebih dahulu agar chatbot bisa menjawab pertanyaan.</p>
          <router-link :to="{ name: 'DokumenRujukan' }" class="text-xs text-bo-300 hover:text-white flex items-center gap-1 mt-1.5 w-fit">
            <ArrowRight :size="11" /> Ke halaman Dokumen Rujukan
          </router-link>
        </div>
      </div>

      <!-- Chat Card -->
      <div class="bo-glass-card overflow-hidden">
        <!-- Header -->
        <div class="px-5 py-3.5 border-b border-white/10 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MessagesSquare :size="15" class="text-bo-300" />
            <span class="text-bo-100 font-semibold text-sm">Tanya Jawab Seputar Kemhan</span>
          </div>
          <button @click="resetSession" class="flex items-center gap-1.5 text-xs text-bo-400 hover:text-white hover:bg-white/10 px-2.5 py-1.5 rounded-lg transition">
            <RotateCcw :size="12" /> Sesi Baru
          </button>
        </div>

        <!-- Messages -->
        <div ref="chatBoxRef" class="h-[26rem] overflow-y-auto p-4 space-y-4">
          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-bo-400 text-sm gap-2">
            <MessagesSquare :size="32" class="opacity-20" />
            <p>Ajukan pertanyaan seputar Kemhan</p>
            <p class="text-xs">Jawaban berdasarkan dokumen rujukan yang telah diupload</p>
          </div>

          <template v-for="(msg, idx) in messages" :key="idx">
            <!-- User -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="max-w-lg bg-bo-800/60 border border-bo-700/40 rounded-2xl rounded-tr-sm px-4 py-2.5">
                <p class="text-sm text-bo-100">{{ msg.content }}</p>
              </div>
            </div>

            <!-- AI -->
            <div v-else class="flex items-start gap-2.5">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-bo-600 to-bo-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot :size="13" class="text-white" />
              </div>
              <div class="flex-1 max-w-lg">
                <div class="bo-glass rounded-2xl rounded-tl-sm px-4 py-2.5">
                  <p class="text-sm text-bo-100 whitespace-pre-wrap">{{ msg.content }}</p>
                </div>
                <!-- Sources -->
                <div v-if="msg.sources?.length" class="mt-1.5 flex flex-wrap gap-1.5">
                  <span v-for="src in msg.sources" :key="src.judul"
                    class="text-xs bg-bo-800/40 border border-bo-700/30 text-bo-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <BookMarked :size="10" /> {{ src.judul }}
                  </span>
                </div>
              </div>
            </div>
          </template>

          <!-- Typing -->
          <div v-if="aiTyping" class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-bo-600 to-bo-800 flex items-center justify-center">
              <Bot :size="13" class="text-white" />
            </div>
            <div class="bo-glass rounded-2xl px-4 py-2.5 flex gap-1">
              <span class="w-1.5 h-1.5 bg-bo-300 rounded-full animate-bounce" style="animation-delay:0ms"></span>
              <span class="w-1.5 h-1.5 bg-bo-300 rounded-full animate-bounce" style="animation-delay:150ms"></span>
              <span class="w-1.5 h-1.5 bg-bo-300 rounded-full animate-bounce" style="animation-delay:300ms"></span>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="border-t border-white/10 p-3 flex gap-2">
          <input
            v-model="inputMsg"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="Tanyakan sesuatu tentang Kemhan..."
            :disabled="aiTyping"
            class="bo-input flex-1 px-4 py-2.5 text-sm"
          />
          <button @click="sendMessage" :disabled="!inputMsg.trim() || aiTyping"
            class="bo-btn-primary px-4 py-2.5 rounded-xl disabled:opacity-40">
            <SendHorizontal :size="16" />
          </button>
        </div>
      </div>
    </div>
  </BackofficeLayout>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { MessagesSquare, Bot, SendHorizontal, RotateCcw, Info, ArrowRight, BookMarked } from 'lucide-vue-next'
import BackofficeLayout from '../../components/backoffice/BackofficeLayout.vue'
import { chatApi, docApi } from '../../services/backofficeApi'

const messages   = ref([])
const inputMsg   = ref('')
const aiTyping   = ref(false)
const chatBoxRef = ref(null)
const sessionId  = ref(`admin-${Date.now()}`)
const docs       = ref([])
const loadingDocs = ref(true)

const hasReadyDoc = computed(() => docs.value.some(d => d.status === 'ready'))

function resetSession() {
  sessionId.value = `admin-${Date.now()}`
  messages.value  = []
}

async function sendMessage() {
  const text = inputMsg.value.trim()
  if (!text || aiTyping.value) return

  messages.value.push({ role: 'user', content: text })
  inputMsg.value = ''
  aiTyping.value = true
  scrollBottom()

  try {
    const res = await chatApi.send(text, sessionId.value)
    messages.value.push({ role: 'assistant', content: res.answer, sources: res.sources })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `Terjadi kesalahan: ${e.message}` })
  } finally {
    aiTyping.value = false
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => { if (chatBoxRef.value) chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight })
}

onMounted(async () => {
  try { docs.value = await docApi.list() } catch(e) { console.error(e) }
  finally { loadingDocs.value = false }
})
</script>
