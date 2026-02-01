import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/setup.js'],
    include: ['**/*.test.js', '**/*.test.jsx', '**/*.test.vue'],
    exclude: ['node_modules', 'dist'],
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})
