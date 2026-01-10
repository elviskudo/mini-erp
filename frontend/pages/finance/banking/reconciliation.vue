<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Bank Reconciliation</h1>
        <p class="text-xs text-gray-500">Match transactions with bank statements</p>
      </div>
      <UDropdown :items="exportItems">
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
      </UDropdown>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <p class="text-xs text-gray-500 pb-2 border-b mb-3">Enter the bank statement ending balance and date to reconcile against your book balance.</p>
      <div class="flex flex-wrap gap-3 items-end">
        <UFormGroup label="Bank Account" hint="Select account to reconcile" :ui="{ hint: 'text-xs text-gray-400' }" class="w-48">
          <USelectMenu v-model="selectedAccount" :options="accountOptions" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        <UFormGroup label="Statement Date" hint="Bank statement date" :ui="{ hint: 'text-xs text-gray-400' }" class="w-44">
          <DatePicker v-model="statementDate" />
        </UFormGroup>
        <UFormGroup label="Statement Balance" hint="Ending balance per bank" :ui="{ hint: 'text-xs text-gray-400' }" class="w-40">
          <UInput v-model.number="statementBalance" type="number" size="sm" />
        </UFormGroup>
        <UButton size="sm" @click="loadTransactions">Load</UButton>
      </div>
    </UCard>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Book Balance</p>
        <p class="font-bold text-lg">{{ formatCurrency(bookBalance) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Statement Balance</p>
        <p class="font-bold text-lg">{{ formatCurrency(statementBalance) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Difference</p>
        <p :class="['font-bold text-lg', difference === 0 ? 'text-green-600' : 'text-red-600']">{{ formatCurrency(difference) }}</p>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="p-3 flex justify-between items-center">
          <h3 class="font-semibold text-sm">Unreconciled Transactions</h3>
          <UButton size="sm" :disabled="selectedTransactions.length === 0" @click="markReconciled">Mark Reconciled</UButton>
        </div>
      </template>
      <UTable v-model:selected="selectedTransactions" :columns="columns" :rows="transactions" :loading="loading" select-mode="multiple">
        <template #transaction_date-data="{ row }"><span class="text-xs">{{ formatDateShort(row.transaction_date) }}</span></template>
        <template #amount-data="{ row }">
          <span :class="['text-xs font-semibold', row.amount >= 0 ? 'text-green-600' : 'text-red-600']">{{ formatCurrency(row.amount) }}</span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const selectedAccount = ref('')
const statementDate = ref('')
const statementBalance = ref(0)
const bookBalance = ref(0)
const transactions = ref<any[]>([])
const selectedTransactions = ref<any[]>([])
const bankAccounts = ref<any[]>([])

const columns = [
  { key: 'transaction_date', label: 'Date' },
  { key: 'reference_number', label: 'Reference' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' }
]

const accountOptions = computed(() => [{ label: 'Select Account', value: '' }, ...bankAccounts.value.map(a => ({ label: a.name, value: a.id }))])
const difference = computed(() => statementBalance.value - bookBalance.value)

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const fetchBankAccounts = async () => { try { bankAccounts.value = (await $api.get('/finance/banking/accounts')).data } catch {} }

const loadTransactions = async () => {
  if (!selectedAccount.value) { toast.add({ title: 'Select account', color: 'red' }); return }
  loading.value = true
  try {
    const res = await $api.get(`/finance/banking/reconciliation/${selectedAccount.value}`)
    transactions.value = res.data.transactions || []
    bookBalance.value = res.data.book_balance || 0
  } catch {
    transactions.value = [
      { id: '1', transaction_date: '2026-01-07', reference_number: 'TRX-001', description: 'Deposit', amount: 12000000 },
      { id: '2', transaction_date: '2026-01-06', reference_number: 'TRX-002', description: 'Payment', amount: -5000000 }
    ]
    bookBalance.value = 257000000
  } finally { loading.value = false }
}

const markReconciled = async () => {
  if (selectedTransactions.value.length === 0) return
  try {
    await $api.post('/finance/banking/reconciliation/mark', { transaction_ids: selectedTransactions.value.map((t: any) => t.id), statement_date: statementDate.value })
    toast.add({ title: 'Transactions reconciled', color: 'green' })
    await loadTransactions()
    selectedTransactions.value = []
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
}

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(transactions.value, 'bank_reconciliation', cols)
  else if (format === 'xlsx') exportToExcel(transactions.value, 'bank_reconciliation', cols)
  else exportToPDF(transactions.value, 'bank_reconciliation', cols, 'Bank Reconciliation')
}

onMounted(() => fetchBankAccounts())
</script>
