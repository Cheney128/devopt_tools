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

  // 初始化认证状态
  if (!authStore.user && authStore.token) {
    try {
      await authStore.fetchCurrentUser()
    } catch (error) {
      // 获取用户信息失败，清除 token
      authStore.logout()
    }
  }

  const isLoggedIn = authStore.isLoggedIn

  // 1. 已登录用户访问登录页，重定向到首页
  if (to.path === '/login' && isLoggedIn) {
    next('/')
    return
  }

  // 2. 公开页面，直接访问
  if (to.meta.public) {
    next()
    return
  }

  // 3. 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!isLoggedIn) {
      // 未登录，重定向到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 4. 检查管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      ElMessage.error('权限不足，无法访问该页面')
      next('/')
      return
    }
  }

  next()
})

export default router
