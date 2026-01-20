import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/devices',
      name: 'devices',
      component: () => import('../views/DeviceManagement.vue')
    },
    {
      path: '/ports',
      name: 'ports',
      component: () => import('../views/PortManagement.vue')
    },
    {
      path: '/vlans',
      name: 'vlans',
      component: () => import('../views/VLANManagement.vue')
    },
    {
      path: '/inspections',
      name: 'inspections',
      component: () => import('../views/InspectionManagement.vue')
    },
    {
      path: '/configurations',
      name: 'configurations',
      component: () => import('../views/ConfigurationManagement.vue')
    },
    {
      path: '/device-collection',
      name: 'device-collection',
      component: () => import('../views/DeviceCollection.vue')
    }
  ]
})

export default router
