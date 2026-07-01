<template>
  <BackofficeLayout>
    <div class="space-y-5">

      <!-- Header Beta -->
      <div class="bo-glass-card p-5 border border-amber-500/30">
        <div class="flex items-center gap-2 mb-2">
          <Sparkles :size="16" class="text-amber-300" />
          <h3 class="text-bo-100 font-semibold text-sm">
            Beta: Generate Infografis
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-200 font-medium uppercase tracking-widest ml-1">Eksperimental</span>
          </h3>
        </div>
        <p class="text-bo-400 text-xs mb-4">
          Pilih satu dokumen rujukan. AI akan membaca isi dokumen lalu mencari data numerik
          (anggaran, jumlah, persentase, dll) dan menghasilkan chart (pie, bar) dalam format SVG.
          Jika dokumen tidak memiliki data numerik, AI akan memberitahu.
        </p>

        <!-- Loading dokumen -->
        <div v-if="loadingDocs" class="flex items-center gap-2 text-xs text-bo-400 mb-3">
          <Loader2 :size="12" class="animate-spin" /> Memuat daftar dokumen...
        </div>

        <!-- Selector + tombol -->
        <div v-else class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-56">
            <label class="block text-xs text-bo-300 mb-1">
              Pilih Dokumen
              <span class="text-bo-500">({{ docs.length }} siap dipakai)</span>
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
            <BarChart2 v-else :size="14" />
            {{ loadingGenerate ? 'Menganalisis...' : 'Generate Infografis' }}
          </button>
        </div>

        <!-- Status pesan -->
        <div v-if="statusMsg" class="mt-3 flex items-center gap-1.5 text-xs"
          :class="statusMsg.type === 'ok' ? 'text-emerald-400' : statusMsg.type === 'warn' ? 'text-amber-400' : 'text-red-400'">
          <CheckCircle2 v-if="statusMsg.type === 'ok'" :size="12" />
          <Info v-else-if="statusMsg.type === 'warn'" :size="12" />
          <AlertCircle v-else :size="12" />
          {{ statusMsg.text }}
        </div>
      </div>

      <!-- Preview SVG / No Data -->
      <div class="bo-glass-card p-5 min-h-64 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h4 class="text-bo-100 text-sm font-semibold flex items-center gap-2">
            <BarChart2 :size="14" /> Hasil Visualisasi
          </h4>
          <div v-if="svgCode" class="flex gap-2">
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

        <!-- Loading -->
        <div v-if="loadingGenerate" class="flex-1 flex flex-col items-center justify-center text-bo-400 text-sm py-10">
          <Loader2 :size="28" class="animate-spin mb-3" />
          <p class="font-medium">AI sedang membaca dan menganalisis dokumen...</p>
          <p class="text-xs text-bo-500 mt-1">Langkah 1: ekstrak data numerik &rarr; Langkah 2: buat chart SVG</p>
          <p class="text-xs text-bo-500 mt-0.5">Proses memerlukan sekitar 15–45 detik</p>
        </div>

        <!-- Tidak ada data numerik -->
        <div v-else-if="noData" class="flex-1 flex flex-col items-center justify-center py-10 text-center">
          <div class="w-12 h-12 rounded-full bg-amber-500/15 flex items-center justify-center mb-3">
            <Info :size="22" class="text-amber-400" />
          </div>
          <p class="text-bo-200 font-medium text-sm">Tidak Ada Data Numerik</p>
          <p class="text-bo-400 text-xs mt-1 max-w-sm leading-relaxed">{{ noDataMsg }}</p>
          <p class="text-bo-500 text-xs mt-3">
            Coba pilih dokumen yang berisi anggaran, statistik, jumlah personel, atau data persentase.
          </p>
        </div>

        <!-- Belum generate -->
        <div v-else-if="!svgCode" class="flex-1 flex flex-col items-center justify-center text-bo-400 text-sm text-center py-10">
          <BarChart2 :size="36" class="mb-3 opacity-30" />
          <p>Belum ada visualisasi yang dihasilkan.</p>
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
  Sparkles, Loader2, BarChart2, CheckCircle2, AlertCircle,
  Info, Copy, Download
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
const noData          = ref(false)
const noDataMsg       = ref('')

onMounted(fetchDocs)

async function fetchDocs() {
  loadingDocs.value = true
  statusMsg.value   = null
  try {
    const all = await docApi.list()
    const arr = Array.isArray(all) ? all : (all?.items ?? [])
    docs.value = arr.filter(d => d.status === 'ready')
    if (docs.value.length === 0) {
      statusMsg.value = { type: 'warn', text: 'Belum ada dokumen yang siap. Upload dan proses dokumen terlebih dahulu.' }
    }
  } catch (e) {
    statusMsg.value = { type: 'err', text: `Gagal memuat daftar dokumen: ${e.message}` }
  } finally {
    loadingDocs.value = false
  }
}

async function handleGenerate() {
  if (!selectedId.value) return
  statusMsg.value       = null
  noData.value          = false
  noDataMsg.value       = ''
  loadingGenerate.value = true
  svgCode.value         = ''
  selectedJudul.value   = docs.value.find(d => d.id === selectedId.value)?.judul ?? 'dokumen'
  try {
    const res = await infografisApi.generate(selectedId.value)

    if (!res.has_data) {
      // Dokumen tidak punya data numerik
      noData.value    = true
      noDataMsg.value = res.message
      statusMsg.value = { type: 'warn', text: 'Tidak ditemukan data numerik yang bisa divisualisasikan.' }
      return
    }

    svgCode.value = res.svg || ''
    statusMsg.value = { type: 'ok', text: res.message || `Chart berhasil dibuat dari "${res.judul_dokumen}"` }
  } catch (e) {
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
  a.download = `chart-${selectedJudul.value.replace(/\s+/g, '-').toLowerCase()}.svg`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
