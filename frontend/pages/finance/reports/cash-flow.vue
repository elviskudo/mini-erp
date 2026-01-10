<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Cash Flow Statement</h1>
        <p class="text-xs text-gray-500">Statement of cash flows for the period</p>
      </div>
      <div class="flex gap-2 items-center">
        <DatePicker v-model="dateRange" mode="range" placeholder="Select period" class="w-48" />
        <UButton @click="fetchData" icon="i-heroicons-arrow-path" size="sm">Generate</UButton>
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <UCard>
      <div class="space-y-4">
        <!-- Operating Activities -->
        <div>
          <h3 class="font-bold text-sm text-gray-800 border-b pb-1 mb-2">Cash Flows from Operating Activities</h3>
          <div v-for="item in operatingActivities" :key="item.name" class="flex justify-between py-1 px-2 hover:bg-gray-50 text-xs">
            <span>{{ item.name }}</span>
            <span :class="item.amount >= 0 ? 'text-green-600' : 'text-red-600'">{{ formatCurrency(item.amount) }}</span>
          </div>
          <div class="flex justify-between py-1.5 px-2 bg-blue-50 font-semibold text-blue-700 rounded text-xs mt-1">
            <span>Net Cash from Operating</span>
            <span>{{ formatCurrency(netOperating) }}</span>
          </div>
        </div>

        <!-- Investing Activities -->
        <div>
          <h3 class="font-bold text-sm text-gray-800 border-b pb-1 mb-2">Cash Flows from Investing Activities</h3>
          <div v-for="item in investingActivities" :key="item.name" class="flex justify-between py-1 px-2 hover:bg-gray-50 text-xs">
            <span>{{ item.name }}</span>
            <span :class="item.amount >= 0 ? 'text-green-600' : 'text-red-600'">{{ formatCurrency(item.amount) }}</span>
          </div>
          <div class="flex justify-between py-1.5 px-2 bg-purple-50 font-semibold text-purple-700 rounded text-xs mt-1">
            <span>Net Cash from Investing</span>
            <span>{{ formatCurrency(netInvesting) }}</span>
          </div>
        </div>

        <!-- Financing Activities -->
        <div>
          <h3 class="font-bold text-sm text-gray-800 border-b pb-1 mb-2">Cash Flows from Financing Activities</h3>
          <div v-for="item in financingActivities" :key="item.name" class="flex justify-between py-1 px-2 hover:bg-gray-50 text-xs">
            <span>{{ item.name }}</span>
            <span :class="item.amount >= 0 ? 'text-green-600' : 'text-red-600'">{{ formatCurrency(item.amount) }}</span>
          </div>
          <div class="flex justify-between py-1.5 px-2 bg-orange-50 font-semibold text-orange-700 rounded text-xs mt-1">
            <span>Net Cash from Financing</span>
            <span>{{ formatCurrency(netFinancing) }}</span>
          </div>
        </div>

        <!-- Summary -->
        <div class="space-y-1 pt-3 border-t">
          <div class="flex justify-between py-1 px-2 text-xs">
            <span>Net Increase in Cash</span>
            <span :class="['font-semibold', netChange >= 0 ? 'text-green-600' : 'text-red-600']">{{ formatCurrency(netChange) }}</span>
          </div>
          <div class="flex justify-between py-1 px-2 text-xs">
            <span>Beginning Cash Balance</span>
            <span>{{ formatCurrency(beginningBalance) }}</span>
          </div>
          <div class="flex justify-between py-2 px-3 bg-gray-100 rounded-lg font-bold text-sm mt-2">
            <span>Ending Cash Balance</span>
            <span class="text-primary-700">{{ formatCurrency(endingBalance) }}</span>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const loading = ref(false)
const dateRange = ref<string[]>(['2026-01-01', '2026-01-31'])

const operatingActivities = ref([
  { name: 'Net Income', amount: 77500000 },
  { name: 'Depreciation', amount: 2000000 },
  { name: 'Increase in Accounts Receivable', amount: -15000000 },
  { name: 'Increase in Inventory', amount: -10000000 },
  { name: 'Increase in Accounts Payable', amount: 8000000 }
])

const investingActivities = ref([
  { name: 'Purchase of Equipment', amount: -25000000 },
  { name: 'Sale of Old Equipment', amount: 5000000 }
])

const financingActivities = ref([
  { name: 'Loan Repayment', amount: -10000000 },
  { name: 'Dividends Paid', amount: -15000000 }
])

const beginningBalance = ref(322500000)

const netOperating = computed(() => operatingActivities.value.reduce((sum, i) => sum + i.amount, 0))
const netInvesting = computed(() => investingActivities.value.reduce((sum, i) => sum + i.amount, 0))
const netFinancing = computed(() => financingActivities.value.reduce((sum, i) => sum + i.amount, 0))
const netChange = computed(() => netOperating.value + netInvesting.value + netFinancing.value)
const endingBalance = computed(() => beginningBalance.value + netChange.value)

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/finance/reports/cash-flow', { params: { date_from: dateRange.value[0], date_to: dateRange.value[1] } })
    if (res.data) {
      operatingActivities.value = res.data.operating || operatingActivities.value
      investingActivities.value = res.data.investing || investingActivities.value
      financingActivities.value = res.data.financing || financingActivities.value
      beginningBalance.value = res.data.beginning_balance || beginningBalance.value
    }
  } catch { /* use mock */ }
  finally { loading.value = false }
}

const doExport = (format: string) => {
  const allItems = [
    ...operatingActivities.value.map(a => ({ ...a, section: 'Operating' })),
    ...investingActivities.value.map(a => ({ ...a, section: 'Investing' })),
    ...financingActivities.value.map(a => ({ ...a, section: 'Financing' }))
  ]
  const cols = [{ key: 'section', label: 'Activity' }, { key: 'name', label: 'Item' }, { key: 'amount', label: 'Amount' }]
  if (format === 'csv') exportToCSV(allItems, 'cash_flow', cols)
  else if (format === 'xlsx') exportToExcel(allItems, 'cash_flow', cols)
  else exportToPDF(allItems, 'cash_flow', cols, 'Cash Flow Statement')
}

onMounted(() => fetchData())
</script>
