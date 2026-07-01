import { createRouter, createWebHistory } from 'vue-router'
import ChatView  from '../views/ChatView.vue'
import ErrorPage from '../views/ErrorPage.vue'
import { config }    from '../config'
import { authStore } from '../stores/auth'

// Lazy-load backoffice pages
const LoginPage      = () => import('../views/backoffice/LoginPage.vue')
const AIManagement   = () => import('../views/backoffice/AIManagement.vue')

const routes = [
  // ── Public routes ──────────────────────────────────────────
  {
    path: '/',
    name: 'Home',
    component: ChatView
  },
  {
    path: '/error/:type',
    name: 'Error',
    component: ErrorPage,
    props: route => ({
      errorType: route.params.type,
      maintenanceETA: route.query.eta
    })
  },

  // ── Backoffice ──────────────────────────────────────────────
  {
    path: '/chatbot/backoffice/login',
    name: 'BackofficeLogin',
    component: LoginPage,
    meta: { guestOnly: true }   // redirect ke dashboard jika sudah login
  },
  {
    path: '/chatbot/backoffice',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'ai-management',
        name: 'BackofficeAIManagement',
        component: AIManagement,
      },
      // Tambahkan child route backoffice lain di sini
    ]
  },

  // ── Fallback ────────────────────────────────────────────────
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: ErrorPage,
    props: { errorType: '404' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// ── Navigation Guards ──────────────────────────────────────────
router.beforeEach((to, from, next) => {
  // 1. Maintenance mode
  if (config.maintenance.enabled && to.name !== 'Error') {
    return next({
      name: 'Error',
      params: { type: 'maintenance' },
      query: { eta: config.maintenance.eta }
    })
  }

  // 2. Protected: harus login
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next({
      name: 'BackofficeLogin',
      query: { redirect: to.fullPath }
    })
  }

  // 3. Guest only: kalau sudah login redirect ke dashboard
  if (to.meta.guestOnly && authStore.isLoggedIn) {
    return next({ name: 'BackofficeAIManagement' })
  }

  next()
})

export default router
