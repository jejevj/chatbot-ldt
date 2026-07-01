<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside class="w-56 bg-white border-r border-gray-200 flex flex-col">
      <div class="px-6 py-5 border-b border-gray-100">
        <span class="font-bold text-gray-800 text-base">Backoffice</span>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1">
        <router-link
          v-for="item in menu"
          :key="item.name"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition"
          active-class="bg-blue-50 text-blue-700 font-medium"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Logout -->
      <div class="px-3 py-4 border-t border-gray-100">
        <button
          @click="handleLogout"
          class="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-red-500 hover:bg-red-50 transition"
        >
          <span>🚪</span>
          <span>Keluar</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- Topbar -->
      <header class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div class="text-sm text-gray-500">
          Halo, <span class="font-medium text-gray-800">{{ user?.nama_user || user?.username || 'Admin' }}</span>
        </div>
      </header>

      <!-- Page Content -->
      <div class="flex-1 overflow-auto">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { authStore } from '../../stores/auth'

const router = useRouter()
const user   = authStore.user

const menu = [
  { name: 'ai-management', label: 'AI Management', icon: '🤖', to: { name: 'BackofficeAIManagement' } },
]

function handleLogout() {
  authStore.logout()
  router.push({ name: 'BackofficeLogin' })
}
</script>
