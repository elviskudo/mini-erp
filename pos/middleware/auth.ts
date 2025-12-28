import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
    const authStore = useAuthStore()
    authStore.init()

    // Allow access to login page
    if (to.path === '/login') {
        if (authStore.isAuthenticated && authStore.canAccessPOS) {
            return navigateTo('/pos')
        }
        return
    }

    // Check authentication
    if (!authStore.isAuthenticated) {
        return navigateTo('/login')
    }

    // Check role access
    if (!authStore.canAccessPOS) {
        return navigateTo('/login?error=unauthorized')
    }
})
