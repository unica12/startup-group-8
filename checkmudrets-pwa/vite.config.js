import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

const config = {
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/*.png'],
      manifest: {
        name: 'ЧекМудрец — Трекер расходов',
        short_name: 'ЧекМудрец',
        lang: 'ru',
        description: 'Сканируй чеки, отслеживай расходы, получай советы по экономии',
        theme_color: '#2E7D32',
        background_color: '#F7FAF5',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        importScripts: ['cleanup-auth-cache.js'],
      },
    }),
  ],
  server: {
    host: true,
    port: 5173,
  },
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_SUPABASE_')
  const key = env.VITE_SUPABASE_PUBLISHABLE_KEY
  if (key && !/^sb_publishable_[\w-]+$/.test(key)) {
    throw new Error('VITE_SUPABASE_PUBLISHABLE_KEY должен содержать только publishable key Supabase.')
  }
  const configuredUrl = env.VITE_SUPABASE_URL
  if (configuredUrl) {
    const url = URL.parse(configuredUrl)
    const local = url?.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)
    if (!url || (url.protocol !== 'https:' && !local) || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
      throw new Error('VITE_SUPABASE_URL должен содержать только базовый URL проекта.')
    }
  }
  return config
})
