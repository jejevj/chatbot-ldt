<template>
  <div class="space-y-5">
    <!-- Upload Card -->
    <div class="bo-glass-card p-5">
      <h3 class="text-bo-100 font-semibold text-sm mb-4 flex items-center gap-2">
        <Upload :size="15" /> Upload Dokumen Baru
      </h3>
      <form @submit.prevent="handleUpload" class="flex flex-wrap gap-3 items-end">
        <div class="flex-1 min-w-40">
          <label class="block text-xs text-bo-300 mb-1">Judul Dokumen</label>
          <input v-model="form.judul" required placeholder="Judul..." class="bo-input w-full px-3 py-2 text-sm" />
        </div>
        <div class="w-36">
          <label class="block text-xs text-bo-300 mb-1">Tipe</label>
          <select v-model="form.tipe" class="bo-input w-full px-3 py-2 text-sm">
            <option value="umum">Umum</option>
            <option value="teknis">Teknis</option>
            <option value="regulasi">Regulasi</option>
          </select>
        </div>
        <div class="flex-1 min-w-48">
          <label class="block text-xs text-bo-300 mb-1">File (PDF/DOCX/TXT)</label>
          <input type="file" @change="onFile" accept=".pdf,.docx,.txt" required
            class="bo-input w-full px-3 py-2 text-sm file:mr-3 file:py-0 file:px-2 file:rounded file:border-0 file:text-xs file:bg-bo-800 file:text-bo-100 cursor-pointer" />
        </div>
        <button type="submit" :disabled="uploading"
          class="bo-btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
          <Loader2 v-if="uploading" :size="14" class="animate-spin" />
          <Upload v-else :size="14" />
          {{ uploading ? 'Mengupload...' : 'Upload' }}
        </button>
      </form>
      <p v-if="uploadError" class="text-red-400 text-xs mt-2 flex items-center gap-1"><AlertCircle :size="12" /> {{ uploadError }}</p>
      <p v-if="uploadSuccess" class="text-emerald-400 text-xs mt-2 flex items-center gap-1"><CheckCircle2 :size="12" /> {{ uploadSuccess }}</p>
    </div>

    <!-- Table -->
    <div class="bo-glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
        <span class="text-bo-100 font-semibold text-sm">Daftar Dokumen</span>
        <button @click="fetchDocs" class="text-bo-300 hover:text-white transition">
          <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        </button>
      </div>

      <div v-if="loading" class="p-8 text-center text-bo-400 text-sm">
        <Loader2 :size="20" class="animate-spin mx-auto mb-2" /> Memuat data...
      </div>

      <div v-else-if="docs.length === 0" class="p-8 text-center text-bo-400 text-sm">
        <FileX :size="32" class="mx-auto mb-2 opacity-40" />
        Belum ada dokumen
      </div>

      <table v-else class="w-full bo-table">
        <thead>
          <tr>
            <th class="text-left">Judul</th>
            <th class="text-left">Tipe</th>
            <th class="text-left">Status</th>
            <th class="text-left">Chunks</th>
            <th class="text-left">Tanggal</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in docs" :key="doc.id">
            <td class="font-medium">{{ doc.judul }}</td>
            <td><span class="capitalize">{{ doc.tipe }}</span></td>
            <td><StatusBadge :status="doc.status" /></td>
            <td>{{ doc.total_chunks ?? '-' }}</td>
            <td>{{ formatDate(doc.uploaded_at) }}</td>
            <td class="text-right pr-4">
              <button @click="confirmDelete(doc)"
                class="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition">
                <Trash2 :size="14" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmModal
      v-model="showConfirm"
      title="Hapus Dokumen"
      :message="`Dokumen '${selected?.judul}' akan dihapus permanen beserta semua chunk & embedding-nya.`"
      confirm-label="Hapus"
      @confirm="deleteDoc"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Upload, RefreshCw, Trash2, FileX, Loader2, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import { docApi } from '../../../services/backofficeApi'
import StatusBadge  from '../StatusBadge.vue'
import ConfirmModal from '../ConfirmModal.vue'

const docs          = ref([])
const loading       = ref(false)
const uploading     = ref(false)
const uploadError   = ref('')
const uploadSuccess = ref('')
const showConfirm   = ref(false)
const selected      = ref(null)
const form          = ref({ judul: '', tipe: 'umum' })
const file          = ref(null)

function onFile(e) { file.value = e.target.files[0] }

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('id-ID', { day:'2-digit', month:'short', year:'numeric' })
}

async function fetchDocs() {
  loading.value = true
  try { docs.value = await docApi.list() }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function handleUpload() {
  uploadError.value = ''
  uploadSuccess.value = ''
  if (!file.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('judul', form.value.judul)
    fd.append('tipe',  form.value.tipe)
    fd.append('file',  file.value)
    await docApi.upload(fd)
    uploadSuccess.value = 'Dokumen berhasil diupload dan sedang diproses'
    form.value = { judul: '', tipe: 'umum' }
    file.value = null
    fetchDocs()
  } catch (e) {
    uploadError.value = e.message
  } finally {
    uploading.value = false
  }
}

function confirmDelete(doc) { selected.value = doc; showConfirm.value = true }

async function deleteDoc() {
  try {
    await docApi.delete(selected.value.id)
    fetchDocs()
  } catch (e) { console.error(e) }
}

onMounted(fetchDocs)
</script>
