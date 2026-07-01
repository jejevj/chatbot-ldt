<template>
  <BackofficeLayout>
    <div class="space-y-5">

      <!-- Step 1: Pilih Dokumen -->
      <div v-if="!activeSession" class="bo-glass-card p-6">
        <h3 class="text-bo-100 font-semibold text-sm mb-1 flex items-center gap-2">
          <BrainCircuit :size="15" /> Mulai Sesi Pelatihan
        </h3>
        <p class="text-bo-400 text-xs mb-5">
          Pilih dokumen rujukan, ajukan pertanyaan ke AI, lalu koreksi jawaban yang salah.
          Koreksi akan disimpan sebagai bahan pelatihan.
        </p>

        <div class="mb-4">
          <label class="block text-xs text-bo-300 mb-1.5">Pilih Dokumen Rujukan</label>
          <div class="relative">
            <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-bo-400" />
            <input
              v-model="docSearch"
              @focus="showDrop = true"
              @blur="() => setTimeout(() => showDrop = false, 150)"
              placeholder="Cari dokumen..."
              class="bo-input w-full pl-9 pr-4 py-2.5 text-sm"
            />
            <!-- Dropdown -->
            <div v-if="showDrop && filteredDocs.length"
              class="absolute z-30 mt-1 w-full bo-glass-card overflow-hidden max-h-52 overflow-y-auto">
              <button v-for="doc in filteredDocs" :key="doc.id"
                @mousedown.prevent="selectDoc(doc)"
                class="w-full text-left px-4 py-2.5 text-sm text-bo-200 hover:bg-white/10 transition flex items-center justify-between gap-3">
                <span class="truncate">{{ doc.judul }}</span>
                <StatusBadge :status="doc.status" />
              </button>
            </div>
            <div v-if="showDrop && !filteredDocs.length && docSearch"
              class="absolute z-30 mt-1 w-full bo-glass-card px-4 py-3 text-sm text-bo-400">
              Dokumen tidak ditemukan
            </div>
          </div>

          <!-- Chip -->
          <div v-if="selectedDoc" class="mt-2 flex items-center gap-2 bg-bo-800/40 border border-bo-700/40 rounded-lg px-3 py-2">
            <BookMarked :size="13" class="text-bo-300 flex-shrink-0" />
            <span class="text-sm text-bo-100 flex-1 truncate">{{ selectedDoc.judul }}</span>
            <button @click="selectedDoc = null; docSearch = ''" class="text-bo-400 hover:text-white">
              <X :size="13" />
            </button>
          </div>
        </div>

        <button @click="startSession" :disabled="!selectedDoc"
          class="bo-btn-primary px-5 py-2.5 rounded-xl text-sm font-medium flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          <MessageSquarePlus :size="15" /> Mulai Sesi
        </button>
      </div>

      <!-- Step 2: Chat + Koreksi -->
      <div v-else class="space-y-3">
        <!-- Session bar -->
        <div class="bo-glass-card px-5 py-3 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <BookMarked :size="14" class="text-bo-400" />
            <div>
              <p class="text-xs text-bo-400">Sesi aktif</p>
              <p class="text-sm font-medium text-bo-100">{{ selectedDoc.judul }}</p>
            </div>
          </div>
          <button @click="endSession" class="flex items-center gap-1.5 text-xs text-bo-400 hover:text-white hover:bg-white/10 px-3 py-1.5 rounded-lg transition">
            <X :size="13" /> Akhiri Sesi
          </button>
        </div>

        <!-- Chat -->
        <div class="bo-glass-card overflow-hidden">
          <div ref="chatRef" class="h-[26rem] overflow-y-auto p-4 space-y-4">
            <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-bo-400 text-sm gap-2">
              <BrainCircuit :size="30" class="opacity-20" />
              <p>Ajukan pertanyaan untuk menguji AI</p>
            </div>

            <template v-for="(msg, idx) in messages" :key="idx">
              <!-- User -->
              <div v-if="msg.role === 'user'" class="flex justify-end">
                <div class="max-w-lg bg-bo-800/60 border border-bo-700/40 rounded-2xl rounded-tr-sm px-4 py-2.5">
                  <p class="text-sm text-bo-100">{{ msg.content }}</p>
                </div>
              </div>

              <!-- AI -->
              <div v-else class="flex flex-col gap-1">
                <div class="flex items-start gap-2.5">
                  <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-bo-600 to-bo-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot :size="13" class="text-white" />
                  </div>
                  <div class="flex-1">
                    <div class="bo-glass max-w-lg rounded-2xl rounded-tl-sm px-4 py-2.5">
                      <p class="text-sm text-bo-100 whitespace-pre-wrap">{{ msg.content }}</p>
                    </div>
                    <div class="mt-1.5 ml-1">
                      <button v-if="!msg.correcting && !msg.corrected"
                        @click="msg.correcting = true"
                        class="flex items-center gap-1.5 text-xs text-bo-500 hover:text-amber-300 transition">
                        <PenLine :size="11" /> Jawaban ini salah? Koreksi
                      </button>
                      <span v-if="msg.corrected" class="flex items-center gap-1 text-xs text-emerald-400">
                        <CheckCircle2 :size="11" /> Koreksi tersimpan sebagai bahan latihan
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Form Koreksi Inline -->
                <div v-if="msg.correcting" class="ml-9 bo-glass-card p-4 space-y-3">
                  <p class="text-xs text-bo-300 font-medium">Jawaban yang seharusnya diberikan AI:</p>
                  <textarea v-model="msg.correctionText" rows="3"
                    placeholder="Tuliskan jawaban yang benar dan lengkap..."
                    class="bo-input w-full px-3 py-2 text-sm resize-none" />
                  <div>
                    <label class="block text-xs text-bo-400 mb-1">Catatan / referensi (opsional)</label>
                    <input v-model="msg.correctionNote"
                      placeholder="Misal: Berdasarkan Pasal 5 UU No. 3 Tahun 2002..."
                      class="bo-input w-full px-3 py-2 text-sm" />
                  </div>
                  <div class="flex gap-2">
                    <button @click="saveCorrection(msg, idx)" :disabled="!msg.correctionText || msg.saving"
                      class="bo-btn-primary px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 disabled:opacity-40">
                      <Loader2 v-if="msg.saving" :size="11" class="animate-spin" />
                      <Save v-else :size="11" /> Simpan sebagai Data Latihan
                    </button>
                    <button @click="msg.correcting = false"
                      class="px-3 py-1.5 rounded-lg text-xs text-bo-400 hover:text-white hover:bg-white/10 transition">Batal</button>
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

          <div class="border-t border-white/10 p-3 flex gap-2">
            <input v-model="inputMsg" @keydown.enter.exact.prevent="sendMessage"
              placeholder="Ketik pertanyaan untuk diuji..." :disabled="aiTyping"
              class="bo-input flex-1 px-4 py-2.5 text-sm" />
            <button @click="sendMessage" :disabled="!inputMsg.trim() || aiTyping"
              class="bo-btn-primary px-4 py-2.5 rounded-xl disabled:opacity-40">
              <SendHorizontal :size="16" />
            </button>
          </div>
        </div>
      </div>

      <!-- Riwayat Data Latihan -->
      <div class="bo-glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
          <span class="text-bo-100 font-semibold text-sm flex items-center gap-2">
            <History :size="14" /> Riwayat Data Latihan
          </span>
          <button @click="fetchFeedbacks" class="text-bo-300 hover:text-white transition">
            <RefreshCw :size="14" :class="loadingFb ? 'animate-spin' : ''" />
          </button>
        </div>

        <div v-if="loadingFb" class="p-8 text-center text-bo-400 text-sm">
          <Loader2 :size="20" class="animate-spin mx-auto mb-2" />
        </div>
        <div v-else-if="feedbacks.length === 0" class="p-8 text-center text-bo-400 text-sm">
          <BrainCircuit :size="32" class="mx-auto mb-2 opacity-20" />
          Belum ada data latihan tersimpan
        </div>

        <table v-else class="w-full bo-table">
          <thead>
            <tr>
              <th class="text-left">Pertanyaan Asal</th>
              <th class="text-left">Koreksi Jawaban</th>
              <th class="text-left">Status</th>
              <th class="text-left">Disimpan</th>
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
                    title="Terapkan sebagai ground truth"
                    class="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/20 transition">
                    <CheckCheck :size="13" />
                  </button>
                  <button @click="confirmDelete(fb)" class="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition">
                    <Trash2 :size="13" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmModal v-model="showConfirm" title="Hapus Data Latihan"
      message="Data latihan ini akan dihapus permanen."
      @confirm="deleteFeedback" />
  </BackofficeLayout>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  BrainCircuit, Search, BookMarked, X, MessageSquarePlus,
  Bot, PenLine, Save, CheckCircle2, SendHorizontal,
  History, RefreshCw, Loader2, Trash2, CheckCheck
} from 'lucide-vue-next'
import BackofficeLayout from '../../components/backoffice/BackofficeLayout.vue'
import StatusBadge      from '../../components/backoffice/StatusBadge.vue'
import ConfirmModal     from '../../components/backoffice/ConfirmModal.vue'
import { docApi, feedbackApi, chatApi } from '../../services/backofficeApi'

