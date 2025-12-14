import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to, from) => {
    const authStore = useAuthStore()

    // Initialize auth state from cookie if not already done
    if (!authStore.isAuthenticated) {
        authStore.initialize()
    }

    // Redirect to login if still not authenticated
    if (!authStore.isAuthenticated && to.path !== '/auth/login' && to.path !== '/auth/register') {
        return navigateTo('/auth/login')
    }
})
