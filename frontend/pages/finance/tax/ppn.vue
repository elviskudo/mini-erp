<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">PPN / VAT Report</h1>
        <p class="text-xs text-gray-500">Value Added Tax summary and transactions</p>
      </div>
      <div class="flex gap-2">
        <USelectMenu v-model="selectedPeriod" :options="periodOptions" option-attribute="label" value-attribute="value" class="w-40" size="sm" />
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">PPN Keluaran (Output)</p>
          <p class="text-lg font-bold text-red-600">{{ formatCurrency(outputTax) }}</p>
          <p class="text-xs text-gray-400">From sales invoices</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">PPN Masukan (Input)</p>
          <p class="text-lg font-bold text-green-600">{{ formatCurrency(inputTax) }}</p>
          <p class="text-xs text-gray-400">From purchase invoices</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">Net Payable / (Refundable)</p>
          <p :class="['text-lg font-bold', netTax >= 0 ? 'text-red-600' : 'text-green-600']">
            {{ formatCurrency(netTax) }}
          </p>
          <p class="text-xs text-gray-400">{{ netTax >= 0 ? 'To be paid' : 'Refund available' }}</p>
        </div>
      </UCard>
    </div>

    <!-- Transactions Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="flex gap-2">
          <UButton :variant="activeTab === 'output' ? 'solid' : 'ghost'" size="sm" @click="activeTab = 'output'">Output Tax (Keluaran)</UButton>
          <UButton :variant="activeTab === 'input' ? 'solid' : 'ghost'" size="sm" @click="activeTab = 'input'">Input Tax (Masukan)</UButton>
        </div>
      </template>
      <UTable :columns="columns" :rows="activeTab === 'output' ? outputTransactions : inputTransactions" :loading="loading">
        <template #date-data="{ row }">
          <span class="text-xs">{{ row.date }}</span>
        </template>
        <template #tax_base-data="{ row }">
          <span class="text-xs">{{ formatCurrency(row.tax_base) }}</span>
        </template>
        <template #tax_amount-data="{ row }">
          <span class="font-semibold text-xs">{{ formatCurrency(row.tax_amount) }}</span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const loading = ref(false)
const selectedPeriod = ref('2026-01')
const activeTab = ref('output')

const periodOptions = [
  { label: 'January 2026', value: '2026-01' },
  { label: 'December 2025', value: '2025-12' },
  { label: 'November 2025', value: '2025-11' },
  { label: 'October 2025', value: '2025-10' }
]

const outputTax = ref(13750000)
const inputTax = ref(9350000)
const netTax = computed(() => outputTax.value - inputTax.value)

const columns = [
  { key: 'date', label: 'Date' },
  { key: 'invoice_number', label: 'Invoice #' },
  { key: 'counterparty', label: 'Customer/Vendor' },
  { key: 'tax_base', label: 'DPP' },
  { key: 'tax_amount', label: 'PPN' }
]

const outputTransactions = ref([
  { id: '1', date: '2026-01-05', invoice_number: 'INV-2026-001', counterparty: 'PT Customer Satu', tax_base: 25000000, tax_amount: 2750000 },
  { id: '2', date: '2026-01-03', invoice_number: 'INV-2026-002', counterparty: 'CV Pelanggan Dua', tax_base: 100000000, tax_amount: 11000000 }
])

const inputTransactions = ref([
  { id: '1', date: '2026-01-05', invoice_number: 'BILL-2026-001', counterparty: 'PT Supplier Utama', tax_base: 50000000, tax_amount: 5500000 },
  { id: '2', date: '2026-01-03', invoice_number: 'BILL-2026-002', counterparty: 'CV Bahan Baku', tax_base: 35000000, tax_amount: 3850000 }
])

const exportItems = [[
  { label: 'Export CSV', icon: 'i-heroicons-document-text', click: () => doExport('csv') },
  { label: 'Export Excel', icon: 'i-heroicons-table-cells', click: () => doExport('xlsx') },
  { label: 'Export PDF', icon: 'i-heroicons-document', click: () => doExport('pdf') }
]]

const doExport = (format: string) => {
  const data = activeTab.value === 'output' ? outputTransactions.value : inputTransactions.value
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  const filename = `ppn_${activeTab.value}_${selectedPeriod.value}`
  if (format === 'csv') exportToCSV(data, filename, cols)
  else if (format === 'xlsx') exportToExcel(data, filename, cols)
  else exportToPDF(data, filename, cols, `PPN ${activeTab.value === 'output' ? 'Keluaran' : 'Masukan'} - ${selectedPeriod.value}`)
}
</script>