// Dokumen
const allDocs      = ref([])
const docSearch    = ref('')
const showDrop     = ref(false)
const selectedDoc  = ref(null)

const filteredDocs = computed(() =>
  allDocs.value
    .filter(d => d.status === 'ready')
    .filter(d => d.judul.toLowerCase().includes(docSearch.value.toLowerCase()))
)

function selectDoc(doc) {
  selectedDoc.value = doc
  docSearch.value   = doc.judul
  showDrop.value    = false
}

// Session
const activeSession = ref(null)
const messages      = ref([])
const inputMsg      = ref('')
const aiTyping      = ref(false)
const chatRef       = ref(null)

function startSession() {
  if (!selectedDoc.value) return
  activeSession.value = `train-${Date.now()}`
  messages.value = []
}

function endSession() {
  activeSession.value = null
  messages.value = []
  inputMsg.value = ''
}

async function sendMessage() {
  const text = inputMsg.value.trim()
  if (!text || aiTyping.value) return
  messages.value.push({ role: 'user', content: text })
  inputMsg.value = ''
  aiTyping.value = true
  scroll()
  try {
    const res = await chatApi.send(text, activeSession.value)
    messages.value.push({
      role: 'assistant', content: res.answer,
      correcting: false, corrected: false, saving: false,
      correctionText: '', correctionNote: ''
    })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `Error: ${e.message}`, correcting: false, corrected: false })
  } finally {
    aiTyping.value = false
    scroll()
  }
}

function scroll() {
  nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight })
}

async function saveCorrection(msg, idx) {
  const userMsg = [...messages.value].slice(0, idx).reverse().find(m => m.role === 'user')
  msg.saving = true
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
  } catch (e) { console.error(e) }
  finally { msg.saving = false }
}

// Feedback history
const feedbacks    = ref([])
const loadingFb    = ref(false)
const showConfirm  = ref(false)
const selectedFb   = ref(null)

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function fetchFeedbacks() {
  loadingFb.value = true
  try { feedbacks.value = await feedbackApi.list() } catch (e) { console.error(e) }
  finally { loadingFb.value = false }
}

async function applyFeedback(fb) {
  try { await feedbackApi.apply(fb.id); fetchFeedbacks() } catch (e) { console.error(e) }
}

function confirmDelete(fb) { selectedFb.value = fb; showConfirm.value = true }
async function deleteFeedback() {
  try { await feedbackApi.delete(selectedFb.value.id); fetchFeedbacks() } catch (e) { console.error(e) }
}

onMounted(async () => {
  allDocs.value = await docApi.list().catch(() => [])
  fetchFeedbacks()
})
</script>
