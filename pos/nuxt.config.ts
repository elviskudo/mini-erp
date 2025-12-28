// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    devtools: { enabled: false },

    modules: [
        '@nuxt/ui',
        '@nuxtjs/tailwindcss',
        '@pinia/nuxt',
        '@nuxtjs/google-fonts'
    ],

    // Icon configuration - use Iconify CDN
    icon: {
        serverBundle: false,
        clientBundle: {
            scan: true
        }
    },

    googleFonts: {
        families: {
            Inter: [400, 500, 600, 700]
        },
        display: 'swap'
    },

    css: ['~/assets/css/main.css'],

    colorMode: {
        preference: 'light'
    },

    devServer: {
        host: '0.0.0.0',
        port: 3000
    },

    runtimeConfig: {
        public: {
            apiBase: '/api'
        }
    },

    // Proxy API calls to backend
    nitro: {
        routeRules: {
            '/api/**': { proxy: 'http://backend_api:8000/**' }
        }
    },

    vite: {
        server: {
            hmr: {
                protocol: 'ws',
                host: '0.0.0.0'
            },
            allowedHosts: ['pos-app.mini-erp.orb.local', 'localhost', '.orb.local']
        }
    },

    compatibilityDate: '2024-01-01'
})
