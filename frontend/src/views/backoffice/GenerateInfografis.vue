<template>
  <BackofficeLayout>
    <div class="space-y-5">
      <!-- Header Beta -->
      <div class="bo-glass-card p-5 border border-amber-500/30">
        <div class="flex items-center justify-between gap-3 mb-3">
          <div class="flex items-center gap-2">
            <Sparkles :size="16" class="text-amber-300" />
            <h3 class="text-bo-100 font-semibold text-sm flex items-center gap-2">
              Beta: Generate Infografis
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-200 font-medium uppercase tracking-widest">Eksperimental</span>
            </h3>
          </div>
        </div>
        <p class="text-bo-400 text-xs mb-4">
          Pilih satu dokumen rujukan. AI akan membaca isi dokumen lalu menyimpulkan
          poin-poin penting yang cocok dijadikan infografis (judul, ringkasan, dan data utama),
          kemudian menghasilkan kode SVG yang siap ditampilkan.
        </p>

        <!-- Loading dokumen -->
        <div v-if="loadingDocs" class="flex items-center gap-2 text-xs text-bo-400 mb-3">
          <Loader2 :size="12" class="animate-spin" /> Memuat daftar dokumen...
        </div>

        <!-- Selector Dokumen + Generate -->
        <div v-else class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-56">
            <label class="block text-xs text-bo-300 mb-1">
              Pilih Dokumen
              <span class="text-bo-500">({{ docs.length }} tersedia)</span>
            </label>
            <select v-model="selectedId" class="bo-input w-full px-3 py-2 text-sm">
              <option value="" disabled>-- Pilih dokumen rujukan --</option>
              <option v-for="doc in docs" :key="doc.id" :value="doc.id">
                {{ doc.judul }} — {{ doc.tipe }}
              </option>
            </select>
          </div>

          <button
            @click="handleGenerate"
            :disabled="!selectedId || loadingGenerate"
            class="bo-btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="loadingGenerate" :size="14" class="animate-spin" />
            <ImageIcon v-else :size="14" />
            {{ loadingGenerate ? 'Menggenerate...' : 'Generate Infografis' }}
          </button>
        </div>

        <div v-if="statusMsg" class="mt-3 flex items-center gap-1.5 text-xs"
          :class="statusMsg.type === 'ok' ? 'text-emerald-400' : 'text-red-400'">
          <CheckCircle2 v-if="statusMsg.type === 'ok'" :size="12" />
          <AlertCircle v-else :size="12" />
          {{ statusMsg.text }}
        </div>
      </div>

      <!-- Preview Infografis SVG -->
      <div class="bo-glass-card p-5 min-h-64 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h4 class="text-bo-100 text-sm font-semibold flex items-center gap-2">
            <LayoutPanelTop :size="14" /> Pratinjau Infografis
          </h4>
          <div class="flex gap-2" v-if="svgCode">
            <button
              @click="downloadSvg"
              class="text-xs px-3 py-1 rounded-lg border border-white/15 text-bo-200 hover:bg-white/10 transition flex items-center gap-1"
            >
              <Download :size="12" /> Unduh SVG
            </button>
            <button
              @click="copySvg"
              class="text-xs px-3 py-1 rounded-lg border border-white/15 text-bo-200 hover:bg-white/10 transition flex items-center gap-1"
            >
              <Copy :size="12" /> Salin SVG
            </button>
          </div>
        </div>

        <div v-if="loadingGenerate" class="flex-1 flex flex-col items-center justify-center text-bo-400 text-sm py-10">
          <Loader2 :size="28" class="animate-spin mb-3" />
          <p>AI sedang membaca dokumen dan menyusun infografis...</p>
          <p class="text-xs text-bo-500 mt-1">Proses ini memerlukan sekitar 10–30 detik</p>
        </div>

        <div v-else-if="!svgCode" class="flex-1 flex flex-col items-center justify-center text-bo-400 text-sm text-center py-10">
          <LayoutPanelTop :size="36" class="mb-3 opacity-30" />
          <p>Belum ada infografis yang dihasilkan.</p>
          <p class="text-xs mt-1 text-bo-500">Pilih dokumen lalu klik "Generate Infografis".</p>
        </div>

        <!-- Render SVG -->
        <div v-else class="mt-2 bg-black/20 rounded-xl p-4 border border-white/10 overflow-auto">
          <div class="w-full flex items-start justify-center" v-html="svgCode" />
        </div>
      </div>
    </div>
  </BackofficeLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Sparkles, Loader2, ImageIcon, CheckCircle2, AlertCircle,
  LayoutPanelTop, Copy, Download
} from 'lucide-vue-next'
import BackofficeLayout from '../../components/backoffice/BackofficeLayout.vue'
import { docApi } from '../../services/backofficeApi'
import { infografisApi } from '../../services/infografisApi'

const docs            = ref([])
const selectedId      = ref('')
const svgCode         = ref('')
const selectedJudul   = ref('')
const loadingDocs     = ref(false)
const loadingGenerate = ref(false)
const statusMsg       = ref(null)

onMounted(fetchDocs)

async function fetchDocs() {
  loadingDocs.value = true
  statusMsg.value   = null
  try {
    const all = await docApi.list()
    // Pastikan array, filter hanya dokumen yg sudah siap
    const arr = Array.isArray(all) ? all : (all?.items ?? [])
    docs.value = arr.filter(d => d.status === 'ready')
    if (docs.value.length === 0) {
      statusMsg.value = { type: 'err', text: 'Belum ada dokumen yang siap dipakai. Upload dan proses dokumen terlebih dahulu.' }
    }
  } catch (e) {
    console.error('[infografis] gagal load docs:', e)
    statusMsg.value = { type: 'err', text: `Gagal memuat daftar dokumen: ${e.message}` }
  } finally {
    loadingDocs.value = false
  }
}

async function handleGenerate() {
  if (!selectedId.value) return
  statusMsg.value       = null
  loadingGenerate.value = true
  svgCode.value         = ''
  selectedJudul.value   = docs.value.find(d => d.id === selectedId.value)?.judul ?? ''
  try {
    const res = await infografisApi.generate(selectedId.value)
    svgCode.value = res.svg || ''
    if (!svgCode.value) throw new Error('AI tidak menghasilkan SVG yang valid')
    statusMsg.value = { type: 'ok', text: `Infografis berhasil dibuat dari "${res.judul_dokumen}"` }
  } catch (e) {
    console.error('[infografis] generate error:', e)
    statusMsg.value = { type: 'err', text: e.message || 'Gagal generate infografis' }
  } finally {
    loadingGenerate.value = false
  }
}

async function copySvg() {
  try {
    await navigator.clipboard.writeText(svgCode.value)
    statusMsg.value = { type: 'ok', text: 'Kode SVG berhasil disalin ke clipboard' }
  } catch {
    statusMsg.value = { type: 'err', text: 'Gagal menyalin SVG' }
  }
}

function downloadSvg() {
  const blob = new Blob([svgCode.value], { type: 'image/svg+xml' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `infografis-${selectedJudul.value.replace(/\s+/g, '-').toLowerCase() || 'dokumen'}.svg`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
