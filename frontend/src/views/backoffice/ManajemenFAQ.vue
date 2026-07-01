<template>
  <BackofficeLayout>
    <div class="space-y-5">

      <!-- Selector Dokumen -->
      <div class="bo-glass-card p-5">
        <h3 class="text-bo-100 font-semibold text-sm mb-1 flex items-center gap-2">
          <ListChecks :size="15" /> Manajemen FAQ per Dokumen
        </h3>
        <p class="text-bo-400 text-xs mb-4">Pilih dokumen untuk melihat, generate, atau regenerate FAQ-nya.</p>

        <div class="flex flex-wrap gap-3 items-end">
          <!-- Custom Select Glassmorphism -->
          <div class="relative flex-1 min-w-56">
            <label class="block text-xs text-bo-300 mb-1">Pilih Dokumen</label>
            <button
              type="button"
              @click="dropdownOpen = !dropdownOpen"
              class="bo-input w-full px-3 py-2 text-sm text-left flex items-center justify-between gap-2"
            >
              <span :class="selectedDoc ? 'text-bo-100' : 'text-bo-500'" class="truncate">
                {{ selectedDoc ? selectedDoc.judul : '-- Pilih dokumen rujukan --' }}
              </span>
              <ChevronDown :size="14" class="flex-shrink-0 text-bo-400 transition-transform" :class="dropdownOpen ? 'rotate-180' : ''" />
            </button>

            <!-- Dropdown Panel -->
            <Transition
              enter-active-class="transition ease-out duration-150"
              enter-from-class="opacity-0 -translate-y-2"
              enter-to-class="opacity-100 translate-y-0"
              leave-active-class="transition ease-in duration-100"
              leave-from-class="opacity-100 translate-y-0"
              leave-to-class="opacity-0 -translate-y-2"
            >
              <div
                v-if="dropdownOpen"
                class="absolute z-50 mt-1 w-full rounded-xl overflow-hidden shadow-2xl border border-white/15"
                style="background: rgba(40,20,8,0.92); backdrop-filter: blur(16px);"
              >
                <!-- Search inside dropdown -->
                <div class="px-3 pt-3 pb-2">
                  <input
                    v-model="docSearch"
                    placeholder="Cari dokumen..."
                    class="w-full bg-white/10 text-bo-100 placeholder-bo-500 text-xs px-3 py-1.5 rounded-lg outline-none border border-white/10 focus:border-white/30"
                    @click.stop
                  />
                </div>
                <div class="max-h-52 overflow-y-auto">
                  <div v-if="loadingDocs" class="px-4 py-3 text-bo-400 text-xs text-center">
                    <Loader2 :size="12" class="animate-spin inline mr-1" /> Memuat...
                  </div>
                  <div v-else-if="filteredDocs.length === 0" class="px-4 py-3 text-bo-500 text-xs text-center">
                    Tidak ada dokumen ditemukan
                  </div>
                  <button
                    v-for="doc in filteredDocs"
                    :key="doc.id"
                    type="button"
                    @click="selectDoc(doc)"
                    class="w-full text-left px-4 py-2.5 text-sm flex items-center gap-3 transition-all"
                    :class="selectedDoc?.id === doc.id
                      ? 'bg-white/20 text-white'
                      : 'text-bo-200 hover:bg-white/10 hover:text-white'"
                  >
                    <div class="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                      :class="selectedDoc?.id === doc.id ? 'bg-amber-500/30' : 'bg-white/10'">
                      <FileText :size="12" :class="selectedDoc?.id === doc.id ? 'text-amber-300' : 'text-bo-400'" />
                    </div>
                    <div class="min-w-0">
                      <p class="truncate leading-tight">{{ doc.judul }}</p>
                      <p class="text-xs leading-tight" :class="selectedDoc?.id === doc.id ? 'text-amber-300/70' : 'text-bo-500'">{{ doc.tipe }}</p>
                    </div>
                    <Check v-if="selectedDoc?.id === doc.id" :size="13" class="ml-auto text-amber-400 flex-shrink-0" />
                  </button>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Tombol Aksi -->
          <template v-if="selectedDoc">
            <button
              v-if="faqList.length === 0"
              @click="generateFAQ"
              :disabled="actionLoading"
              class="bo-btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
            >
              <Loader2 v-if="actionLoading" :size="13" class="animate-spin" />
              <Sparkles v-else :size="13" />
              Generate FAQ
            </button>
            <button
              v-else
              @click="regenerateFAQ"
              :disabled="actionLoading"
              class="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 border border-amber-500/40 text-amber-300 hover:bg-amber-500/20 transition"
            >
              <Loader2 v-if="actionLoading" :size="13" class="animate-spin" />
              <RefreshCw v-else :size="13" />
              Regenerate FAQ
            </button>
          </template>
        </div>

        <!-- Alert Aksi -->
        <div v-if="actionMsg" class="mt-3 flex items-center gap-1.5 text-xs" :class="actionMsg.type === 'ok' ? 'text-emerald-400' : 'text-red-400'">
          <CheckCircle2 v-if="actionMsg.type === 'ok'" :size="12" />
          <AlertCircle  v-else :size="12" />
          {{ actionMsg.text }}
        </div>
      </div>

      <!-- List FAQ -->
      <div v-if="selectedDoc" class="bo-glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10">
          <span class="text-bo-100 font-semibold text-sm flex items-center gap-2">
            <HelpCircle :size="14" />
            FAQ — {{ selectedDoc.judul }}
            <span class="text-xs text-bo-400 font-normal">({{ faqList.length }} item)</span>
          </span>
          <button @click="loadFAQ" class="text-bo-300 hover:text-white transition">
            <RefreshCw :size="14" :class="loadingFAQ ? 'animate-spin' : ''" />
          </button>
        </div>

        <div v-if="loadingFAQ" class="p-10 text-center text-bo-400 text-sm">
          <Loader2 :size="20" class="animate-spin mx-auto mb-2" /> Memuat FAQ...
        </div>
        <div v-else-if="faqList.length === 0" class="p-10 text-center text-bo-400 text-sm">
          <HelpCircle :size="36" class="mx-auto mb-2 opacity-30" />
          <p>Belum ada FAQ untuk dokumen ini.</p>
          <p class="text-xs mt-1">Klik <strong class="text-amber-300">Generate FAQ</strong> untuk membuat FAQ otomatis.</p>
        </div>

        <!-- FAQ Accordion -->
        <div v-else class="divide-y divide-white/5">
          <div
            v-for="(faq, idx) in faqList"
            :key="faq.id"
            class="group"
          >
            <button
              type="button"
              @click="toggleFAQ(idx)"
              class="w-full flex items-start gap-3 px-5 py-3.5 text-left hover:bg-white/5 transition-all"
            >
              <div class="mt-0.5 w-6 h-6 rounded-md bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                <span class="text-amber-400 text-xs font-bold">{{ idx + 1 }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-bo-100 text-sm font-medium leading-snug">{{ faq.pertanyaan }}</p>
                <span class="text-xs text-bo-500 capitalize">{{ faq.kategori }}</span>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0 mt-0.5">
                <ChevronDown
                  :size="14"
                  class="text-bo-400 transition-transform duration-200"
                  :class="openIdx === idx ? 'rotate-180 text-amber-400' : ''"
                />
              </div>
            </button>

            <!-- Jawaban Panel -->
            <Transition
              enter-active-class="transition ease-out duration-150"
              enter-from-class="opacity-0 -translate-y-1"
              enter-to-class="opacity-100 translate-y-0"
              leave-active-class="transition ease-in duration-100"
              leave-from-class="opacity-100"
              leave-to-class="opacity-0"
            >
              <div v-if="openIdx === idx" class="px-5 pb-4">
                <div class="ml-9 p-3 rounded-xl text-sm text-bo-200 leading-relaxed"
                  style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08)">
                  {{ faq.jawaban }}
                </div>
                <div class="ml-9 mt-2 flex items-center justify-end">
                  <button
                    @click.stop="confirmDeleteFAQ(faq)"
                    class="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition px-2 py-1 rounded-lg hover:bg-red-500/10"
                  >
                    <Trash2 :size="11" /> Hapus
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <!-- Placeholder belum pilih -->
      <div v-else class="bo-glass-card p-12 text-center">
        <ListChecks :size="40" class="mx-auto mb-3 text-bo-600" />
        <p class="text-bo-400 text-sm">Pilih dokumen di atas untuk melihat atau generate FAQ-nya.</p>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <ConfirmModal v-model="showConfirm"
      title="Hapus FAQ"
      :message="`FAQ '${toDelete?.pertanyaan?.slice(0,60)}...' akan dihapus.`"
      confirm-label="Hapus"
      @confirm="deleteFAQ" />
  </BackofficeLayout>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  ListChecks, ChevronDown, FileText, Check, Sparkles,
  RefreshCw, HelpCircle, Loader2, AlertCircle, CheckCircle2,
  Trash2
} from 'lucide-vue-next'
import BackofficeLayout from '../../components/backoffice/BackofficeLayout.vue'
import ConfirmModal     from '../../components/backoffice/ConfirmModal.vue'
import { docApi, faqApi } from '../../services/backofficeApi'

