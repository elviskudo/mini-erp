<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">AP Aging Report</h1>
        <p class="text-xs text-gray-500">Accounts payable aging analysis</p>
      </div>
      <div class="flex gap-2">
        <div class="w-40">
          <DatePicker v-model="asOfDate" placeholder="As of date" />
        </div>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="sm" @click="fetchAging">Refresh</UButton>
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <!-- Summary Cards with K, M format -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
      <UCard v-for="bucket in agingBuckets" :key="bucket.label" :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xs font-medium text-gray-500">{{ bucket.label }}</p>
          <p :class="['text-lg font-bold', bucket.color]">{{ formatCurrencyCompact(bucket.amount) }}</p>
          <p class="text-xs text-gray-400">{{ bucket.count }} bills</p>
        </div>
      </UCard>
    </div>

    <!-- Total Summary -->
    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex justify-between items-center">
        <span class="text-sm font-semibold text-gray-700">Total Outstanding</span>
        <span class="text-xl font-bold text-primary-600">{{ formatCurrencyCompact(totalOutstanding) }}</span>
      </div>
    </UCard>

    <!-- Vendor Breakdown Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="flex items-center justify-between p-3">
          <h3 class="font-semibold text-sm">Vendor Breakdown</h3>
          <UInput v-model="search" placeholder="Search vendor..." icon="i-heroicons-magnifying-glass" size="sm" class="w-48" />
        </div>
      </template>
      <UTable :columns="columns" :rows="filteredVendors" :loading="loading">
        <template #vendor-data="{ row }">
          <span class="font-medium text-xs">{{ row.vendor }}</span>
        </template>
        <template #current-data="{ row }">
          <span class="text-xs text-green-600">{{ formatCurrencyCompact(row.current) }}</span>
        </template>
        <template #days_1_30-data="{ row }">
          <span class="text-xs text-blue-600">{{ formatCurrencyCompact(row.days_1_30) }}</span>
        </template>
        <template #days_31_60-data="{ row }">
          <span class="text-xs text-yellow-600">{{ formatCurrencyCompact(row.days_31_60) }}</span>
        </template>
        <template #days_61_90-data="{ row }">
          <span class="text-xs text-orange-600">{{ formatCurrencyCompact(row.days_61_90) }}</span>
        </template>
        <template #over_90-data="{ row }">
          <span class="text-xs text-red-600">{{ formatCurrencyCompact(row.over_90) }}</span>
        </template>
        <template #total-data="{ row }">
          <span class="font-bold text-xs">{{ formatCurrencyCompact(row.total) }}</span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()

const loading = ref(false)
const search = ref('')
const asOfDate = ref(new Date().toISOString().split('T')[0])
const agingData = ref<any>({ buckets: [], vendors: [], total: 0 })

const columns = [
  { key: 'vendor', label: 'Vendor' },
  { key: 'current', label: 'Current' },
  { key: 'days_1_30', label: '1-30 Days' },
  { key: 'days_31_60', label: '31-60 Days' },
  { key: 'days_61_90', label: '61-90 Days' },
  { key: 'over_90', label: '> 90 Days' },
  { key: 'total', label: 'Total' }
]

const agingBuckets = computed(() => {
  const buckets = agingData.value.buckets || []
  const colors = ['text-green-600', 'text-blue-600', 'text-yellow-600', 'text-orange-600', 'text-red-600']
  return buckets.map((b: any, i: number) => ({
    label: b.label,
    amount: b.amount,
    count: b.count,
    color: colors[i] || 'text-gray-600'
  }))
})

const totalOutstanding = computed(() => agingData.value.total || 0)

const filteredVendors = computed(() => {
  const vendors = agingData.value.vendors || []
  if (!search.value) return vendors
  const s = search.value.toLowerCase()
  return vendors.filter((v: any) => v.vendor?.toLowerCase().includes(s))
})

const formatCurrencyCompact = (amount: number) => {
  return `Rp ${formatCompact(amount)}`
}

const exportItems = [[
  { label: 'Export CSV', icon: 'i-heroicons-document-text', click: () => doExport('csv') },
  { label: 'Export Excel', icon: 'i-heroicons-table-cells', click: () => doExport('xlsx') },
  { label: 'Export PDF', icon: 'i-heroicons-document', click: () => doExport('pdf') }
]]

const fetchAging = async () => {
  loading.value = true
  try {
    const res = await $api.get('/ap/aging', { params: { as_of_date: asOfDate.value } })
    agingData.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const doExport = (format: string) => {
  const exportCols = columns.map(c => ({ key: c.key, label: c.label }))
  const data = filteredVendors.value.map((v: any) => ({
    vendor: v.vendor,
    current: v.current,
    days_1_30: v.days_1_30,
    days_31_60: v.days_31_60,
    days_61_90: v.days_61_90,
    over_90: v.over_90,
    total: v.total
  }))
  
  if (format === 'csv') exportToCSV(data, 'ap_aging', exportCols)
  else if (format === 'xlsx') exportToExcel(data, 'ap_aging', exportCols)
  else if (format === 'pdf') exportToPDF(data, 'ap_aging', exportCols, 'AP Aging Report')
}

watch(asOfDate, () => { fetchAging() })

onMounted(() => {
  fetchAging()
})
</script>
