import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/simulador-4q',
      name: 'simulator-4q',
      component: () => import('../views/Simulador4Q.vue')
    },
    {
      path: '/simulador-rendija',
      name: 'simulator-rendija',
      component: () => import('../views/DoubleSlitView.vue')
    },
    {
      path: '/simulador-teleport',
      name: 'simulator-teleport',
      component: () => import('../views/TeleportView.vue')
    },
    {
      path: '/simulador-grover',
      name: 'simulator-grover',
      component: () => import('../views/GroverView.vue')
    }
  ],
})

export default router
