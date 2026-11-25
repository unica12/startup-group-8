import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

const pagesBase = '/startup-group-8/app/'

function pwa(base) {
  return VitePWA({
    registerType: 'autoUpdate',
    scope: base,
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
      start_url: base,
      scope: base,
      icons: [
        { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        { src: 'icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
      importScripts: ['cleanup-auth-cache.js'],
      navigateFallbackAllowlist: [new RegExp(`^${base}`)],
    },
  })
}

function isLoopback(hostname) {
  const name = hostname.replace(/\.$/, '')
  return ['localhost', '[::1]', '0.0.0.0'].includes(name) || name.startsWith('127.')
}

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const base = mode === 'production' ? pagesBase : '/'
  const publicBuild = command === 'build' && mode === 'production'
  const key = env.VITE_SUPABASE_PUBLISHABLE_KEY || ''
  if (key && !/^sb_publishable_[\w-]+$/.test(key)) {
    throw new Error('VITE_SUPABASE_PUBLISHABLE_KEY должен содержать только publishable key Supabase.')
  }
  let configuredUrl = env.VITE_SUPABASE_URL || ''
  if (configuredUrl) {
    const url = URL.parse(configuredUrl)
    const local = url && isLoopback(url.hostname)
    if (!url || (url.protocol !== 'https:' && !(url.protocol === 'http:' && local)) || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
      throw new Error('VITE_SUPABASE_URL должен содержать только базовый URL проекта.')
    }
    if (publicBuild && local) configuredUrl = ''
  }
  const api = URL.parse(env.VITE_API_URL || (publicBuild ? '' : 'http://localhost:8000'))
  const valid = api && ['http:', 'https:'].includes(api.protocol) && !api.username && !api.password && !api.search && !api.hash
    && (!publicBuild || (api.protocol === 'https:' && !isLoopback(api.hostname)))
  if (publicBuild && process.env.GITHUB_ACTIONS === 'true' && (!valid || !configuredUrl || !key)) {
    throw new Error('Для Pages задай VITE_API_URL и VITE_SUPABASE_URL с публичными HTTPS-адресами и VITE_SUPABASE_PUBLISHABLE_KEY.')
  }
  return {
    base,
    plugins: [react(), tailwindcss(), pwa(base)],
    server: { host: true, port: 5173 },
    envPrefix: [],
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(valid ? api.href : ''),
      'import.meta.env.VITE_SUPABASE_URL': JSON.stringify(configuredUrl),
      'import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY': JSON.stringify(key),
    },
  }
})
