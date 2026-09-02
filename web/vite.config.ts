import path from "node:path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// 前端只认 /api 前缀，由 vite 代理到后端。
// 这样开发时没有跨域问题，部署时也只需把 /api 指到后端地址。
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(process.cwd(), "./src") },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8787", changeOrigin: true },
    },
  },
})
