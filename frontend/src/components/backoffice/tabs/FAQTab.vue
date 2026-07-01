<template>
  <div class="space-y-5">
    <!-- Form Tambah -->
    <div class="bo-glass-card p-5">
      <h3 class="text-bo-100 font-semibold text-sm mb-4 flex items-center gap-2">
        <Plus :size="15" /> {{ editId ? 'Edit FAQ' : 'Tambah FAQ Baru' }}
      </h3>
      <form @submit.prevent="handleSubmit" class="space-y-3">
        <div>
          <label class="block text-xs text-bo-300 mb-1">Pertanyaan</label>
          <input v-model="form.pertanyaan" required placeholder="Tuliskan pertanyaan..." class="bo-input w-full px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs text-bo-300 mb-1">Jawaban</label>
          <textarea v-model="form.jawaban" required placeholder="Tuliskan jawaban..." rows="3"
            class="bo-input w-full px-3 py-2 text-sm resize-none"></textarea>
        </div>
        <div class="flex gap-2">
          <button type="submit" :disabled="saving"
            class="bo-btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
            <Loader2 v-if="saving" :size="14" class="animate-spin" />
            <Save v-else :size="14" />
            {{ saving ? 'Menyimpan...' : (editId ? 'Update' : 'Simpan') }}
          </button>
          <button v-if="editId" type="button" @click="resetForm"
            class="px-4 py-2 rounded-lg text-sm text-bo-300 hover:text-white hover:bg-white/10 transition">
            Batal
          </button>
        </div>
      </form>
      <p v-if="msg" class="text-emerald-400 text-xs mt-2 flex items-center gap-1"><CheckCircle2 :size="12" /> {{ msg }}</p>
    </div>

    <!-- Table -->
    <div class="bo-glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
        <span class="text-bo-100 font-semibold text-sm">Daftar FAQ</span>
        <button @click="fetchFAQ" class="text-bo-300 hover:text-white transition">
          <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        </button>
      </div>

      <div v-if="loading" class="p-8 text-center text-bo-400 text-sm">
        <Loader2 :size="20" class="animate-spin mx-auto mb-2" /> Memuat data...
      </div>
      <div v-else-if="faqs.length === 0" class="p-8 text-center text-bo-400 text-sm">
        <HelpCircle :size="32" class="mx-auto mb-2 opacity-40" /> Belum ada FAQ
      </div>

      <table v-else class="w-full bo-table">
        <thead>
          <tr>
            <th class="text-left">Pertanyaan</th>
            <th class="text-left">Jawaban</th>
            <th class="text-left">Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="faq in faqs" :key="faq.id">
            <td class="max-w-xs truncate">{{ faq.pertanyaan }}</td>
            <td class="max-w-sm truncate">{{ faq.jawaban }}</td>
            <td><StatusBadge :status="faq.is_active ? 'active' : 'inactive'" /></td>
            <td class="text-right pr-4">
              <div class="flex items-center justify-end gap-1">
                <button @click="startEdit(faq)" class="p-1.5 rounded-lg text-bo-300 hover:bg-white/10 transition">
                  <Pencil :size="13" />
                </button>
                <button @click="confirmDelete(faq)" class="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition">
                  <Trash2 :size="13" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmModal v-model="showConfirm" title="Hapus FAQ"
      :message="`FAQ '${selected?.pertanyaan?.slice(0,60)}...' akan dihapus permanen.`"
      @confirm="deleteFAQ" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Save, Pencil, Trash2, RefreshCw, Loader2, CheckCircle2, HelpCircle } from 'lucide-vue-next'
import { faqApi } from '../../../services/backofficeApi'
import StatusBadge  from '../StatusBadge.vue'
import ConfirmModal from '../ConfirmModal.vue'

const faqs        = ref([])
const loading     = ref(false)
const saving      = ref(false)
const msg         = ref('')
const showConfirm = ref(false)
const selected    = ref(null)
const editId      = ref(null)
const form        = ref({ pertanyaan: '', jawaban: '' })

async function fetchFAQ() {
  loading.value = true
  try { faqs.value = await faqApi.list() } catch(e) { console.error(e) }
  finally { loading.value = false }
}

async function handleSubmit() {
  saving.value = true; msg.value = ''
  try {
    if (editId.value) {
      await faqApi.update(editId.value, form.value)
      msg.value = 'FAQ berhasil diupdate'
    } else {
      await faqApi.create(form.value)
      msg.value = 'FAQ berhasil ditambahkan'
    }
    resetForm(); fetchFAQ()
  } catch(e) { console.error(e) }
  finally { saving.value = false }
}

function startEdit(faq) {
  editId.value = faq.id
  form.value   = { pertanyaan: faq.pertanyaan, jawaban: faq.jawaban }
}

function resetForm() {
  editId.value = null
  form.value   = { pertanyaan: '', jawaban: '' }
}

function confirmDelete(faq) { selected.value = faq; showConfirm.value = true }

async function deleteFAQ() {
  try { await faqApi.delete(selected.value.id); fetchFAQ() } catch(e) { console.error(e) }
}

onMounted(fetchFAQ)
</script>
