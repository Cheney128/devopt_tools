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
      path: '/backup-management',
      name: 'backup-management',
      component: () => import('../views/BackupManagement.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'backup-overview',
          component: () => import('../views/BackupManagement.vue')
        },
        {
          path: 'schedules',
          name: 'backup-schedules-tab',
          component: () => import('../views/BackupManagement.vue')
        },
        {
          path: 'monitoring',
          name: 'backup-monitoring-tab',
          component: () => import('../views/BackupManagement.vue')
        },
        {
          path: 'configs',
          name: 'backup-configs-tab',
          component: () => import('../views/BackupManagement.vue')
        },
        {
          path: 'git-configs',
          name: 'backup-git-configs-tab',
          component: () => import('../views/BackupManagement.vue')
        }
      ]
    },
    {
      path: '/device-collection',
      name: 'device-collection',
      component: () => import('../views/DeviceCollection.vue'),
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
    },
    {
      path: '/configurations',
      redirect: '/backup-management'
    },
    {
      path: '/backup-schedules',
      redirect: '/backup-management/schedules'
    },
    {
      path: '/monitoring',
      redirect: '/backup-management/monitoring'
    },
    {
      path: '/git-configs',
      redirect: '/backup-management/git-configs'
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  // 临时关闭登录验证 - 用于调试
  return next()
  
  // const authStore = useAuthStore()

  // if (!authStore.isInitialized && authStore.token) {
  //   await authStore.init()
  // }

  // const isLoggedIn = authStore.isLoggedIn

  // if (to.path === '/login' && isLoggedIn) {
  //   return next('/')
  // }

  // if (to.meta.public) {
  //   return next()
  // }

  // if (to.meta.requiresAuth) {
  //   if (!isLoggedIn) {
  //     return next({
  //       path: '/login',
  //       query: { redirect: to.fullPath }
  //     })
  //   }

  //   if (to.meta.requiresAdmin && !authStore.isAdmin) {
  //     ElMessage.error('权限不足，无法访问该页面')
  //     return next('/')
  //   }
  // }

  // next()
})

export default router
