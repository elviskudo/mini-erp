<template>
  <div class="relative">
    <div v-if="showPrefix" class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
      <span class="text-gray-500 text-sm">{{ currencySymbol }}</span>
    </div>
    <UInput
      v-bind="$attrs"
      :model-value="displayValue"
      :class="{ 'pl-12': showPrefix }"
      @input="onInput"
      @blur="onBlur"
      @focus="onFocus"
      inputmode="numeric"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: number | string | null
  currency?: string  // IDR, USD, EUR, etc
  showPrefix?: boolean
  decimals?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 0,
  currency: 'IDR',
  showPrefix: true,
  decimals: 0
})

const emit = defineEmits(['update:modelValue'])

// Currency configurations
const currencyConfig: Record<string, { symbol: string; locale: string; decimals: number }> = {
  IDR: { symbol: 'Rp', locale: 'id-ID', decimals: 0 },
  USD: { symbol: '$', locale: 'en-US', decimals: 2 },
  EUR: { symbol: '€', locale: 'de-DE', decimals: 2 },
  SGD: { symbol: 'S$', locale: 'en-SG', decimals: 2 },
  MYR: { symbol: 'RM', locale: 'ms-MY', decimals: 2 },
  JPY: { symbol: '¥', locale: 'ja-JP', decimals: 0 },
  CNY: { symbol: '¥', locale: 'zh-CN', decimals: 2 },
  GBP: { symbol: '£', locale: 'en-GB', decimals: 2 },
  AUD: { symbol: 'A$', locale: 'en-AU', decimals: 2 },
  THB: { symbol: '฿', locale: 'th-TH', decimals: 2 }
}

const config = computed(() => currencyConfig[props.currency] || currencyConfig.IDR)
const currencySymbol = computed(() => config.value.symbol)
const decimalPlaces = computed(() => props.decimals ?? config.value.decimals)

const isFocused = ref(false)
const rawValue = ref('')

// Display formatted value when not focused
const displayValue = computed(() => {
  if (isFocused.value) {
    return rawValue.value
  }
  const num = parseNumber(props.modelValue)
  if (num === 0 && !props.modelValue) return ''
  return formatNumber(num)
})

// Parse string to number
const parseNumber = (value: number | string | null): number => {
  if (value === null || value === undefined || value === '') return 0
  if (typeof value === 'number') return value
  // Remove all non-numeric except decimal
  const cleaned = value.toString().replace(/[^\d.-]/g, '')
  return parseFloat(cleaned) || 0
}

// Format number with thousand separators
const formatNumber = (num: number): string => {
  return new Intl.NumberFormat(config.value.locale, {
    minimumFractionDigits: decimalPlaces.value,
    maximumFractionDigits: decimalPlaces.value
  }).format(num)
}

// Handle input - allow only digits and format
const onInput = (event: Event) => {
  const input = event.target as HTMLInputElement
  const value = input.value
  
  // Remove non-numeric except decimal point
  let cleaned = value.replace(/[^\d.]/g, '')
  
  // Handle multiple decimal points
  const parts = cleaned.split('.')
  if (parts.length > 2) {
    cleaned = parts[0] + '.' + parts.slice(1).join('')
  }
  
  rawValue.value = cleaned
  
  // Emit numeric value
  const numericValue = parseFloat(cleaned) || 0
  emit('update:modelValue', numericValue)
}

const onFocus = () => {
  isFocused.value = true
  // Show raw number without formatting
  const num = parseNumber(props.modelValue)
  rawValue.value = num > 0 ? num.toString() : ''
}

const onBlur = () => {
  isFocused.value = false
}

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  if (!isFocused.value) {
    rawValue.value = parseNumber(newVal).toString()
  }
})
</script>
