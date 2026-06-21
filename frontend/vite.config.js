import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { proxy: {
    '/v1/products': 'http://localhost:8001',
    '/v1/categories': 'http://localhost:8001',
    '/v1/cart': 'http://localhost:8002',
    '/v1/orders': 'http://localhost:8003',
    '/v1/auth': 'http://localhost:8004',
    '/v1/search': 'http://localhost:8005',
  }}
})
