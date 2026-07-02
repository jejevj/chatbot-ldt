<template>
  <div class="min-h-screen flex items-center justify-center px-4"
       style="background: linear-gradient(135deg, #1f1208 0%, #3d2710 40%, #5e3f1f 100%)">

    <!-- Decorative blur blobs -->
    <div class="pointer-events-none fixed inset-0 overflow-hidden">
      <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-20" style="background: radial-gradient(circle, #d07f38, transparent 70%)"></div>
      <div class="absolute -bottom-32 -right-32 w-96 h-96 rounded-full opacity-15" style="background: radial-gradient(circle, #b8621e, transparent 70%)"></div>
    </div>

    <div class="bo-glass-card relative w-full max-w-md p-8">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bo-btn-primary mb-4">
          <BotMessageSquare :size="28" class="text-white" />
        </div>
        <h1 class="text-xl font-bold text-bo-100">Backoffice Admin</h1>
        <p class="text-bo-300 text-sm mt-1">Masuk untuk mengelola sistem chatbot</p>
      </div>

      <!-- Alert Error -->
      <div v-if="errorMsg" class="mb-5 flex items-start gap-3 bg-red-500/15 border border-red-500/30 text-red-300 text-sm rounded-xl px-4 py-3">
        <AlertCircle :size="16" class="mt-0.5 flex-shrink-0" />
        <span>{{ errorMsg }}</span>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-5">
        <!-- Username -->
        <div>
          <label class="block text-xs font-medium text-bo-200 mb-1.5 uppercase tracking-wide">Username</label>
          <div class="relative">
            <User :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-bo-400" />
            <input
              v-model="form.username"
              type="text"
              placeholder="Masukkan username"
              required
              autocomplete="username"
              class="bo-input w-full pl-9 pr-4 py-2.5 text-sm"
            />
          </div>
        </div>

        <!-- Password -->
        <div>
          <label class="block text-xs font-medium text-bo-200 mb-1.5 uppercase tracking-wide">Password</label>
          <div class="relative">
            <Lock :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-bo-400" />
            <input
              v-model="form.password"
              :type="showPass ? 'text' : 'password'"
              placeholder="Masukkan password"
              required
              autocomplete="current-password"
              class="bo-input w-full pl-9 pr-10 py-2.5 text-sm"
            />
            <button type="button" @click="showPass = !showPass"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-bo-400 hover:text-bo-200 transition">
              <Eye v-if="!showPass" :size="15" />
              <EyeOff v-else :size="15" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="bo-btn-primary w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 mt-2"
        >
          <Loader2 v-if="loading" :size="16" class="animate-spin" />
          <LogIn v-else :size="16" />
          <span>{{ loading ? 'Memproses...' : 'Masuk' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { BotMessageSquare, AlertCircle, User, Lock, Eye, EyeOff, LogIn, Loader2 } from 'lucide-vue-next'
import { authStore } from '../../stores/auth'
import { loginAdmin } from '../../services/authService'

const router = useRouter()
const form     = reactive({ username: '', password: '' })
const loading  = ref(false)
const errorMsg = ref('')
const showPass = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  loading.value  = true
  try {
    const data = await loginAdmin(form.username, form.password)
    authStore.login(data.token, data.user)
    router.push({ name: 'DokumenRujukan' })
  } catch (err) {
    errorMsg.value = err.message || 'Terjadi kesalahan, coba lagi'
  } finally {
    loading.value = false
  }
}
</script>
