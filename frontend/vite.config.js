import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    strictPort: true,
    proxy: Object.fromEntries([1, 2, 3, 4].map((number) => [
      `/api/node${number}`,
      {
        target: `http://127.0.0.1:${8000 + number}`,
        rewrite: (path) => path.replace(`/api/node${number}`, ''),
      },
    ])),
  },
})
