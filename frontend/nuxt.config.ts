// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    devtools: { enabled: true },
    modules: ['@nuxt/ui', '@nuxtjs/tailwindcss', '@pinia/nuxt'],

    // Disable SSR for faster client-side navigation
    ssr: false,

    devServer: {
        host: '0.0.0.0',
        port: Number(process.env.NUXT_PORT) || 80
    },

    vite: {
        server: {
            hmr: {
                protocol: 'wss',
                host: 'frontend-web.mini-erp.orb.local',
                clientPort: 443
            },
            allowedHosts: ['frontend-web.mini-erp.orb.local', 'localhost', '.orb.local']
        },
        // Optimize build
        build: {
            transpile: ['vuedraggable'],
            cssCodeSplit: true,
            rollupOptions: {
                output: {
                    manualChunks: {
                        'vendor': ['vue', 'pinia'],
                    }
                }
            }
        }
    },

    colorMode: {
        preference: 'light'
    },

    app: {
        head: {
            link: [
                // Preconnect for faster font loading
                { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
                { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
                // Use font-display: swap for non-blocking font load
                { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap' }
            ]
        },
        // Page transition for smoother navigation
        pageTransition: { name: 'page', mode: 'out-in' }
    },

    runtimeConfig: {
        public: {
            apiBase: '/api'
        }
    },

    // Experimental features for performance
    experimental: {
        payloadExtraction: false,
    },

    // Route rules for performance
    routeRules: {
        // Cache static assets
        '/_nuxt/**': { headers: { 'cache-control': 'public, max-age=31536000, immutable' } },
        // Auth pages - no caching
        '/auth/**': { ssr: false },
    },

    compatibilityDate: '2025-01-01'
})
