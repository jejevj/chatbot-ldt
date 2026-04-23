<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 text-center">
      <!-- Error Icon -->
      <div class="mb-6">
        <div v-if="errorType === '404'" class="text-6xl mb-4">🔍</div>
        <div v-else-if="errorType === '500'" class="text-6xl mb-4">⚠️</div>
        <div v-else-if="errorType === 'maintenance'" class="text-6xl mb-4">🔧</div>
        <div v-else class="text-6xl mb-4">❌</div>
      </div>

      <!-- Error Title -->
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
        {{ errorTitle }}
      </h1>

      <!-- Error Message -->
      <p class="text-gray-600 dark:text-gray-300 mb-8">
        {{ errorMessage }}
      </p>

      <!-- Error Code -->
      <div v-if="errorCode" class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Kode Error: {{ errorCode }}
      </div>

      <!-- Actions -->
      <div class="space-y-3">
        <button
          @click="goHome"
          class="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          Kembali ke Beranda
        </button>
        
        <button
          v-if="errorType !== 'maintenance'"
          @click="goBack"
          class="w-full px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg font-medium transition-colors"
        >
          Kembali ke Halaman Sebelumnya
        </button>

        <button
          v-if="errorType === 'maintenance'"
          @click="checkStatus"
          class="w-full px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg font-medium transition-colors"
        >
          Cek Status Sistem
        </button>
      </div>

      <!-- Additional Info -->
      <div v-if="errorType === 'maintenance'" class="mt-6 text-sm text-gray-500 dark:text-gray-400">
        Estimasi waktu: {{ maintenanceETA || 'Segera' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  errorType: {
    type: String,
    default: '404' // 404, 500, maintenance, network
  },
  errorCode: {
    type: String,
    default: null
  },
  maintenanceETA: {
    type: String,
    default: null
  }
})

const router = useRouter()

const errorTitle = computed(() => {
  switch (props.errorType) {
    case '404':
      return 'Halaman Tidak Ditemukan'
    case '500':
      return 'Terjadi Kesalahan Server'
    case 'maintenance':
      return 'Sistem Sedang Maintenance'
    case 'network':
      return 'Koneksi Terputus'
    default:
      return 'Terjadi Kesalahan'
  }
})

const errorMessage = computed(() => {
  switch (props.errorType) {
    case '404':
      return 'Maaf, halaman yang Anda cari tidak ditemukan. Mungkin halaman telah dipindahkan atau dihapus.'
    case '500':
      return 'Terjadi kesalahan pada server. Tim kami sedang bekerja untuk memperbaikinya. Silakan coba lagi nanti.'
    case 'maintenance':
      return 'Sistem sedang dalam pemeliharaan untuk meningkatkan kualitas layanan. Mohon maaf atas ketidaknyamanannya.'
    case 'network':
      return 'Tidak dapat terhubung ke server. Periksa koneksi internet Anda dan coba lagi.'
    default:
      return 'Terjadi kesalahan yang tidak terduga. Silakan coba lagi atau hubungi administrator.'
  }
})

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

const checkStatus = () => {
  window.location.reload()
}
</script>
