<template>
  <div
    :class="sidebarClass"
    class="fixed left-0 top-0 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-transform duration-300 z-20 w-80"
  >
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
        Riwayat Chat
      </h2>
    </div>

    <!-- New Chat Button -->
    <div class="p-4 space-y-2">
      <button
        @click="$emit('new-chat')"
        class="w-full px-4 py-2.5 bg-transparent border-2 border-blue-500 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors font-medium"
      >
        + Chat Baru
      </button>
      
      <button
        v-if="sessions.length > 0"
        @click="$emit('delete-all-sessions')"
        class="w-full px-4 py-2.5 bg-transparent border-2 border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors font-medium text-sm"
      >
        🗑️ Hapus Semua Riwayat
      </button>
    </div>

    <!-- Sessions List -->
    <div class="flex-1 overflow-y-auto p-4 space-y-2">
      <div v-if="isLoading" class="text-center text-gray-500 dark:text-gray-400">
        Memuat...
      </div>
      
      <div v-else-if="sessions.length === 0" class="text-center text-gray-500 dark:text-gray-400 text-sm">
        Belum ada riwayat chat
      </div>
      
      <button
        v-for="session in sessions"
        :key="session.session_id"
        @click="$emit('select-session', session.session_id)"
        :class="sessionClass(session.session_id)"
        class="w-full text-left px-4 py-3 rounded-lg transition-colors group relative"
      >
        <p class="text-sm font-medium truncate pr-8">
          {{ session.title }}
        </p>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ formatDate(session.updated_at) }}
        </p>
        
        <button
          @click.stop="$emit('delete-session', session.session_id)"
          class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-opacity"
        >
          🗑️
        </button>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  sessions: {
    type: Array,
    default: () => [],
  },
  currentSessionId: {
    type: String,
    default: null,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close', 'new-chat', 'select-session', 'delete-session', 'delete-all-sessions'])

const sidebarClass = computed(() => {
  return props.isOpen
    ? 'translate-x-0'
    : '-translate-x-full'
})

const sessionClass = (sessionId) => {
  const base = 'relative'
  return sessionId === props.currentSessionId
    ? `${base} bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100`
    : `${base} hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-900 dark:text-gray-100`
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  
  // Parse as UTC and convert to local time
  const date = new Date(dateString)
  
  // Check if valid
  if (isNaN(date.getTime())) return ''
  
  const now = new Date()
  const diff = now - date
  
  if (diff < 86400000) { // Less than 24 hours
    return date.toLocaleTimeString('id-ID', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  } else if (diff < 604800000) { // Less than 7 days
    return date.toLocaleDateString('id-ID', { weekday: 'short' })
  } else {
    return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
  }
}
</script>
