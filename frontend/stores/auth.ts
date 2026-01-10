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
    // Regional settings
    region_code?: string
    locale?: string
    timezone?: string
    gmt_offset?: string
    gmt_offset_minutes?: number
    // Currency settings
    currency?: string
    currency_symbol?: string
    decimal_places?: number
    date_format?: string
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
            // Save tenant to cookie (full object for timezone persistence)
            const tenantCookie = useCookie('tenant_data', { maxAge: 60 * 60 * 24 * 7 })
            tenantCookie.value = JSON.stringify(tenant)
        },
        updateTenantSettings(settings: Partial<Tenant>) {
            if (this.tenant) {
                this.tenant = { ...this.tenant, ...settings }
                const tenantCookie = useCookie('tenant_data', { maxAge: 60 * 60 * 24 * 7 })
                tenantCookie.value = JSON.stringify(this.tenant)
            }
        },
        async loadTenantSettings() {
            // Load tenant settings from API on app init
            try {
                const { $api } = useNuxtApp()
                const res = await $api.get('/config/tenant-settings')
                if (res.data && this.tenant) {
                    this.updateTenantSettings({
                        region_code: res.data.region_code,
                        locale: res.data.locale,
                        timezone: res.data.timezone,
                        gmt_offset: res.data.gmt_offset,
                        gmt_offset_minutes: res.data.gmt_offset_minutes,
                        currency: res.data.currency_code,
                        currency_symbol: res.data.currency_symbol,
                        date_format: res.data.date_format
                    })
                }
            } catch (e) {
                console.error('Failed to load tenant settings:', e)
            }
        },
        logout() {
            this.token = null
            this.user = null
            this.tenantId = null
            this.tenant = null
            this.isAuthenticated = false
            const cookie = useCookie('auth_token')
            cookie.value = null
            const tenantCookie = useCookie('tenant_data')
            tenantCookie.value = null
            navigateTo('/auth/login')
        },
        initialize() {
            const cookie = useCookie('auth_token')
            if (cookie.value) {
                this.setToken(cookie.value as string)
            }
            // Restore full tenant object from cookie
            const tenantCookie = useCookie('tenant_data')
            if (tenantCookie.value) {
                try {
                    const tenant = typeof tenantCookie.value === 'string'
                        ? JSON.parse(tenantCookie.value)
                        : tenantCookie.value
                    this.tenant = tenant
                    this.tenantId = tenant.id
                } catch (e) {
                    console.error('Failed to parse tenant cookie:', e)
                }
            }
        }
    }
})

