import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// El front corre en 5173 y la API en 8000. El proxy evita CORS mientras se
// desarrolla; en produccion no hace falta, porque FastAPI sirve el build desde
// el mismo dominio.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // El puerto de la API en desarrollo. Se puede cambiar sin tocar el
      // codigo: PUERTO_API=8002 npm run dev. Sirve cuando Windows deja un
      // socket tomado por un proceso que ya murio y el puerto no se libera.
      '/api': {
        target: `http://127.0.0.1:${process.env.PUERTO_API ?? 8001}`,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        // three.js pesa mucho: en su propio trozo, para que el resto de la
        // aplicacion cargue sin esperarlo. En forma de funcion porque la de
        // objeto no encaja con los tipos de rollup en esta version.
        manualChunks(id: string) {
          if (id.includes('node_modules/three')) return 'three'
          return undefined
        },
      },
    },
  },
})
