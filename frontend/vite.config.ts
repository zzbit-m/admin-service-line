import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/',
  build: {
    outDir: '../public',
    emptyOutDir: false,
    rollupOptions: {
      input: {
        main: './liff-app.html'
      }
    }
  },
  server: {
    proxy: {
      '/auth': 'http://localhost:8001',
      '/requests': 'http://localhost:8001',
      '/admin': 'http://localhost:8001',
      '/resources': 'http://localhost:8001',
    }
  }
})
