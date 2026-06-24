import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1/chats/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
