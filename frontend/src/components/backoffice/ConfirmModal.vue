<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('update:modelValue', false)" />

      <!-- Modal -->
      <div class="bo-glass-card relative z-10 w-full max-w-sm mx-4 p-6">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
            <AlertTriangle :size="20" class="text-red-400" />
          </div>
          <div>
            <h3 class="text-bo-100 font-semibold text-base">{{ title }}</h3>
            <p class="text-bo-300 text-sm mt-1">{{ message }}</p>
          </div>
        </div>

        <div class="flex gap-3 mt-6 justify-end">
          <button
            @click="$emit('update:modelValue', false)"
            class="px-4 py-2 rounded-lg text-sm text-bo-200 hover:text-white hover:bg-white/10 transition"
          >
            Batal
          </button>
          <button
            @click="$emit('confirm'); $emit('update:modelValue', false)"
            class="bo-btn-danger px-4 py-2 rounded-lg text-sm font-medium"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { AlertTriangle } from 'lucide-vue-next'
defineProps({
  modelValue:   { type: Boolean, default: false },
  title:        { type: String,  default: 'Konfirmasi' },
  message:      { type: String,  default: 'Apakah Anda yakin?' },
  confirmLabel: { type: String,  default: 'Hapus' },
})
defineEmits(['update:modelValue', 'confirm'])
</script>
