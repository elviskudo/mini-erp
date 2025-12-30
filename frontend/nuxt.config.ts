// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    devtools: { enabled: true },
    modules: ['@nuxt/ui', '@nuxtjs/tailwindcss', '@pinia/nuxt'],
    devServer: {
        host: '0.0.0.0',
        port: Number(process.env.NUXT_PORT) || 80
    },
    vite: {
        server: {
            hmr: {
                protocol: 'ws',
                host: '0.0.0.0'
            },
            allowedHosts: ['frontend-web.mini-erp.orb.local', 'localhost', '.orb.local']
        }
    },
    colorMode: {
        preference: 'light'
    },
    app: {
        head: {
            link: [
                { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
                { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
                { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap' }
            ]
        }
    },
    runtimeConfig: {
        public: {
            apiBase: '/api'
        }
    },
    compatibilityDate: '2025-01-01'
})
