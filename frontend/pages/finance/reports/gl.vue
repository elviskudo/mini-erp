<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">General Ledger Report</h1>
        <p class="text-xs text-gray-500">Detailed transaction history by account</p>
      </div>
      <UDropdown :items="exportItems">
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
      </UDropdown>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <UFormGroup label="Account" hint="Select account to view" :ui="{ hint: 'text-xs text-gray-400' }" class="w-56">
          <USelectMenu v-model="selectedAccount" :options="accountOptions" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        <UFormGroup label="Period" hint="Date range" :ui="{ hint: 'text-xs text-gray-400' }" class="w-44">
          <DatePicker v-model="dateRange" mode="range" />
        </UFormGroup>
        <UButton @click="fetchData" icon="i-heroicons-arrow-path" size="sm">Generate</UButton>
      </div>
    </UCard>

    <UCard v-if="selectedAccount" :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="p-3 flex justify-between items-center">
          <div>
            <h3 class="font-bold text-sm">{{ currentAccountName }}</h3>
            <p class="text-xs text-gray-500">{{ dateRange[0] || 'Start' }} to {{ dateRange[1] || 'End' }}</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-gray-500">Opening Balance</p>
            <p class="font-bold text-sm">{{ formatCurrency(openingBalance) }}</p>
          </div>
        </div>
      </template>
      <UTable :columns="columns" :rows="ledgerEntries" :loading="loading">
        <template #date-data="{ row }"><span class="text-xs">{{ formatDateShort(row.date) }}</span></template>
        <template #journal_number-data="{ row }"><span class="text-xs font-mono">{{ row.journal_number }}</span></template>
        <template #description-data="{ row }"><span class="text-xs">{{ row.description }}</span></template>
        <template #debit-data="{ row }">
          <span v-if="row.debit" class="text-green-600 text-xs font-medium">{{ formatCurrency(row.debit) }}</span>
          <span v-else class="text-xs text-gray-300">-</span>
        </template>
        <template #credit-data="{ row }">
          <span v-if="row.credit" class="text-red-600 text-xs font-medium">{{ formatCurrency(row.credit) }}</span>
          <span v-else class="text-xs text-gray-300">-</span>
        </template>
        <template #balance-data="{ row }">
          <span class="font-semibold text-xs">{{ formatCurrency(row.balance) }}</span>
        </template>
      </UTable>
      <div class="p-3 border-t">
        <div class="grid grid-cols-3 gap-4 text-center">
          <div><p class="text-xs text-gray-500">Total Debits</p><p class="font-bold text-green-600 text-sm">{{ formatCurrency(totalDebits) }}</p></div>
          <div><p class="text-xs text-gray-500">Total Credits</p><p class="font-bold text-red-600 text-sm">{{ formatCurrency(totalCredits) }}</p></div>
          <div><p class="text-xs text-gray-500">Closing Balance</p><p class="font-bold text-primary-700 text-sm">{{ formatCurrency(closingBalance) }}</p></div>
        </div>
      </div>
    </UCard>

    <UCard v-else class="text-center py-8 text-gray-500">
      <UIcon name="i-heroicons-document-magnifying-glass" class="w-10 h-10 mx-auto mb-3" />
      <p class="text-sm">Select an account to view its ledger</p>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const loading = ref(false)
const selectedAccount = ref('')
const dateRange = ref<string[]>([])
const openingBalance = ref(250000000)
const accounts = ref<any[]>([])
const ledgerEntries = ref<any[]>([])

const columns = [
  { key: 'date', label: 'Date' },
  { key: 'journal_number', label: 'Journal #' },
  { key: 'description', label: 'Description' },
  { key: 'debit', label: 'Debit' },
  { key: 'credit', label: 'Credit' },
  { key: 'balance', label: 'Balance' }
]

const accountOptions = computed(() => [{ label: 'Select Account', value: '' }, ...accounts.value.map(a => ({ label: `${a.code} - ${a.name}`, value: a.id }))])
const currentAccountName = computed(() => accounts.value.find(a => a.id === selectedAccount.value)?.name || '')
const totalDebits = computed(() => ledgerEntries.value.reduce((sum, e) => sum + (e.debit || 0), 0))
const totalCredits = computed(() => ledgerEntries.value.reduce((sum, e) => sum + (e.credit || 0), 0))
const closingBalance = computed(() => openingBalance.value + totalDebits.value - totalCredits.value)

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const fetchAccounts = async () => {
  try {
    const flattenTree = (nodes: any[]): any[] => nodes.flatMap(n => [n, ...(n.children ? flattenTree(n.children) : [])])
    accounts.value = flattenTree((await $api.get('/finance/coa')).data)
  } catch {
    accounts.value = [{ id: '1', code: '1111', name: 'Cash in Bank' }, { id: '2', code: '1211', name: 'Accounts Receivable' }]
  }
}

const fetchData = async () => {
  if (!selectedAccount.value) return
  loading.value = true
  try {
    const params: any = { account_id: selectedAccount.value }
    if (dateRange.value?.length === 2) { params.date_from = dateRange.value[0]; params.date_to = dateRange.value[1] }
    const res = await $api.get('/finance/reports/gl', { params })
    ledgerEntries.value = res.data.entries || []
    openingBalance.value = res.data.opening_balance || 0
  } catch {
    ledgerEntries.value = [
      { date: '2026-01-05', journal_number: 'JE-001', description: 'Sales Invoice INV-2026-001', debit: 25000000, credit: 0, balance: 275000000 },
      { date: '2026-01-06', journal_number: 'JE-002', description: 'Payment to Supplier', debit: 0, credit: 5000000, balance: 270000000 },
      { date: '2026-01-07', journal_number: 'JE-003', description: 'Payment from Customer', debit: 12000000, credit: 0, balance: 282000000 }
    ]
  } finally { loading.value = false }
}

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(ledgerEntries.value, 'gl_report', cols)
  else if (format === 'xlsx') exportToExcel(ledgerEntries.value, 'gl_report', cols)
  else exportToPDF(ledgerEntries.value, 'gl_report', cols, `General Ledger - ${currentAccountName.value}`)
}

watch(selectedAccount, () => { if (selectedAccount.value) fetchData() })
onMounted(() => fetchAccounts())
</script>
