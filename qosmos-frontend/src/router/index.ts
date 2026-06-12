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
      path: '/simulador-2q',
      name: 'simulator-2q',
      component: () => import('../views/Simulator2Q.vue')
    },
    {
      path: '/simulador-rendija',
      name: 'simulator-rendija',
      component: () => import('../views/DoubleSlitView.vue')
    }
  ],
})

export default router
