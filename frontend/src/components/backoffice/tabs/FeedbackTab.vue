<template>
  <div class="space-y-5">
    <!-- Form Tambah Koreksi -->
    <div class="bo-glass-card p-5">
      <h3 class="text-bo-100 font-semibold text-sm mb-4 flex items-center gap-2">
        <Plus :size="15" /> Tambah Koreksi Manual
      </h3>
      <form @submit.prevent="handleSubmit" class="space-y-3">
        <div>
          <label class="block text-xs text-bo-300 mb-1">Pertanyaan Asal</label>
          <input v-model="form.question" required placeholder="Pertanyaan yang salah dijawab AI..."
            class="bo-input w-full px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs text-bo-300 mb-1">Jawaban AI (salah)</label>
          <textarea v-model="form.ai_answer" placeholder="Jawaban AI yang tidak tepat..." rows="2"
            class="bo-input w-full px-3 py-2 text-sm resize-none"></textarea>
        </div>
        <div>
          <label class="block text-xs text-bo-300 mb-1">Koreksi Jawaban (benar)</label>
          <textarea v-model="form.corrected_answer" required placeholder="Jawaban yang benar..." rows="2"
            class="bo-input w-full px-3 py-2 text-sm resize-none"></textarea>
        </div>
        <button type="submit" :disabled="saving"
          class="bo-btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
          <Loader2 v-if="saving" :size="14" class="animate-spin" />
          <Save v-else :size="14" />
          {{ saving ? 'Menyimpan...' : 'Simpan Koreksi' }}
        </button>
      </form>
      <p v-if="msg" class="text-emerald-400 text-xs mt-2 flex items-center gap-1"><CheckCircle2 :size="12" /> {{ msg }}</p>
    </div>

    <!-- Table -->
    <div class="bo-glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
        <span class="text-bo-100 font-semibold text-sm">Daftar Koreksi AI</span>
        <button @click="fetchFeedback" class="text-bo-300 hover:text-white transition">
          <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        </button>
      </div>

      <div v-if="loading" class="p-8 text-center text-bo-400 text-sm">
        <Loader2 :size="20" class="animate-spin mx-auto mb-2" /> Memuat data...
      </div>
      <div v-else-if="feedbacks.length === 0" class="p-8 text-center text-bo-400 text-sm">
        <MessageSquareWarning :size="32" class="mx-auto mb-2 opacity-40" /> Belum ada koreksi
      </div>

      <table v-else class="w-full bo-table">
        <thead>
          <tr>
            <th class="text-left">Pertanyaan</th>
            <th class="text-left">Koreksi</th>
            <th class="text-left">Status</th>
            <th class="text-left">Tanggal</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fb in feedbacks" :key="fb.id">
            <td class="max-w-xs truncate">{{ fb.question }}</td>
            <td class="max-w-sm truncate">{{ fb.corrected_answer }}</td>
            <td><StatusBadge :status="fb.status" /></td>
            <td>{{ formatDate(fb.created_at) }}</td>
            <td class="text-right pr-4">
              <div class="flex items-center justify-end gap-1">
                <button v-if="fb.status === 'pending'" @click="applyFeedback(fb)"
                  class="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/20 transition" title="Apply sebagai ground truth">
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

    <ConfirmModal v-model="showConfirm" title="Hapus Koreksi"
      :message="`Koreksi ini akan dihapus permanen.`"
      @confirm="deleteFeedback" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Save, Trash2, RefreshCw, Loader2, CheckCircle2, CheckCheck, MessageSquareWarning } from 'lucide-vue-next'
import { feedbackApi } from '../../../services/backofficeApi'
import StatusBadge  from '../StatusBadge.vue'
import ConfirmModal from '../ConfirmModal.vue'

const feedbacks   = ref([])
const loading     = ref(false)
const saving      = ref(false)
const msg         = ref('')
const showConfirm = ref(false)
const selected    = ref(null)
const form        = ref({ question: '', ai_answer: '', corrected_answer: '' })

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('id-ID', { day:'2-digit', month:'short', year:'numeric' })
}

async function fetchFeedback() {
  loading.value = true
  try { feedbacks.value = await feedbackApi.list() } catch(e) { console.error(e) }
  finally { loading.value = false }
}

async function handleSubmit() {
  saving.value = true; msg.value = ''
  try {
    await feedbackApi.create(form.value)
    msg.value  = 'Koreksi berhasil disimpan'
    form.value = { question: '', ai_answer: '', corrected_answer: '' }
    fetchFeedback()
  } catch(e) { console.error(e) }
  finally { saving.value = false }
}

async function applyFeedback(fb) {
  try { await feedbackApi.apply(fb.id); fetchFeedback() } catch(e) { console.error(e) }
}

function confirmDelete(fb) { selected.value = fb; showConfirm.value = true }

async function deleteFeedback() {
  try { await feedbackApi.delete(selected.value.id); fetchFeedback() } catch(e) { console.error(e) }
}

onMounted(fetchFeedback)
</script>
