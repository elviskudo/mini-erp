import { defineStore } from 'pinia'

interface User {
    id: string
    username: string
    email: string
    role: string
    tenant_id: string
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null as User | null,
        token: null as string | null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        canAccessPOS: (state) => {
            const allowedRoles = ['ADMIN', 'MANAGER', 'CASHIER']
            return state.user && allowedRoles.includes(state.user.role)
        }
    },

    actions: {
        init() {
            if (process.client) {
                this.token = localStorage.getItem('pos_token')
                const userStr = localStorage.getItem('pos_user')
                if (userStr) {
                    try {
                        this.user = JSON.parse(userStr)
                    } catch (e) {
                        this.user = null
                    }
                }
            }
        },

        setAuth(token: string, user: User) {
            this.token = token
            this.user = user
            if (process.client) {
                localStorage.setItem('pos_token', token)
                localStorage.setItem('pos_user', JSON.stringify(user))
            }
        },

        logout() {
            this.token = null
            this.user = null
            if (process.client) {
                localStorage.removeItem('pos_token')
                localStorage.removeItem('pos_user')
            }
        }
    }
})
