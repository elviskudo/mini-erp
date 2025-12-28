import axios from 'axios'

export default defineNuxtPlugin(() => {
    const config = useRuntimeConfig()

    const api = axios.create({
        baseURL: config.public.apiBase,
        headers: {
            'Content-Type': 'application/json'
        }
    })

    // Add auth token to requests
    api.interceptors.request.use((config) => {
        const token = localStorage.getItem('pos_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    })

    // Handle auth errors
    api.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response?.status === 401) {
                localStorage.removeItem('pos_token')
                localStorage.removeItem('pos_user')
                navigateTo('/login')
            }
            return Promise.reject(error)
        }
    )

    return {
        provide: {
            api
        }
    }
})
