import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from '../src/router'

global.fetch = vi.fn()
global.URL.createObjectURL = vi.fn(() => 'http://example.com/test')
global.URL.revokeObjectURL = vi.fn()

export function setupTestApp() {
  const app = createApp({})
  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus)
  
  // 注册Element Plus图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
  
  return app
}

export function mountComponent(component, options = {}) {
  const app = setupTestApp()
  const wrapper = mount(component, {
    global: {
      plugins: [createPinia(), router, ElementPlus]
    },
    ...options
  })
  return wrapper
}
