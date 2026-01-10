import { useAuthStore } from '~/stores/auth'

// Fallback region config when tenant settings not available
const DEFAULT_CONFIG = {
    locale: 'id-ID',
    currency: 'IDR',
    currency_symbol: 'Rp',
    timezone: 'Asia/Jakarta',
    gmt_offset: 'GMT+7',
    gmt_offset_minutes: 420,
    decimal_places: 0
}

// Safe getter for tenant config from store
const getTenantConfig = () => {
    try {
        const auth = useAuthStore()
        const tenant = auth?.tenant

        if (tenant) {
            return {
                locale: tenant.locale || DEFAULT_CONFIG.locale,
                currency: tenant.currency || DEFAULT_CONFIG.currency,
                currency_symbol: tenant.currency_symbol || DEFAULT_CONFIG.currency_symbol,
                timezone: tenant.timezone || DEFAULT_CONFIG.timezone,
                gmt_offset: tenant.gmt_offset || DEFAULT_CONFIG.gmt_offset,
                gmt_offset_minutes: tenant.gmt_offset_minutes ?? DEFAULT_CONFIG.gmt_offset_minutes,
                decimal_places: tenant.decimal_places ?? DEFAULT_CONFIG.decimal_places
            }
        }
        return DEFAULT_CONFIG
    } catch {
        // Fallback if store not available (e.g., during SSR)
        return DEFAULT_CONFIG
    }
}


export const formatCurrency = (amount: number): string => {
    if (amount === null || amount === undefined || isNaN(amount)) return '-'
    try {
        const config = getTenantConfig()
        return new Intl.NumberFormat(config.locale, {
            style: 'currency',
            currency: config.currency,
            minimumFractionDigits: config.currency === 'JPY' ? 0 : 0,
            maximumFractionDigits: config.currency === 'JPY' ? 0 : 0,
        }).format(amount)
    } catch {
        return `IDR ${amount.toLocaleString()}`
    }
}

// Get currency symbol for compact display
export const getCurrencySymbol = (): string => {
    const config = getTenantConfig()
    return config.currency_symbol || 'Rp'
}

// Format with K, M, B suffix
export const formatCompact = (value: number): string => {
    if (value === null || value === undefined || isNaN(value)) return '0'
    if (value === 0) return '0'
    const absValue = Math.abs(value)
    const sign = value < 0 ? '-' : ''

    if (absValue >= 1_000_000_000) {
        return sign + (absValue / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B'
    } else if (absValue >= 1_000_000) {
        return sign + (absValue / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
    } else if (absValue >= 1_000) {
        return sign + (absValue / 1_000).toFixed(1).replace(/\.0$/, '') + 'K'
    }
    return sign + absValue.toString()
}

export const formatCurrencyCompact = (amount: number): string => {
    return `${getCurrencySymbol()} ${formatCompact(amount)}`
}

export const formatDate = (dateString: string): string => {
    if (!dateString) return '-'
    try {
        const config = getTenantConfig()
        const date = new Date(dateString)
        if (isNaN(date.getTime())) return '-'

        return new Intl.DateTimeFormat(config.locale, {
            dateStyle: 'medium',
            timeZone: config.timezone,
        }).format(date)
    } catch {
        return dateString
    }
}

export const formatDateTime = (dateString: string): string => {
    if (!dateString) return '-'
    try {
        const config = getTenantConfig()
        const date = new Date(dateString)
        if (isNaN(date.getTime())) return '-'

        const formatted = new Intl.DateTimeFormat(config.locale, {
            dateStyle: 'medium',
            timeStyle: 'short',
            timeZone: config.timezone,
        }).format(date)

        return `${formatted} (${config.gmt_offset})`
    } catch {
        return dateString
    }
}

// Get timezone display string
export const getTimezoneDisplay = (): string => {
    const config = getTenantConfig()
    return `${config.timezone} (${config.gmt_offset})`
}

// Export utilities
export const exportToCSV = (data: any[], filename: string, columns: { key: string, label: string }[]) => {
    const headers = columns.map(c => c.label).join(',')
    const rows = data.map(row =>
        columns.map(c => {
            const val = row[c.key]
            return typeof val === 'string' && val.includes(',') ? `"${val}"` : val
        }).join(',')
    )
    const csv = [headers, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    downloadBlob(blob, `${filename}.csv`)
}

export const exportToExcel = async (data: any[], filename: string, columns: { key: string, label: string }[]) => {
    const XLSX = await import('xlsx')
    const wsData = [
        columns.map(c => c.label),
        ...data.map(row => columns.map(c => row[c.key]))
    ]
    const ws = XLSX.utils.aoa_to_sheet(wsData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Data')
    XLSX.writeFile(wb, `${filename}.xlsx`)
}

export const exportToPDF = async (data: any[], filename: string, columns: { key: string, label: string }[], title: string) => {
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF()

    doc.setFontSize(16)
    doc.text(title, 14, 20)

    doc.setFontSize(10)
    let y = 35
    const cellWidth = (180 / columns.length)

    // Headers
    columns.forEach((col, i) => {
        doc.setFont('', 'bold')
        doc.text(col.label, 14 + (i * cellWidth), y)
    })
    y += 8

    // Data rows
    doc.setFont('', 'normal')
    data.forEach(row => {
        if (y > 280) {
            doc.addPage()
            y = 20
        }
        columns.forEach((col, i) => {
            const val = String(row[col.key] ?? '')
            doc.text(val.substring(0, 25), 14 + (i * cellWidth), y)
        })
        y += 6
    })

    doc.save(`${filename}.pdf`)
}

const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

