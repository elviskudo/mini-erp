import { defineStore } from 'pinia'
import jwt_decode from 'jwt-decode'

interface User {
    id: string
    username: string
    role: string
    exp: number
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: null as string | null,
        user: null as User | null,
        isAuthenticated: false
    }),
    actions: {
        setToken(token: string) {
            this.token = token
            this.isAuthenticated = true
            try {
                this.user = jwt_decode(token)
            } catch (e) {
                this.user = null
            }
            // Save to cookie (simple version)
            const cookie = useCookie('auth_token')
            cookie.value = token
        },
        logout() {
            this.token = null
            this.user = null
            this.isAuthenticated = false
            const cookie = useCookie('auth_token')
            cookie.value = null
            navigateTo('/auth/login')
        },
        initialize() {
            const cookie = useCookie('auth_token')
            if (cookie.value) {
                this.setToken(cookie.value as string)
            }
        }
    }
})
