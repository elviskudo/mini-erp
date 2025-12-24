/**
 * Currency composable - provides currency configuration from tenant settings API
 */
import { useAuthStore } from '~/stores/auth'

export interface CurrencyConfig {
    code: string
    symbol: string
    position: 'before' | 'after'
    thousandSeparator: string
    decimalSeparator: string
    decimals: number
}

// Global state for currency settings (singleton)
const currencyConfig = ref<CurrencyConfig>({
    code: 'IDR',
    symbol: 'Rp',
    position: 'before',
    thousandSeparator: '.',
    decimalSeparator: ',',
    decimals: 0
})
const isLoaded = ref(false)

export const useCurrency = () => {
    const authStore = useAuthStore()

    // Load settings from API
    const loadSettings = async () => {
        if (isLoaded.value || !authStore.token) return

        try {
            const response = await $fetch('/api/settings', {
                headers: { Authorization: `Bearer ${authStore.token}` }
            }) as any

            if (response) {
                currencyConfig.value = {
                    code: response.currency_code || 'IDR',
                    symbol: response.currency_symbol || 'Rp',
                    position: response.currency_position || 'before',
                    thousandSeparator: response.thousand_separator || '.',
                    decimalSeparator: response.decimal_separator || ',',
                    decimals: parseInt(response.decimal_places) || 0
                }
                isLoaded.value = true
            }
        } catch (e) {
            console.error('Failed to load currency settings', e)
        }
    }

    // Format number to currency display
    const formatCurrency = (value: number | null | undefined): string => {
        if (value === null || value === undefined) return '-'

        const cfg = currencyConfig.value

        // Format with decimals
        let formatted = value.toFixed(cfg.decimals)

        // Split into parts
        const parts = formatted.split('.')

        // Add thousand separators
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, cfg.thousandSeparator)

        // Join with decimal separator
        formatted = cfg.decimals > 0 ? parts.join(cfg.decimalSeparator) : parts[0]

        // Apply position
        return cfg.position === 'before'
            ? `${cfg.symbol} ${formatted}`
            : `${formatted} ${cfg.symbol}`
    }

    // Format number only (without symbol)
    const formatNumber = (value: number | null | undefined): string => {
        if (value === null || value === undefined) return '0'

        const cfg = currencyConfig.value
        let formatted = value.toFixed(cfg.decimals)
        const parts = formatted.split('.')
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, cfg.thousandSeparator)
        return cfg.decimals > 0 ? parts.join(cfg.decimalSeparator) : parts[0]
    }

    // Re-fetch settings when needed
    const reloadSettings = () => {
        isLoaded.value = false
        return loadSettings()
    }

    return {
        config: currencyConfig,
        formatCurrency,
        formatNumber,
        loadSettings,
        reloadSettings,
        isLoaded
    }
}