// ── State ──────────────────────────────────────────────
const docs        = ref([])
const loadingDocs = ref(false)
const docSearch   = ref('')
const dropdownOpen = ref(false)
const selectedDoc  = ref(null)

const faqList    = ref([])
const loadingFAQ = ref(false)
const openIdx    = ref(null)

const actionLoading = ref(false)
const actionMsg     = ref(null)

const showConfirm = ref(false)
const toDelete    = ref(null)

// ── Computed ───────────────────────────────────────────
const filteredDocs = computed(() => {
  const q = docSearch.value.toLowerCase()
  return q ? docs.value.filter(d => d.judul.toLowerCase().includes(q)) : docs.value
})

// ── Close dropdown on outside click ───────────────────
function onOutsideClick(e) {
  if (!e.target.closest('.relative')) dropdownOpen.value = false
}
onMounted(async () => {
  document.addEventListener('click', onOutsideClick)
  loadingDocs.value = true
  try { docs.value = await docApi.list() } catch (e) { console.error(e) }
  finally { loadingDocs.value = false }
})
onBeforeUnmount(() => document.removeEventListener('click', onOutsideClick))

// ── Actions ────────────────────────────────────────────
function selectDoc(doc) {
  selectedDoc.value = doc
  dropdownOpen.value = false
  docSearch.value = ''
  actionMsg.value = null
  openIdx.value = null
  loadFAQ()
}

