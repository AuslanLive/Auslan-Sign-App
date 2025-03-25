import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    historyApiFallback: true,
  },
  root: "src", // 👈 Set the root to 'src' if index.html is inside src/
  build: {
    outDir: "../dist", // 👈 Ensure output goes outside src/
  },
})
