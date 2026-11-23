import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/*.png'],
      manifest: {
        name: 'ЧекМудрец — Трекер расходов',
        short_name: 'ЧекМудрец',
        description: 'Сканируй чеки, отслеживай расходы, получай советы по экономии',
        theme_color: '#0A2540',
        background_color: '#0A2540',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/.*\/receipts/,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-receipts', expiration: { maxEntries: 50, maxAgeSeconds: 300 } },
          },
          {
            urlPattern: /^https:\/\/.*\/stats/,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-stats', expiration: { maxEntries: 10, maxAgeSeconds: 300 } },
          },
        ],
      },
    }),
  ],
  server: {
    host: true,
    port: 5173,
  },
})
