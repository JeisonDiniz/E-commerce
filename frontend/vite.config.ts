import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Imagens de produto servidas pelo back-end (ver STORAGE_BACKEND
      // "local" em app/core/storage.py) — sem isso o dev server do Vite
      // não sabe para onde encaminhar /media e as fotos quebram em dev.
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})