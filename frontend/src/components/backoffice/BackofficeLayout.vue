<template>
  <div class="min-h-screen flex" style="background: linear-gradient(135deg, #1f1208 0%, #3d2710 40%, #5e3f1f 100%)">

    <!-- Sidebar -->
    <aside class="bo-sidebar w-64 flex flex-col z-20 flex-shrink-0">
      <!-- Brand -->
      <div class="px-5 py-5 flex items-center gap-3 border-b border-white/10">
        <div class="w-8 h-8 rounded-lg bo-btn-primary flex items-center justify-center flex-shrink-0">
          <BotMessageSquare :size="18" class="text-white" />
        </div>
        <div>
          <p class="font-bold text-bo-100 text-sm leading-tight">Backoffice Admin</p>
          <p class="text-bo-400 text-xs">Sistem Chatbot Kemhan</p>
        </div>
      </div>

      <!-- Nav -->
      <nav class="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p class="text-bo-500 text-xs font-semibold uppercase tracking-widest px-3 pb-2 pt-1">Manajemen</p>

        <router-link
          v-for="item in menu"
          :key="item.name"
          :to="{ name: item.name }"
          class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-bo-300 hover:text-white hover:bg-white/10 transition-all group"
          active-class="bg-white/15 text-white font-medium shadow-inner"
        >
          <div
            class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
            :class="activeRoute === item.name ? 'bg-bo-700/60' : 'bg-white/5 group-hover:bg-white/10'"
          >
            <component :is="item.icon" :size="15" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="leading-tight truncate">{{ item.label }}</p>
            <p class="text-xs text-bo-500 leading-tight truncate">{{ item.desc }}</p>
          </div>
          <span
            v-if="item.beta"
            class="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/25 text-amber-300 font-semibold uppercase tracking-wider flex-shrink-0"
          >Beta</span>
        </router-link>
      </nav>

      <!-- User + Logout -->
      <div class="px-3 py-4 border-t border-white/10 space-y-0.5">
        <div class="flex items-center gap-3 px-3 py-2">
          <div class="w-7 h-7 rounded-full bg-bo-700 flex items-center justify-center flex-shrink-0">
            <UserCircle :size="15" class="text-bo-300" />
          </div>
          <span class="text-sm text-bo-200 truncate">{{ authStore.user?.nama_user || authStore.user?.username_user || 'Admin' }}</span>
        </div>
        <button
          @click="handleLogout"
          class="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-red-400 hover:text-white hover:bg-red-500/20 transition-all"
        >
          <div class="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
            <LogOut :size="15" />
          </div>
          Keluar
        </button>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">
      <!-- Topbar -->
      <header class="bo-topbar px-6 py-3.5 flex items-center justify-between flex-shrink-0">
        <div>
          <h2 class="text-bo-100 font-semibold text-sm">{{ currentMenu?.label }}</h2>
          <p class="text-bo-400 text-xs">{{ currentMenu?.desc }}</p>
        </div>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  BotMessageSquare, BookMarked, MessagesSquare, BrainCircuit,
  ListChecks, PanelsTopLeft, LogOut, UserCircle
} from 'lucide-vue-next'
import { authStore } from '../../stores/auth'

const router = useRouter()
const route  = useRoute()

const menu = [
  {
    name: 'DokumenRujukan',
    label: 'Dokumen Rujukan',
    desc: 'Upload & kelola dokumen sumber',
    icon: BookMarked,
  },
  {
    name: 'ManajemenFAQ',
    label: 'Manajemen FAQ',
    desc: 'Generate & kelola FAQ per dokumen',
    icon: ListChecks,
  },
  {
    name: 'GenerateInfografis',
    label: 'Generate Infografis',
    desc: 'Buat infografis SVG dari dokumen',
    icon: PanelsTopLeft,
    beta: true,
  },
  {
    name: 'TanyaJawab',
    label: 'Tanya Jawab',
    desc: 'Uji chatbot dengan dokumen',
    icon: MessagesSquare,
  },
  {
    name: 'PelatihanAI',
    label: 'Pelatihan AI',
    desc: 'Koreksi & latih ulang AI',
    icon: BrainCircuit,
  },
]

const activeRoute = computed(() => route.name)
const currentMenu = computed(() => menu.find(m => m.name === route.name))

function handleLogout() {
  authStore.logout()
  router.push({ name: 'BackofficeLogin' })
}
</script>
