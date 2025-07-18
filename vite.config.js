import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5173', // Adjust to the backend server URL if needed
        changeOrigin: true,
      },
    },
  },
})
