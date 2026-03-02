import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue')
    },
    {
      path: '/mock',
      name: 'Mock',
      component: () => import('@/views/mock/index.vue')
    },
    {
      path: '/api-test',
      name: 'ApiTest',
      component: () => import('@/views/api-test/index.vue')
    },
    {
      path: '/ui-test',
      name: 'UiTest',
      component: () => import('@/views/ui-test/index.vue')
    }
  ]
})

export default router
