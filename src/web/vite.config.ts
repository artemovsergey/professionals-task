import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Порт веб-клиента и прокси на API. Прокси обязателен: браузер сам
// отправляет запросы на 5173, а API живёт на 5080. Без прокси в консоли
// будет CORS-ошибка, а с прокси запрос уходит с того же origin и заголовки
// Access-Control не нужны.
const API_TARGET = process.env.VITE_API_TARGET ?? 'http://localhost:5080'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
        // Поток событий дашборда нельзя буферизовать: иначе обновления
        // придут пачками раз в минуту вместо событий по мере изменений.
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
              proxyRes.headers['x-accel-buffering'] = 'no'
            }
          })
        },
      },
    },
  },
  preview: {
    port: 4173,
  },
  build: {
    // recharts и jsPDF весят больше полутора мегабайт вместе. Клиент
    // запускается локально из одной сборки, поэтому дробить их на отдельные
    // чанки ради сети не имеет смысла — предупреждение о размере гасим явно,
    // чтобы в выводе сборки не оставалось ничего, кроме результата.
    chunkSizeWarningLimit: 1600,
  },
})
