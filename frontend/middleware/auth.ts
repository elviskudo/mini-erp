import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to, from) => {
    const authStore = useAuthStore()

    // Initialize auth state from cookie if not already done
    if (!authStore.isAuthenticated) {
        authStore.initialize()
    }

    // Public paths that don't require authentication
    const publicPaths = [
        '/auth/login',
        '/auth/register',
        '/auth/register-company',
        '/auth/join-company',
        '/auth/verify'
    ]

    const isPublicPath = publicPaths.some(path => to.path.startsWith(path))

    // Redirect to login if not authenticated and not on public path
    if (!authStore.isAuthenticated && !isPublicPath) {
        return navigateTo('/auth/login')
    }
})
