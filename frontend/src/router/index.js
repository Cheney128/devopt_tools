import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/devices',
      name: 'devices',
      component: () => import('../views/DeviceManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ports',
      name: 'ports',
      component: () => import('../views/PortManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/vlans',
      name: 'vlans',
      component: () => import('../views/VLANManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/inspections',
      name: 'inspections',
      component: () => import('../views/InspectionManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/configurations',
      name: 'configurations',
      component: () => import('../views/ConfigurationManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/monitoring',
      name: 'monitoring',
      component: () => import('../views/BackupMonitoring.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/backup-schedules',
      name: 'backup-schedules',
      component: () => import('../views/BackupScheduleManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/device-collection',
      name: 'device-collection',
      component: () => import('../views/DeviceCollection.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/git-configs',
      name: 'git-configs',
      component: () => import('../views/GitConfigManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UserManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 等待初始化完成（只执行一次）
  if (!authStore.isInitialized && authStore.token) {
    await authStore.init()
  }

  const isLoggedIn = authStore.isLoggedIn

  // 1. 已登录用户访问登录页，重定向到首页
  if (to.path === '/login' && isLoggedIn) {
    return next('/')
  }

  // 2. 公开页面，直接访问
  if (to.meta.public) {
    return next()
  }

  // 3. 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!isLoggedIn) {
      return next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    }

    // 4. 检查管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      ElMessage.error('权限不足，无法访问该页面')
      return next('/')
    }
  }

  next()
})

export default router
