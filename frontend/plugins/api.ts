import axios from 'axios'
import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin((nuxtApp) => {
    const config = useRuntimeConfig()

    // In server side, we might need full URL if not using proxy correctly, 
    // but Nuxt proxy usually handles relative paths from client well.
    // For SSR validation, usually we call backend on internal docker network url, 
    // but for simplicity let's rely on client-side mostly or relative path.

    const api = axios.create({
        baseURL: config.public.apiBase,
        headers: {
            'Content-Type': 'application/json'
        }
    })

    api.interceptors.request.use((config) => {
        const authStore = useAuthStore()

        // Add auth token
        if (authStore.token) {
            config.headers.Authorization = `Bearer ${authStore.token}`
        }

        // Add tenant ID for multi-tenancy (Iron Wall)
        if (authStore.tenantId) {
            config.headers['X-Tenant-ID'] = authStore.tenantId
        }

        return config
    })

    api.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response && error.response.status === 401) {
                const authStore = useAuthStore()
                authStore.logout()
            }
            return Promise.reject(error)
        }
    )

    return {
        provide: {
            api: api
        }
    }
})
