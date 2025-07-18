import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // historyApiFallback: true,
    port: 3173,

    // set up a proxy to redirect API calls to the backend server
    proxy: {
      '/api': {
        target: 'http://localhost:5173', // Adjust to the backend server URL in server.py
        changeOrigin: true,
      },
    },
  },
})
