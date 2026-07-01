<template>
  <div class="space-y-5">

    <!-- STEP 1: Pilih Dokumen & Mulai Sesi -->
    <div v-if="!activeSession" class="bo-glass-card p-6">
      <h3 class="text-bo-100 font-semibold text-sm mb-1 flex items-center gap-2">
        <BookOpen :size="15" /> Sesi Koreksi AI
      </h3>
      <p class="text-bo-400 text-xs mb-5">Pilih dokumen, lakukan tanya jawab, lalu koreksi jawaban AI yang salah sebagai bahan pelatihan.</p>

      <!-- Pilih Dokumen -->
      <div class="mb-4">
        <label class="block text-xs text-bo-300 mb-1.5">Pilih Dokumen Referensi</label>
        <div class="relative">
          <div class="relative">
            <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-bo-400" />
            <input
              v-model="docSearch"
              @focus="showDocDropdown = true"
              @blur="handleBlur"
              type="text"
              placeholder="Cari dokumen..."
              class="bo-input w-full pl-9 pr-4 py-2.5 text-sm"
            />
          </div>
          <div v-if="showDocDropdown && filteredDocs.length"
            class="absolute z-30 mt-1 w-full bo-glass-card overflow-hidden max-h-56 overflow-y-auto">
            <button
              v-for="doc in filteredDocs" :key="doc.id"
              @mousedown.prevent="selectDoc(doc)"
              class="w-full text-left px-4 py-2.5 text-sm text-bo-200 hover:bg-white/10 transition flex items-center justify-between gap-3"
            >
              <span class="truncate">{{ doc.judul }}</span>
              <StatusBadge :status="doc.status" />
            </button>
          </div>
          <div v-if="showDocDropdown && !filteredDocs.length && docSearch"
            class="absolute z-30 mt-1 w-full bo-glass-card px-4 py-3 text-sm text-bo-400">
            Dokumen tidak ditemukan
          </div>
        </div>

        <div v-if="selectedDoc" class="mt-2 flex items-center gap-2 bg-bo-800/40 border border-bo-700/40 rounded-lg px-3 py-2">
          <FileText :size="13" class="text-bo-300 flex-shrink-0" />
          <span class="text-sm text-bo-100 flex-1 truncate">{{ selectedDoc.judul }}</span>
          <button @click="selectedDoc = null" class="text-bo-400 hover:text-white transition">
            <X :size="13" />
          </button>
        </div>
      </div>

      <button
        @click="startSession"
        :disabled="!selectedDoc"
        class="bo-btn-primary px-5 py-2.5 rounded-xl text-sm font-medium flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <MessageSquarePlus :size="15" /> Mulai Sesi Chat
      </button>
    </div>

    <!-- STEP 2: Chat Session -->
    <div v-else class="space-y-4">
      <div class="bo-glass-card px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-bo-800/60 flex items-center justify-center">
            <FileText :size="14" class="text-bo-300" />
          </div>
          <div>
            <p class="text-xs text-bo-400">Dokumen aktif</p>
            <p class="text-sm font-medium text-bo-100">{{ selectedDoc.judul }}</p>
          </div>
        </div>
        <button @click="endSession"
          class="flex items-center gap-1.5 text-xs text-bo-400 hover:text-white hover:bg-white/10 px-3 py-1.5 rounded-lg transition">
          <X :size="13" /> Akhiri Sesi
        </button>
      </div>

      <div class="bo-glass-card overflow-hidden">
        <div ref="chatBoxRef" class="h-96 overflow-y-auto p-4 space-y-4">
          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-bo-400 text-sm gap-2">
            <MessageSquare :size="28" class="opacity-30" />
            <span>Mulai bertanya tentang dokumen ini</span>
          </div>

          <template v-for="(msg, idx) in messages" :key="idx">
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="max-w-lg bg-bo-800/60 border border-bo-700/40 rounded-2xl rounded-tr-sm px-4 py-2.5">
                <p class="text-sm text-bo-100">{{ msg.content }}</p>
              </div>
            </div>

            <div v-else class="flex flex-col gap-1.5">
              <div class="flex items-start gap-2.5">
                <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-bo-600 to-bo-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot :size="13" class="text-white" />
                </div>
                <div class="flex-1">
                  <div class="bo-glass max-w-lg rounded-2xl rounded-tl-sm px-4 py-2.5">
                    <p class="text-sm text-bo-100 whitespace-pre-wrap">{{ msg.content }}</p>
                  </div>
                  <div class="mt-1.5 ml-1">
                    <button
                      v-if="!msg.correcting && !msg.corrected"
                      @click="msg.correcting = true"
                      class="flex items-center gap-1.5 text-xs text-bo-400 hover:text-amber-300 transition"
                    >
                      <PenLine :size="12" /> Koreksi jawaban ini
                    </button>
                    <span v-if="msg.corrected" class="flex items-center gap-1 text-xs text-emerald-400">
                      <CheckCircle2 :size="12" /> Koreksi tersimpan
                    </span>
                  </div>
                </div>
              </div>

              <div v-if="msg.correcting" class="ml-9 bo-glass-card p-4 space-y-3">
                <p class="text-xs text-bo-300 flex items-center gap-1.5">
                  <PenLine :size="12" /> Masukkan jawaban yang benar
                </p>
                <textarea
                  v-model="msg.correctionText"
                  rows="3"
                  placeholder="Tuliskan jawaban yang seharusnya diberikan AI..."
                  class="bo-input w-full px-3 py-2 text-sm resize-none"
                />
                <div>
                  <label class="block text-xs text-bo-400 mb-1">Catatan admin (opsional)</label>
                  <input v-model="msg.correctionNote" placeholder="Misal: Berdasarkan pasal 3 ayat 2..."
                    class="bo-input w-full px-3 py-2 text-sm" />
                </div>
                <div class="flex gap-2">
                  <button @click="saveCorrection(msg, idx)" :disabled="!msg.correctionText"
                    class="bo-btn-primary px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 disabled:opacity-40">
                    <Save :size="12" /> Simpan Koreksi
                  </button>
                  <button @click="msg.correcting = false"
                    class="px-3 py-1.5 rounded-lg text-xs text-bo-400 hover:text-white hover:bg-white/10 transition">
                    Batal
                  </button>
                </div>
              </div>
            </div>
          </template>

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

        <div class="border-t border-white/10 p-3 flex gap-2">
          <input
            v-model="inputMsg"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="Ketik pertanyaan tentang dokumen ini..."
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

    <!-- Riwayat Koreksi -->
    <div class="bo-glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
        <span class="text-bo-100 font-semibold text-sm flex items-center gap-2">
          <History :size="14" /> Riwayat Koreksi Tersimpan
        </span>
        <button @click="fetchFeedbacks" class="text-bo-300 hover:text-white transition">
          <RefreshCw :size="14" :class="loadingHistory ? 'animate-spin' : ''" />
        </button>
      </div>

      <div v-if="loadingHistory" class="p-8 text-center text-bo-400 text-sm">
        <Loader2 :size="20" class="animate-spin mx-auto mb-2" />
      </div>
      <div v-else-if="feedbacks.length === 0" class="p-8 text-center text-bo-400 text-sm">
        <BookOpen :size="32" class="mx-auto mb-2 opacity-30" />
        Belum ada koreksi tersimpan
      </div>

      <table v-else class="w-full bo-table">
        <thead>
          <tr>
            <th class="text-left">Pertanyaan</th>
            <th class="text-left">Koreksi Jawaban</th>
            <th class="text-left">Status</th>
            <th class="text-left">Tanggal</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fb in feedbacks" :key="fb.id">
            <td class="max-w-xs"><p class="truncate">{{ fb.pertanyaan_asli }}</p></td>
            <td class="max-w-sm"><p class="truncate">{{ fb.jawaban_koreksi }}</p></td>
            <td><StatusBadge :status="fb.status" /></td>
            <td>{{ formatDate(fb.created_at) }}</td>
            <td class="text-right pr-4">
              <div class="flex items-center justify-end gap-1">
                <button v-if="fb.status === 'pending'" @click="applyFeedback(fb)"
                  title="Apply sebagai ground truth"
                  class="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/20 transition">
                  <CheckCheck :size="13" />
                </button>
                <button @click="confirmDelete(fb)"
                  class="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition">
                  <Trash2 :size="13" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmModal v-model="showConfirm" title="Hapus Koreksi"
      message="Koreksi ini akan dihapus permanen."
      @confirm="deleteCorrection" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  BookOpen, Search, FileText, X, MessageSquarePlus, MessageSquare,
  Bot, PenLine, Save, CheckCircle2, SendHorizontal, History,
  RefreshCw, Loader2, Trash2, CheckCheck
} from 'lucide-vue-next'
import { docApi, feedbackApi, chatApi } from '../../../services/backofficeApi'
import StatusBadge  from '../StatusBadge.vue'
import ConfirmModal from '../ConfirmModal.vue'

