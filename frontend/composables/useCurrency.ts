/**
 * Currency composable - provides currency configuration from user settings
 */
import { useAuthStore } from '~/stores/auth'

export interface CurrencyConfig {
    code: string
    symbol: string
    locale: string
    decimals: number
}

const currencyConfigs: Record<string, CurrencyConfig> = {
    IDR: { code: 'IDR', symbol: 'Rp', locale: 'id-ID', decimals: 0 },
    USD: { code: 'USD', symbol: '$', locale: 'en-US', decimals: 2 },
    EUR: { code: 'EUR', symbol: '€', locale: 'de-DE', decimals: 2 },
    SGD: { code: 'SGD', symbol: 'S$', locale: 'en-SG', decimals: 2 },
    MYR: { code: 'MYR', symbol: 'RM', locale: 'ms-MY', decimals: 2 },
    JPY: { code: 'JPY', symbol: '¥', locale: 'ja-JP', decimals: 0 },
    CNY: { code: 'CNY', symbol: '¥', locale: 'zh-CN', decimals: 2 },
    GBP: { code: 'GBP', symbol: '£', locale: 'en-GB', decimals: 2 },
    AUD: { code: 'AUD', symbol: 'A$', locale: 'en-AU', decimals: 2 },
    THB: { code: 'THB', symbol: '฿', locale: 'th-TH', decimals: 2 }
}

// Default currency from localStorage or config
const defaultCurrency = ref<string>('IDR')

export const useCurrency = () => {
    const authStore = useAuthStore()

    // Get currency from user settings or localStorage
    const currencyCode = computed(() => {
        // Check localStorage first (set in config)
        if (process.client) {
            const saved = localStorage.getItem('erp_currency')
            if (saved && currencyConfigs[saved]) {
                return saved
            }
        }
        return defaultCurrency.value
    })

    const config = computed<CurrencyConfig>(() => {
        return currencyConfigs[currencyCode.value] || currencyConfigs.IDR
    })

    // Format number to currency display
    const formatCurrency = (value: number | null | undefined): string => {
        if (value === null || value === undefined) return '-'
        const cfg = config.value
        return `${cfg.symbol} ${new Intl.NumberFormat(cfg.locale, {
            minimumFractionDigits: cfg.decimals,
            maximumFractionDigits: cfg.decimals
        }).format(value)}`
    }

    // Format number only (without symbol)
    const formatNumber = (value: number | null | undefined): string => {
        if (value === null || value === undefined) return '0'
        const cfg = config.value
        return new Intl.NumberFormat(cfg.locale, {
            minimumFractionDigits: cfg.decimals,
            maximumFractionDigits: cfg.decimals
        }).format(value)
    }

    // Set currency preference
    const setCurrency = (code: string) => {
        if (currencyConfigs[code]) {
            defaultCurrency.value = code
            if (process.client) {
                localStorage.setItem('erp_currency', code)
            }
        }
    }

    // Get all available currencies
    const availableCurrencies = computed(() => {
        return Object.entries(currencyConfigs).map(([code, cfg]) => ({
            label: `${cfg.symbol} - ${code}`,
            value: code
        }))
    })

    return {
        currencyCode,
        config,
        formatCurrency,
        formatNumber,
        setCurrency,
        availableCurrencies
    }
}
