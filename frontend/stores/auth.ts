import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'

interface User {
    id: string
    username: string
    role: string
    tenant_id?: string
    exp: number
}

interface Tenant {
    id: string
    name: string
    company_code?: string
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: null as string | null,
        user: null as User | null,
        tenantId: null as string | null,
        tenant: null as Tenant | null,
        isAuthenticated: false
    }),
    actions: {
        setToken(token: string) {
            this.token = token
            this.isAuthenticated = true
            try {
                const decoded = jwtDecode(token) as User & { tenant_id?: string }
                this.user = decoded
                // Set tenant from token if available
                if (decoded.tenant_id) {
                    this.tenantId = decoded.tenant_id
                }
            } catch (e) {
                this.user = null
            }
            // Save to cookie with 7 days expiry
            const cookie = useCookie('auth_token', { maxAge: 60 * 60 * 24 * 7 })
            cookie.value = token
        },
        setTenant(tenant: Tenant) {
            this.tenant = tenant
            this.tenantId = tenant.id
            // Save tenant to cookie
            const tenantCookie = useCookie('tenant_id')
            tenantCookie.value = tenant.id
        },
        logout() {
            this.token = null
            this.user = null
            this.tenantId = null
            this.tenant = null
            this.isAuthenticated = false
            const cookie = useCookie('auth_token')
            cookie.value = null
            const tenantCookie = useCookie('tenant_id')
            tenantCookie.value = null
            navigateTo('/auth/login')
        },
        initialize() {
            const cookie = useCookie('auth_token')
            if (cookie.value) {
                this.setToken(cookie.value as string)
            }
            // Restore tenant from cookie
            const tenantCookie = useCookie('tenant_id')
            if (tenantCookie.value) {
                this.tenantId = tenantCookie.value as string
            }
        }
    }
})
