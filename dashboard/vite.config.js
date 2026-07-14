import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Dev: the FastAPI backend runs on 8787; prod serves the built dashboard
    // same-origin, so fetch('/api/...') works identically in both.
    proxy: { '/api': 'http://localhost:8787' }
  }
})
