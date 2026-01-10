<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">AR Aging Report</h1>
        <p class="text-xs text-gray-500">Accounts receivable aging analysis</p>
      </div>
      <div class="flex gap-2">
        <div class="w-40">
          <DatePicker v-model="asOfDate" />
        </div>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="sm" @click="fetchAging">Refresh</UButton>
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
      <UCard v-for="bucket in agingBuckets" :key="bucket.label" :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xs font-medium text-gray-500">{{ bucket.label }}</p>
          <p :class="['text-lg font-bold', bucket.color]">{{ formatCurrencyCompact(bucket.amount) }}</p>
          <p class="text-xs text-gray-400">{{ bucket.count }} invoices</p>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex justify-between items-center">
        <span class="text-sm font-semibold text-gray-700">Total Outstanding</span>
        <span class="text-xl font-bold text-primary-600">{{ formatCurrencyCompact(totalOutstanding) }}</span>
      </div>
    </UCard>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="flex items-center justify-between p-3">
          <h3 class="font-semibold text-sm">Customer Breakdown</h3>
          <UInput v-model="search" placeholder="Search customer..." icon="i-heroicons-magnifying-glass" size="sm" class="w-48" />
        </div>
      </template>
      <UTable :columns="columns" :rows="filteredCustomers" :loading="loading">
        <template #customer-data="{ row }"><span class="font-medium text-xs">{{ row.customer }}</span></template>
        <template #current-data="{ row }"><span class="text-xs text-green-600">{{ formatCurrencyCompact(row.current) }}</span></template>
        <template #days_1_30-data="{ row }"><span class="text-xs text-blue-600">{{ formatCurrencyCompact(row.days_1_30) }}</span></template>
        <template #days_31_60-data="{ row }"><span class="text-xs text-yellow-600">{{ formatCurrencyCompact(row.days_31_60) }}</span></template>
        <template #days_61_90-data="{ row }"><span class="text-xs text-orange-600">{{ formatCurrencyCompact(row.days_61_90) }}</span></template>
        <template #over_90-data="{ row }"><span class="text-xs text-red-600">{{ formatCurrencyCompact(row.over_90) }}</span></template>
        <template #total-data="{ row }"><span class="font-bold text-xs">{{ formatCurrencyCompact(row.total) }}</span></template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()

const loading = ref(false)
const search = ref('')
const asOfDate = ref(new Date().toISOString().split('T')[0])
const agingData = ref<any>({ buckets: [], customers: [], total: 0 })

const columns = [
  { key: 'customer', label: 'Customer' },
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
  return buckets.map((b: any, i: number) => ({ ...b, color: colors[i] }))
})

const totalOutstanding = computed(() => agingData.value.total || 0)
const filteredCustomers = computed(() => {
  const custs = agingData.value.customers || []
  if (!search.value) return custs
  return custs.filter((c: any) => c.customer?.toLowerCase().includes(search.value.toLowerCase()))
})

const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const fetchAging = async () => {
  loading.value = true
  try {
    const res = await $api.get('/ar/aging', { params: { as_of_date: asOfDate.value } })
    agingData.value = res.data
  } catch {
    agingData.value = {
      buckets: [
        { label: 'Current', amount: 25000000, count: 8 },
        { label: '1-30 Days', amount: 12000000, count: 4 },
        { label: '31-60 Days', amount: 5000000, count: 2 },
        { label: '61-90 Days', amount: 3000000, count: 1 },
        { label: '> 90 Days', amount: 2000000, count: 1 }
      ],
      customers: [
        { customer: 'PT Customer Satu', current: 15000000, days_1_30: 8000000, days_31_60: 3000000, days_61_90: 0, over_90: 0, total: 26000000 },
        { customer: 'CV Pelanggan Dua', current: 8000000, days_1_30: 3000000, days_31_60: 2000000, days_61_90: 3000000, over_90: 2000000, total: 18000000 }
      ],
      total: 47000000
    }
  } finally { loading.value = false }
}

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredCustomers.value, 'ar_aging', cols)
  else if (format === 'xlsx') exportToExcel(filteredCustomers.value, 'ar_aging', cols)
  else exportToPDF(filteredCustomers.value, 'ar_aging', cols, 'AR Aging Report')
}

watch(asOfDate, () => fetchAging())
onMounted(() => fetchAging())
</script>
