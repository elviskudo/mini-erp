import { useAuthStore } from '~/stores/auth'

export const formatCurrency = (amount: number) => {
    const auth = useAuthStore()
    const currency = auth.user?.tenant?.currency || 'USD'

    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
    }).format(amount)
}

export const formatDate = (dateString: string) => {
    const auth = useAuthStore()
    const timezone = auth.user?.tenant?.timezone || 'UTC'

    if (!dateString) return '-'
    const date = new Date(dateString)

    return new Intl.DateTimeFormat('en-US', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: timezone,
    }).format(date)
}