async function loadFAQ() {
  if (!selectedDoc.value) return
  loadingFAQ.value = true
  faqList.value = []
  try { faqList.value = await faqApi.listByDoc(selectedDoc.value.id) }
  catch (e) { console.error(e) }
  finally { loadingFAQ.value = false }
}

async function generateFAQ() {
  actionMsg.value = null
  actionLoading.value = true
  try {
    const res = await faqApi.generate(selectedDoc.value.id)
    actionMsg.value = { type: 'ok', text: `Berhasil generate ${res.generated} FAQ untuk "${res.judul_dokumen}"` }
    await loadFAQ()
  } catch (e) {
    actionMsg.value = { type: 'err', text: e.message }
  } finally {
    actionLoading.value = false
  }
}

async function regenerateFAQ() {
  actionMsg.value = null
  actionLoading.value = true
  try {
    const res = await faqApi.regenerate(selectedDoc.value.id)
    actionMsg.value = { type: 'ok', text: `Regenerated ${res.generated} FAQ untuk "${res.judul_dokumen}"` }
    openIdx.value = null
    await loadFAQ()
  } catch (e) {
    actionMsg.value = { type: 'err', text: e.message }
  } finally {
    actionLoading.value = false
  }
}

function toggleFAQ(idx) {
  openIdx.value = openIdx.value === idx ? null : idx
}

function confirmDeleteFAQ(faq) { toDelete.value = faq; showConfirm.value = true }
async function deleteFAQ() {
  try {
    await faqApi.delete(toDelete.value.id)
    await loadFAQ()
    actionMsg.value = { type: 'ok', text: 'FAQ berhasil dihapus' }
  } catch (e) {
    actionMsg.value = { type: 'err', text: e.message }
  }
}
</script>
