import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/mock',
      name: 'Mock',
      component: () => import('@/views/mock/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/mock/compare',
      name: 'MockCompare',
      component: () => import('@/views/mock/CompareRecords.vue'),
      meta: { requiresAuth: true, title: '对比记录' }
    },
    {
      path: '/api-test',
      name: 'ApiTest',
      component: () => import('@/views/api-test/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ui-test',
      name: 'UiTest',
      component: () => import('@/views/ui-test/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/testcase',
      name: 'TestCase',
      component: () => import('@/views/testcase/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/testcase/create',
      name: 'TestCaseCreate',
      component: () => import('@/views/testcase/CaseEditor.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/testcase/:id',
      name: 'TestCaseDetail',
      component: () => import('@/views/testcase/CaseDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/testcase/:id/edit',
      name: 'TestCaseEdit',
      component: () => import('@/views/testcase/CaseEditor.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// Auth guard
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false // Default to true

  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
