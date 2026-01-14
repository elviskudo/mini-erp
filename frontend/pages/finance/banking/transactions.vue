<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Bank Transactions</h1>
        <p class="text-xs text-gray-500">View and record bank transactions</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Transaction</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" />
        </div>
        <div class="w-48">
          <label class="block text-xs font-medium text-gray-600 mb-1">Account</label>
          <USelectMenu v-model="selectedAccount" :options="accountOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="Reference..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
        <UButton variant="ghost" size="sm" @click="clearFilters">Clear</UButton>
      </div>
    </UCard>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredTransactions" :loading="loading">
        <template #transaction_number-data="{ row }">
          <span class="font-medium text-primary-600 text-xs">{{ row.transaction_number }}</span>
        </template>
        <template #transaction_date-data="{ row }">
          <span class="text-xs">{{ formatDateShort(row.transaction_date) }}</span>
        </template>
        <template #amount-data="{ row }">
          <span :class="['text-xs font-semibold', row.amount >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ row.amount >= 0 ? '+' : '' }}{{ formatCurrency(row.amount) }}
          </span>
        </template>
        <template #running_balance-data="{ row }">
          <span class="font-medium text-xs">{{ formatCurrency(row.running_balance) }}</span>
        </template>
        <template #is_reconciled-data="{ row }">
          <UIcon :name="row.is_reconciled ? 'i-heroicons-check-circle' : 'i-heroicons-clock'" 
                 :class="row.is_reconciled ? 'text-green-500' : 'text-gray-400'" class="w-4 h-4" />
        </template>
      </UTable>
    </UCard>

    <FormSlideover v-model="showForm" title="New Transaction" :loading="saving" @submit="saveTransaction">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Record a deposit, withdrawal, or transfer for a bank account.</p>
        
        <UFormGroup label="Bank Account" required hint="Select the bank account for this transaction" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.bank_account_id" :options="accountOptions" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Date" required hint="Transaction date" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="form.transaction_date" />
          </UFormGroup>
          <UFormGroup label="Type" required hint="Deposit, withdrawal, transfer" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.transaction_type" :options="transactionTypes" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Amount" required hint="Positive for deposit, negative for withdrawal" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.amount" type="number" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Counterparty" hint="Person or company involved" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.counterparty_name" placeholder="Name" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Details about this transaction" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Reference" hint="Check number, transfer ref, etc." :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.reference_number" size="sm" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()
const route = useRoute()

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const selectedAccount = ref(route.query.account?.toString() || '')
const search = ref('')
const dateRange = ref<string[]>([])
const transactions = ref<any[]>([])
const bankAccounts = ref<any[]>([])

const columns = [
  { key: 'transaction_date', label: 'Date' },
  { key: 'transaction_number', label: 'Ref #' },
  { key: 'transaction_type', label: 'Type' },
  { key: 'counterparty_name', label: 'Counterparty' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' },
  { key: 'running_balance', label: 'Balance' },
  { key: 'is_reconciled', label: 'Recon' }
]

const transactionTypes = ['Deposit', 'Withdrawal', 'Transfer In', 'Transfer Out', 'Payment', 'Receipt', 'Bank Fee', 'Interest']
const accountOptions = computed(() => [{ label: 'All Accounts', value: '' }, ...bankAccounts.value.map(a => ({ label: a.name, value: a.id }))])

const form = reactive({ bank_account_id: '', transaction_date: '', transaction_type: 'Deposit', amount: 0, counterparty_name: '', description: '', reference_number: '' })

const filteredTransactions = computed(() => {
  let result = transactions.value
  // Account filter
  const accountId = typeof selectedAccount.value === 'object' ? selectedAccount.value?.value : selectedAccount.value
  if (accountId) result = result.filter((t: any) => t.bank_account_id === accountId)
  // Date range filter
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    if (startDate && endDate) {
      result = result.filter((t: any) => {
        if (!t.transaction_date) return false
        const tDate = t.transaction_date.split('T')[0]
        return tDate >= startDate && tDate <= endDate
      })
    }
  }
  // Search filter
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter((t: any) => 
      t.reference_number?.toLowerCase().includes(s) || 
      t.description?.toLowerCase().includes(s) ||
      t.transaction_number?.toLowerCase().includes(s) ||
      t.counterparty_name?.toLowerCase().includes(s)
    )
  }
  return result
})

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const fetchTransactions = async () => {
  loading.value = true
  try { transactions.value = (await $api.get('/finance/banking/transactions')).data }
  catch {
    transactions.value = [
      { id: '1', transaction_date: '2026-01-07', transaction_number: 'TRX-001', transaction_type: 'Deposit', counterparty_name: 'PT Customer', description: 'Payment INV-001', amount: 12000000, running_balance: 262000000, is_reconciled: false },
      { id: '2', transaction_date: '2026-01-06', transaction_number: 'TRX-002', transaction_type: 'Payment', counterparty_name: 'PT Supplier', description: 'Payment BILL-001', amount: -5000000, running_balance: 250000000, is_reconciled: true }
    ]
  } finally { loading.value = false }
}

const fetchBankAccounts = async () => { try { bankAccounts.value = (await $api.get('/finance/banking/accounts')).data } catch {} }

const openForm = () => {
  Object.assign(form, { bank_account_id: selectedAccount.value, transaction_date: new Date().toISOString().split('T')[0], transaction_type: 'Deposit', amount: 0, counterparty_name: '', description: '', reference_number: '' })
  showForm.value = true
}

const saveTransaction = async () => {
  if (!form.bank_account_id || !form.transaction_date || !form.amount) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try { await $api.post('/finance/banking/transactions', form); toast.add({ title: 'Transaction saved', color: 'green' }); showForm.value = false; await fetchTransactions() }
  catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const clearFilters = () => { selectedAccount.value = ''; search.value = ''; dateRange.value = [] }

const doExport = (format: string) => {
  const cols = columns.filter(c => c.key !== 'is_reconciled').map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredTransactions.value, 'bank_transactions', cols)
  else if (format === 'xlsx') exportToExcel(filteredTransactions.value, 'bank_transactions', cols)
  else exportToPDF(filteredTransactions.value, 'bank_transactions', cols, 'Bank Transactions')
}

onMounted(() => { fetchTransactions(); fetchBankAccounts() })
</script>
