import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import ErrorPage from '../views/ErrorPage.vue'
import { config } from '../config'

const routes = [
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

// Global navigation guard for maintenance mode
router.beforeEach((to, from, next) => {
  // Check maintenance mode
  if (config.maintenance.enabled && to.name !== 'Error') {
    next({
      name: 'Error',
      params: { type: 'maintenance' },
      query: { eta: config.maintenance.eta }
    })
  } else {
    next()
  }
})

export default router
