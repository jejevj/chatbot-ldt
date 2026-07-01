import { createRouter, createWebHistory } from 'vue-router'
import ChatView  from '../views/ChatView.vue'
import ErrorPage from '../views/ErrorPage.vue'
import { config }    from '../config'
import { authStore } from '../stores/auth'

// Lazy-load backoffice pages
const LoginPage    = () => import('../views/backoffice/LoginPage.vue')
const AIManagement = () => import('../views/backoffice/AIManagement.vue')

const routes = [
  // ── Public ───────────────────────────────────────────────────
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

  // ── Backoffice ───────────────────────────────────────────────
  {
    // URL aktual: /chatbot/backoffice/login (karena vite base = /chatbot/)
    path: '/backoffice/login',
    name: 'BackofficeLogin',
    component: LoginPage,
    meta: { guestOnly: true }
  },
  {
    path: '/backoffice',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'ai-management',
        name: 'BackofficeAIManagement',
        component: AIManagement,
      },
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

router.beforeEach((to, from, next) => {
  if (config.maintenance.enabled && to.name !== 'Error') {
    return next({
      name: 'Error',
      params: { type: 'maintenance' },
      query: { eta: config.maintenance.eta }
    })
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next({
      name: 'BackofficeLogin',
      query: { redirect: to.fullPath }
    })
  }

  if (to.meta.guestOnly && authStore.isLoggedIn) {
    return next({ name: 'BackofficeAIManagement' })
  }

  next()
})

export default router