// ── Dokumen ─────────────────────────────────────────────
const docs            = ref([])
const docSearch       = ref('')
const showDocDropdown = ref(false)
const selectedDoc     = ref(null)

const filteredDocs = computed(() =>
  docs.value
    .filter(d => d.status === 'ready')
    .filter(d => d.judul.toLowerCase().includes(docSearch.value.toLowerCase()))
)

function selectDoc(doc) {
  selectedDoc.value     = doc
  docSearch.value       = doc.judul
  showDocDropdown.value = false
}

function handleBlur() {
  setTimeout(() => { showDocDropdown.value = false }, 150)
}

// ── Session Chat ─────────────────────────────────────────
const activeSession = ref(null)
const messages      = ref([])
const inputMsg      = ref('')
const aiTyping      = ref(false)
const chatBoxRef    = ref(null)

function startSession() {
  if (!selectedDoc.value) return
  activeSession.value = `admin-${Date.now()}`
  messages.value = []
}

function endSession() {
  activeSession.value = null
  messages.value      = []
  inputMsg.value      = ''
}

async function sendMessage() {
  const text = inputMsg.value.trim()
  if (!text || aiTyping.value) return

  messages.value.push({ role: 'user', content: text })
  inputMsg.value = ''
  aiTyping.value = true
  scrollBottom()

  try {
    const res = await chatApi.send(text, activeSession.value)
    messages.value.push({
      role: 'assistant',
      content: res.answer,
      correcting: false,
      corrected: false,
      correctionText: '',
      correctionNote: '',
    })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `Terjadi kesalahan: ${e.message}`, correcting: false, corrected: false })
  } finally {
    aiTyping.value = false
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => {
    if (chatBoxRef.value) chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
  })
}

