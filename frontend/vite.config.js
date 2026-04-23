import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  base: '/chatbot/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3210,
    proxy: {
      '/chatbot-api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
