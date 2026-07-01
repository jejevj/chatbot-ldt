<template>
  <BackofficeLayout>
    <div class="space-y-5">

      <!-- Upload Card -->
      <div class="bo-glass-card p-5">
        <h3 class="text-bo-100 font-semibold text-sm mb-1 flex items-center gap-2">
          <Upload :size="15" /> Upload Dokumen Baru
        </h3>
        <p class="text-bo-400 text-xs mb-4">Dokumen yang diupload akan dijadikan sumber pengetahuan chatbot. Mendukung PDF, DOCX, dan TXT.</p>

        <form @submit.prevent="handleUpload" class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-44">
            <label class="block text-xs text-bo-300 mb-1">Judul Dokumen</label>
            <input v-model="form.judul" required placeholder="Contoh: UU No. 3 Tahun 2002" class="bo-input w-full px-3 py-2 text-sm" />
          </div>
          <div class="w-36">
            <label class="block text-xs text-bo-300 mb-1">Kategori</label>
            <select v-model="form.tipe" class="bo-input w-full px-3 py-2 text-sm">
              <option value="umum">Umum</option>
              <option value="regulasi">Regulasi / UU</option>
              <option value="teknis">Teknis</option>
              <option value="faq">FAQ</option>
            </select>
          </div>
          <div class="flex-1 min-w-52">
            <label class="block text-xs text-bo-300 mb-1">File (PDF / DOCX / TXT)</label>
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

        <div v-if="uploadMsg" class="mt-3 flex items-center gap-1.5 text-xs" :class="uploadMsg.type === 'ok' ? 'text-emerald-400' : 'text-red-400'">
          <CheckCircle2 v-if="uploadMsg.type === 'ok'" :size="12" />
          <AlertCircle  v-else :size="12" />
          {{ uploadMsg.text }}
        </div>
      </div>

      <!-- Daftar Dokumen -->
      <div class="bo-glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
          <span class="text-bo-100 font-semibold text-sm">Daftar Dokumen Rujukan</span>
          <button @click="fetchDocs" class="text-bo-300 hover:text-white transition">
            <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
          </button>
        </div>

        <div v-if="loading" class="p-10 text-center text-bo-400 text-sm">
          <Loader2 :size="20" class="animate-spin mx-auto mb-2" /> Memuat...
        </div>
        <div v-else-if="docs.length === 0" class="p-10 text-center text-bo-400 text-sm">
          <FileX :size="36" class="mx-auto mb-2 opacity-30" />
          Belum ada dokumen yang diupload
        </div>

        <table v-else class="w-full bo-table">
          <thead>
            <tr>
              <th class="text-left">Judul</th>
              <th class="text-left">Kategori</th>
              <th class="text-left">Status</th>
              <th class="text-left">Chunks</th>
              <th class="text-left">Tanggal Upload</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in docs" :key="doc.id">
              <td class="font-medium max-w-xs">
                <p class="truncate">{{ doc.judul }}</p>
                <p class="text-xs text-bo-500 truncate">{{ doc.filename }}</p>
              </td>
              <td><span class="capitalize">{{ doc.tipe }}</span></td>
              <td>
                <StatusBadge :status="doc.status" />
                <p v-if="doc.error_message" class="text-xs text-red-400 mt-0.5 truncate max-w-32">{{ doc.error_message }}</p>
              </td>
              <td>{{ doc.total_chunks ?? '-' }}</td>
              <td>{{ formatDate(doc.uploaded_at) }}</td>
              <td class="text-right pr-4">
                <button @click="confirmDelete(doc)" class="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition">
                  <Trash2 :size="14" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmModal v-model="showConfirm"
      title="Hapus Dokumen"
      :message="`Dokumen '${selected?.judul}' akan dihapus permanen beserta seluruh data embedding-nya.`"
      confirm-label="Hapus"
      @confirm="deleteDoc" />
  </BackofficeLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Upload, RefreshCw, Trash2, FileX, Loader2, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import BackofficeLayout from '../../components/backoffice/BackofficeLayout.vue'
import StatusBadge      from '../../components/backoffice/StatusBadge.vue'
import ConfirmModal     from '../../components/backoffice/ConfirmModal.vue'
import { docApi } from '../../services/backofficeApi'

const docs        = ref([])
const loading     = ref(false)
const uploading   = ref(false)
const uploadMsg   = ref(null)
const showConfirm = ref(false)
const selected    = ref(null)
const form        = ref({ judul: '', tipe: 'umum' })
const file        = ref(null)

function onFile(e) { file.value = e.target.files[0] }
function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function fetchDocs() {
  loading.value = true
  try { docs.value = await docApi.list() } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function handleUpload() {
  uploadMsg.value = null
  if (!file.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('judul', form.value.judul)
    fd.append('tipe',  form.value.tipe)
    fd.append('file',  file.value)
    await docApi.upload(fd)
    uploadMsg.value = { type: 'ok', text: 'Dokumen berhasil diupload dan sedang diproses' }
    form.value = { judul: '', tipe: 'umum' }
    file.value = null
    fetchDocs()
  } catch (e) {
    uploadMsg.value = { type: 'err', text: e.message }
  } finally {
    uploading.value = false
  }
}

function confirmDelete(doc) { selected.value = doc; showConfirm.value = true }
async function deleteDoc() {
  try { await docApi.delete(selected.value.id); fetchDocs() } catch (e) { console.error(e) }
}

onMounted(fetchDocs)
</script>
