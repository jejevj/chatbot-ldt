<template>
  <div class="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
    <form @submit.prevent="handleSubmit" class="max-w-4xl mx-auto">
      <div class="flex gap-2 items-end">
        <textarea
          ref="textareaRef"
          v-model="input"
          :placeholder="editValue ? 'Edit pesan Anda...' : placeholder"
          :disabled="disabled"
          :maxlength="maxLength"
          rows="1"
          class="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none overflow-hidden"
          :class="{ 'ring-2 ring-yellow-500': editValue }"
          @keydown.enter.exact.prevent="handleSubmit"
          @keydown.shift.enter.exact="handleNewLine"
          @input="autoResize"
        />
        
        <button
          v-if="editValue"
          type="button"
          @click="handleCancelEdit"
          class="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Batal
        </button>
        
        <button
          v-if="editValue"
          type="submit"
          :disabled="!input.trim() || disabled"
          class="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
        >
          Kirim
        </button>
        
        <button
          v-else-if="isLoading"
          type="button"
          @click="$emit('cancel')"
          class="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
        >
          Batal
        </button>
        
        <button
          v-else
          type="submit"
          :disabled="!input.trim() || disabled"
          class="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
        >
          Kirim
        </button>
      </div>
      
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-2 text-right">
        {{ input.length }} / {{ maxLength }} • Enter untuk kirim, Shift+Enter untuk baris baru
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import config from '../config'

const props = defineProps({
  isLoading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: 'Ketik pertanyaan Anda...',
  },
  maxLength: {
    type: Number,
    default: config.ui.maxMessageLength,
  },
  editValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['submit', 'cancel', 'cancel-edit'])

const input = ref('')
const textareaRef = ref(null)

// Watch for edit value changes
import { watch } from 'vue'
watch(() => props.editValue, (newValue) => {
  if (newValue) {
    input.value = newValue
    nextTick(() => autoResize())
  }
})

const handleSubmit = () => {
  if (input.value.trim() && !props.disabled) {
    emit('submit', input.value.trim())
    input.value = ''
    resetTextarea()
  }
}

const handleCancelEdit = () => {
  input.value = ''
  emit('cancel-edit')
  resetTextarea()
}

const handleNewLine = (e) => {
  // Allow default behavior for Shift+Enter (add new line)
  // The textarea will handle it automatically
}

const autoResize = () => {
  const textarea = textareaRef.value
  if (!textarea) return
  
  // Reset height to auto to get the correct scrollHeight
  textarea.style.height = 'auto'
  
  // Set height based on content, max 200px (about 8 lines)
  const newHeight = Math.min(textarea.scrollHeight, 200)
  textarea.style.height = newHeight + 'px'
}

const resetTextarea = () => {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })
}
</script>
