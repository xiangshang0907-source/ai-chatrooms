import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/rooms': 'http://localhost:8000'
    }
  }
})