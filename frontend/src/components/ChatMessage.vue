<template>
  <div :class="messageClass">
    <div :class="containerClass">
      <!-- Avatar (order changes based on role) -->
      <div :class="avatarClass" :style="avatarOrder">
        <div v-if="message.role === 'user'">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
        <img 
          v-else
          src="/ai-profile.png" 
          alt="AI Assistant"
          class="w-full h-full object-cover"
        />
      </div>

      <!-- Content -->
      <div :class="contentWrapperClass" :style="contentOrder">
        <div class="mb-1" :class="nameLabelAlign">
          <span class="text-xs font-medium" :class="nameClass">
            {{ message.role === 'user' ? 'Anda' : 'Asisten' }}
          </span>
        </div>
        
        <div :class="bubbleClass">
          <div v-html="formattedContent" class="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap"></div>
        </div>

        <!-- Sources -->
        <div v-if="message.sources && message.sources.length > 0" class="mt-3 space-y-2">
          <p class="text-xs font-medium text-gray-600 dark:text-gray-400">📚 Sumber Data:</p>
          <div class="space-y-2">
            <a
              v-for="(source, index) in message.sources"
              :key="index"
              :href="source.url"
              target="_blank"
              rel="noopener noreferrer"
              class="block p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <p class="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline">
                {{ source.judul }}
              </p>
              <div class="flex gap-2 mt-1">
                <span class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                  {{ source.kategori }}
                </span>
                <span class="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded">
                  {{ source.tipe }}
                </span>
              </div>
            </a>
          </div>
        </div>

        <!-- Timestamp -->
        <p class="text-xs text-gray-400 mt-2" :class="nameLabelAlign">
          {{ formatTime(message.timestamp) }}
          <button
            v-if="isLastUserMessage && message.role === 'user'"
            @click="emit('edit-message', message)"
            class="ml-2 text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
            title="Edit pesan"
          >
            ✏️ Edit
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  isLastUserMessage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit-message'])

// Configure marked
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

const messageClass = computed(() => {
  return props.message.role === 'user' ? 'py-4 flex justify-end' : 'py-4 flex justify-start'
})

const containerClass = computed(() => {
  return 'flex items-start gap-4 max-w-4xl'
})

const avatarOrder = computed(() => {
  return props.message.role === 'user' ? { order: 2 } : { order: 1 }
})

const contentOrder = computed(() => {
  return props.message.role === 'user' ? { order: 1 } : { order: 2 }
})

const nameLabelAlign = computed(() => {
  return props.message.role === 'user' ? 'text-right' : 'text-left'
})

const avatarClass = computed(() => {
  const base = 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md'
  return props.message.role === 'user'
    ? `${base} bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600 text-white`
    : `${base} bg-gradient-to-br from-purple-500 to-indigo-600 text-white`
})

const contentWrapperClass = computed(() => {
  // Check if content is short (likely single line)
  const isShortContent = props.message.content.length < 80 && !props.message.content.includes('\n')
  return isShortContent ? 'inline-block' : 'flex-1 min-w-0'
})

const nameClass = computed(() => {
  return props.message.role === 'user'
    ? 'text-blue-600 dark:text-blue-400'
    : 'text-purple-600 dark:text-purple-400'
})

const bubbleClass = computed(() => {
  const base = 'rounded-2xl px-4 py-3 shadow-sm'
  if (props.message.isError) {
    return `${base} bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800`
  }
  return props.message.role === 'user'
    ? `${base} bg-gradient-to-br from-blue-500 to-blue-600 text-white`
    : `${base} bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700`
})

const formattedContent = computed(() => {
  // For user messages, preserve line breaks more explicitly
  if (props.message.role === 'user') {
    // Escape HTML but preserve line breaks
    const escaped = props.message.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
      .replace(/\n/g, '<br>')
    return escaped
  }
  
  // For assistant messages, use markdown
  return marked(props.message.content)
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  // Parse timestamp and convert to local time
  const date = new Date(timestamp)
  
  // Check if date is valid
  if (isNaN(date.getTime())) return ''
  
  // Format to local time
  return date.toLocaleTimeString('id-ID', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
}
</script>
