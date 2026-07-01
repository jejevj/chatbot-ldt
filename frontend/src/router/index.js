import { createRouter, createWebHistory } from 'vue-router'
import ChatView  from '../views/ChatView.vue'
import ErrorPage from '../views/ErrorPage.vue'
import { config }    from '../config'
import { authStore } from '../stores/auth'

const LoginPage      = () => import('../views/backoffice/LoginPage.vue')
const DokumenRujukan = () => import('../views/backoffice/DokumenRujukan.vue')
const TanyaJawab     = () => import('../views/backoffice/TanyaJawab.vue')
const PelatihanAI    = () => import('../views/backoffice/PelatihanAI.vue')

const routes = [
  { path: '/', name: 'Home', component: ChatView },
  {
    path: '/error/:type', name: 'Error', component: ErrorPage,
    props: route => ({ errorType: route.params.type, maintenanceETA: route.query.eta })
  },

  // Backoffice
  {
    path: '/backoffice/login', name: 'BackofficeLogin',
    component: LoginPage, meta: { guestOnly: true }
  },
  {
    path: '/backoffice', meta: { requiresAuth: true },
    children: [
      { path: 'dokumen',   name: 'DokumenRujukan', component: DokumenRujukan },
      { path: 'tanya-jawab', name: 'TanyaJawab',  component: TanyaJawab },
      { path: 'pelatihan', name: 'PelatihanAI',   component: PelatihanAI },
    ]
  },

  { path: '/:pathMatch(.*)*', name: 'NotFound', component: ErrorPage, props: { errorType: '404' } }
]

const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })

router.beforeEach((to, from, next) => {
  if (config.maintenance.enabled && to.name !== 'Error')
    return next({ name: 'Error', params: { type: 'maintenance' }, query: { eta: config.maintenance.eta } })

  if (to.meta.requiresAuth && !authStore.isLoggedIn)
    return next({ name: 'BackofficeLogin', query: { redirect: to.fullPath } })

  if (to.meta.guestOnly && authStore.isLoggedIn)
    return next({ name: 'DokumenRujukan' })

  // redirect /backoffice ke halaman pertama
  if (to.path === '/backoffice') return next({ name: 'DokumenRujukan' })

  next()
})

export default router
