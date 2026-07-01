<template>
  <div class="min-h-screen flex" style="background: linear-gradient(135deg, #1f1208 0%, #3d2710 40%, #5e3f1f 100%)">

    <!-- Sidebar -->
    <aside class="bo-sidebar w-60 flex flex-col z-20">
      <!-- Brand -->
      <div class="px-5 py-5 flex items-center gap-3 border-b border-white/10">
        <div class="w-8 h-8 rounded-lg bo-btn-primary flex items-center justify-center">
          <BotMessageSquare :size="18" class="text-white" />
        </div>
        <span class="font-bold text-bo-100 text-sm tracking-wide">Backoffice Admin</span>
      </div>

      <!-- Nav -->
      <nav class="flex-1 px-3 py-4 space-y-1">
        <router-link
          v-for="item in menu"
          :key="item.name"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-bo-200 hover:text-white hover:bg-white/10 transition-all"
          active-class="bg-white/15 text-white font-medium"
        >
          <component :is="item.icon" :size="17" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Logout -->
      <div class="px-3 py-4 border-t border-white/10">
        <button
          @click="handleLogout"
          class="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-red-300 hover:text-white hover:bg-red-500/20 transition-all"
        >
          <LogOut :size="17" />
          <span>Keluar</span>
        </button>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Topbar -->
      <header class="bo-topbar px-6 py-3.5 flex items-center justify-between">
        <h2 class="text-bo-100 font-semibold text-sm">{{ pageTitle }}</h2>
        <div class="flex items-center gap-2 text-sm text-bo-200">
          <UserCircle :size="16" />
          <span>{{ authStore.user?.nama_user || authStore.user?.username_user || 'Admin' }}</span>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { BotMessageSquare, LayoutDashboard, FileText, HelpCircle, MessageSquareWarning, LogOut, UserCircle } from 'lucide-vue-next'
import { authStore } from '../../stores/auth'

const router = useRouter()
const route  = useRoute()

const menu = [
  { name: 'ai-management', label: 'AI Management', icon: LayoutDashboard, to: { name: 'BackofficeAIManagement' } },
]

const pageTitle = computed(() => {
  const map = {
    BackofficeAIManagement: 'AI Management',
  }
  return map[route.name] || 'Backoffice'
})

function handleLogout() {
  authStore.logout()
  router.push({ name: 'BackofficeLogin' })
}
</script>