// ── Koreksi ──────────────────────────────────────────────
async function saveCorrection(msg, idx) {
  const userMsg = [...messages.value].slice(0, idx).reverse().find(m => m.role === 'user')
  try {
    await feedbackApi.create({
      pertanyaan_asli:  userMsg?.content || '',
      jawaban_ai:       msg.content,
      jawaban_koreksi:  msg.correctionText,
      catatan_admin:    msg.correctionNote || null,
    })
    msg.correcting = false
    msg.corrected  = true
    fetchFeedbacks()
  } catch (e) {
    console.error(e)
  }
}

// ── Riwayat Koreksi ──────────────────────────────────────
const feedbacks      = ref([])
const loadingHistory = ref(false)
const showConfirm    = ref(false)
const selected       = ref(null)

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function fetchFeedbacks() {
  loadingHistory.value = true
  try { feedbacks.value = await feedbackApi.list() } catch (e) { console.error(e) }
  finally { loadingHistory.value = false }
}

async function applyFeedback(fb) {
  try { await feedbackApi.apply(fb.id); fetchFeedbacks() } catch (e) { console.error(e) }
}

function confirmDelete(fb) { selected.value = fb; showConfirm.value = true }

async function deleteCorrection() {
  try { await feedbackApi.delete(selected.value.id); fetchFeedbacks() } catch (e) { console.error(e) }
}

onMounted(async () => {
  docs.value = await docApi.list().catch(() => [])
  fetchFeedbacks()
})
</script>
