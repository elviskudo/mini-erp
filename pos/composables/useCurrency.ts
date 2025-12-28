// Currency utility composable - formats prices based on tenant settings
export const useCurrency = () => {
    const { $api } = useNuxtApp()

    const settings = useState<{
        currency_code: string
        currency_symbol: string
        currency_position: string
        decimal_separator: string
        thousand_separator: string
        decimal_places: string
    }>('currency_settings', () => ({
        currency_code: 'IDR',
        currency_symbol: 'Rp',
        currency_position: 'before',
        decimal_separator: ',',
        thousand_separator: '.',
        decimal_places: '0'
    }))

    const loaded = useState('currency_loaded', () => false)

    const loadSettings = async () => {
        if (loaded.value) return

        try {
            const res = await $api.get('/pos/settings')
            settings.value = res.data
            loaded.value = true
        } catch (e) {
            console.error('Failed to load currency settings:', e)
        }
    }

    const formatPrice = (value: number | null | undefined): string => {
        if (value === null || value === undefined) return '-'

        const decimals = parseInt(settings.value.decimal_places) || 0
        const parts = value.toFixed(decimals).split('.')

        // Format integer part with thousand separator
        let intPart = parts[0]
        const thousand = settings.value.thousand_separator
        intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, thousand)

        // Build final number
        let formatted = intPart
        if (decimals > 0 && parts[1]) {
            formatted += settings.value.decimal_separator + parts[1]
        }

        // Add currency symbol
        const symbol = settings.value.currency_symbol
        if (settings.value.currency_position === 'after') {
            return `${formatted} ${symbol}`
        }
        return `${symbol} ${formatted}`
    }

    return {
        settings,
        loadSettings,
        formatPrice
    }
}
