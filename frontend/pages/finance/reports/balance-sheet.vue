<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Balance Sheet</h1>
        <p class="text-xs text-gray-500">Statement of financial position</p>
      </div>
      <div class="flex gap-2 items-center">
        <DatePicker v-model="asOfDate" placeholder="As of date" class="w-40" />
        <UButton @click="fetchData" icon="i-heroicons-arrow-path" size="sm">Generate</UButton>
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Assets -->
      <UCard>
        <template #header>
          <h3 class="font-bold text-sm">Assets</h3>
        </template>
        <div class="space-y-3">
          <div>
            <h4 class="font-semibold text-xs text-gray-600 border-b pb-1 mb-1">Current Assets</h4>
            <div v-for="item in currentAssets" :key="item.name" class="flex justify-between py-1 px-2 text-xs">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.amount) }}</span>
            </div>
            <div class="flex justify-between py-1.5 px-2 bg-gray-50 font-medium text-xs">
              <span>Total Current Assets</span>
              <span>{{ formatCurrency(totalCurrentAssets) }}</span>
            </div>
          </div>
          <div>
            <h4 class="font-semibold text-xs text-gray-600 border-b pb-1 mb-1">Non-Current Assets</h4>
            <div v-for="item in nonCurrentAssets" :key="item.name" class="flex justify-between py-1 px-2 text-xs">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.amount) }}</span>
            </div>
            <div class="flex justify-between py-1.5 px-2 bg-gray-50 font-medium text-xs">
              <span>Total Non-Current Assets</span>
              <span>{{ formatCurrency(totalNonCurrentAssets) }}</span>
            </div>
          </div>
        </div>
        <div class="mt-3 pt-3 border-t flex justify-between font-bold text-sm text-primary-700">
          <span>Total Assets</span>
          <span>{{ formatCurrency(totalAssets) }}</span>
        </div>
      </UCard>

      <!-- Liabilities & Equity -->
      <UCard>
        <template #header>
          <h3 class="font-bold text-sm">Liabilities & Equity</h3>
        </template>
        <div class="space-y-3">
          <div>
            <h4 class="font-semibold text-xs text-gray-600 border-b pb-1 mb-1">Current Liabilities</h4>
            <div v-for="item in currentLiabilities" :key="item.name" class="flex justify-between py-1 px-2 text-xs">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.amount) }}</span>
            </div>
            <div class="flex justify-between py-1.5 px-2 bg-gray-50 font-medium text-xs">
              <span>Total Current Liabilities</span>
              <span>{{ formatCurrency(totalCurrentLiabilities) }}</span>
            </div>
          </div>
          <div>
            <h4 class="font-semibold text-xs text-gray-600 border-b pb-1 mb-1">Equity</h4>
            <div v-for="item in equity" :key="item.name" class="flex justify-between py-1 px-2 text-xs">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.amount) }}</span>
            </div>
            <div class="flex justify-between py-1.5 px-2 bg-gray-50 font-medium text-xs">
              <span>Total Equity</span>
              <span>{{ formatCurrency(totalEquity) }}</span>
            </div>
          </div>
        </div>
        <div class="mt-3 pt-3 border-t flex justify-between font-bold text-sm text-primary-700">
          <span>Total Liabilities & Equity</span>
          <span>{{ formatCurrency(totalLiabilitiesEquity) }}</span>
        </div>
      </UCard>
    </div>

    <!-- Balance Check -->
    <UCard :class="totalAssets === totalLiabilitiesEquity ? 'bg-green-50' : 'bg-red-50'" :ui="{ body: { padding: 'p-3' } }">
      <div class="flex justify-center items-center text-sm">
        <span v-if="totalAssets === totalLiabilitiesEquity" class="text-green-700 font-semibold">✓ Balance sheet is balanced</span>
        <span v-else class="text-red-700 font-semibold">⚠️ Balance sheet is out of balance by {{ formatCurrency(Math.abs(totalAssets - totalLiabilitiesEquity)) }}</span>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const loading = ref(false)
const asOfDate = ref(new Date().toISOString().split('T')[0])

const currentAssets = ref([
  { name: 'Cash & Bank', amount: 340000000 },
  { name: 'Accounts Receivable', amount: 45000000 },
  { name: 'Inventory', amount: 120000000 },
  { name: 'Prepaid Expenses', amount: 10000000 }
])

const nonCurrentAssets = ref([
  { name: 'Property & Equipment', amount: 250000000 },
  { name: 'Accumulated Depreciation', amount: -50000000 },
  { name: 'Intangible Assets', amount: 20000000 }
])

const currentLiabilities = ref([
  { name: 'Accounts Payable', amount: 32500000 },
  { name: 'Accrued Expenses', amount: 15000000 },
  { name: 'Tax Payable', amount: 8000000 }
])

const equity = ref([
  { name: 'Capital Stock', amount: 500000000 },
  { name: 'Retained Earnings', amount: 80000000 },
  { name: 'Current Period Earnings', amount: 99500000 }
])

const totalCurrentAssets = computed(() => currentAssets.value.reduce((sum, i) => sum + i.amount, 0))
const totalNonCurrentAssets = computed(() => nonCurrentAssets.value.reduce((sum, i) => sum + i.amount, 0))
const totalAssets = computed(() => totalCurrentAssets.value + totalNonCurrentAssets.value)
const totalCurrentLiabilities = computed(() => currentLiabilities.value.reduce((sum, i) => sum + i.amount, 0))
const totalEquity = computed(() => equity.value.reduce((sum, i) => sum + i.amount, 0))
const totalLiabilitiesEquity = computed(() => totalCurrentLiabilities.value + totalEquity.value)

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/finance/reports/balance-sheet', { params: { as_of_date: asOfDate.value } })
    if (res.data) {
      currentAssets.value = res.data.current_assets || currentAssets.value
      nonCurrentAssets.value = res.data.non_current_assets || nonCurrentAssets.value
      currentLiabilities.value = res.data.current_liabilities || currentLiabilities.value
      equity.value = res.data.equity || equity.value
    }
  } catch { /* use mock */ }
  finally { loading.value = false }
}

const doExport = (format: string) => {
  const allItems = [
    ...currentAssets.value.map(a => ({ ...a, section: 'Current Assets' })),
    ...nonCurrentAssets.value.map(a => ({ ...a, section: 'Non-Current Assets' })),
    ...currentLiabilities.value.map(a => ({ ...a, section: 'Current Liabilities' })),
    ...equity.value.map(a => ({ ...a, section: 'Equity' }))
  ]
  const cols = [{ key: 'section', label: 'Section' }, { key: 'name', label: 'Account' }, { key: 'amount', label: 'Amount' }]
  if (format === 'csv') exportToCSV(allItems, 'balance_sheet', cols)
  else if (format === 'xlsx') exportToExcel(allItems, 'balance_sheet', cols)
  else exportToPDF(allItems, 'balance_sheet', cols, `Balance Sheet as of ${asOfDate.value}`)
}

onMounted(() => fetchData())
</script>
