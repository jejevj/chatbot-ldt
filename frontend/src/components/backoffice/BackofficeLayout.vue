import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { BotMessageSquare, BookMarked, MessagesSquare, BrainCircuit, ListChecks, PanelsTopLeft, LogOut, UserCircle } from 'lucide-vue-next'
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
    label: 'Beta: Infografis',
    desc: 'Generate infografis SVG dari dokumen',
    icon: PanelsTopLeft,
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

const activeRoute  = computed(() => route.name)
const currentMenu  = computed(() => menu.find(m => m.name === route.name))

function handleLogout() {
  authStore.logout()
  router.push({ name: 'BackofficeLogin' })
}
