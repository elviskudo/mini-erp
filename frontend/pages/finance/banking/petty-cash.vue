<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Petty Cash</h1>
        <p class="text-xs text-gray-500">Manage petty cash expenses and replenishments</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-minus" size="sm" variant="outline" @click="openExpenseForm">Record Expense</UButton>
        <UButton icon="i-heroicons-plus" size="sm" @click="openReplenishForm">Replenish</UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Current Balance</p>
        <p class="font-bold text-xl text-green-600">{{ formatCurrencyCompact(currentBalance) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">This Month Expenses</p>
        <p class="font-bold text-lg text-red-600">{{ formatCurrencyCompact(monthlyExpenses) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Last Replenishment</p>
        <p class="font-bold text-lg">{{ formatCurrencyCompact(lastReplenishment) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Transactions</p>
        <p class="font-bold text-lg">{{ transactions.length }}</p>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="Description..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
        <UButton variant="ghost" size="sm" @click="clearFilters">Clear</UButton>
      </div>
    </UCard>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredTransactions" :loading="loading">
        <template #date-data="{ row }"><span class="text-xs">{{ formatDateShort(row.date) }}</span></template>
        <template #amount-data="{ row }">
          <span :class="['text-xs font-semibold', row.type === 'replenishment' ? 'text-green-600' : 'text-red-600']">
            {{ row.type === 'replenishment' ? '+' : '-' }}{{ formatCurrency(row.amount) }}
          </span>
        </template>
        <template #type-data="{ row }">
          <UBadge :color="row.type === 'replenishment' ? 'green' : 'orange'" variant="soft" size="xs">{{ row.type }}</UBadge>
        </template>
      </UTable>
    </UCard>

    <!-- Expense Form -->
    <FormSlideover v-model="showExpenseForm" title="Record Expense" :loading="saving" @submit="saveExpense">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Record a petty cash expense for small purchases or reimbursements.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Date" required hint="Date of expense" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="expenseForm.date" />
          </UFormGroup>
          <UFormGroup label="Amount" required hint="Expense amount" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="expenseForm.amount" type="number" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Category" hint="Type of expense for reporting" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="expenseForm.category" :options="expenseCategories" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" required hint="What was purchased or reimbursed" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="expenseForm.description" rows="2" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Requested By" hint="Employee who requested the expense" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="expenseForm.requested_by" size="sm" />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Replenish Form -->
    <FormSlideover v-model="showReplenishForm" title="Replenish Petty Cash" :loading="saving" @submit="saveReplenishment">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Add funds to petty cash from a bank account.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Date" required hint="Replenishment date" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="replenishForm.date" />
          </UFormGroup>
          <UFormGroup label="Amount" required hint="Amount to add" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="replenishForm.amount" type="number" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Source Account" hint="Bank account funds are withdrawn from" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="replenishForm.source_account_id" :options="bankAccounts" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Notes about this replenishment" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="replenishForm.description" rows="2" size="sm" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const showExpenseForm = ref(false)
const showReplenishForm = ref(false)
const search = ref('')
const dateRange = ref<string[]>([])
const transactions = ref<any[]>([])
const bankAccountsList = ref<any[]>([])

const currentBalance = ref(5000000)
const monthlyExpenses = ref(2500000)
const lastReplenishment = ref(3000000)

const columns = [
  { key: 'date', label: 'Date' },
  { key: 'type', label: 'Type' },
  { key: 'category', label: 'Category' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' },
  { key: 'requested_by', label: 'Requested By' }
]

const expenseCategories = ['Office Supplies', 'Transportation', 'Meals', 'Miscellaneous', 'Utilities', 'Cleaning']
const bankAccounts = computed(() => [{ label: 'Select', value: '' }, ...bankAccountsList.value.map(a => ({ label: a.name, value: a.id }))])

const expenseForm = reactive({ date: '', amount: 0, category: 'Office Supplies', description: '', requested_by: '' })
const replenishForm = reactive({ date: '', amount: 0, source_account_id: '', description: '' })

const filteredTransactions = computed(() => {
  let result = transactions.value
  // Search filter - search in multiple fields
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter((t: any) => 
      t.description?.toLowerCase().includes(s) ||
      t.category?.toLowerCase().includes(s) ||
      t.type?.toLowerCase().includes(s) ||
      t.requested_by?.toLowerCase().includes(s) ||
      t.transaction_number?.toLowerCase().includes(s)
    )
  }
  // Date range filter
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    if (startDate && endDate) {
      result = result.filter((t: any) => {
        if (!t.date) return false
        const tDate = t.date.split('T')[0]
        return tDate >= startDate && tDate <= endDate
      })
    }
  }
  return result
})

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`

const fetchTransactions = async () => {
  loading.value = true
  try { 
    const res = await $api.get('/finance/banking/petty-cash')
    // API returns { balance, transactions: [] }
    transactions.value = res.data.transactions || []
    currentBalance.value = res.data.balance || 0
    // Calculate monthly expenses
    const now = new Date()
    const thisMonth = transactions.value.filter((t: any) => {
      if (!t.date || t.type !== 'expense') return false
      const tDate = new Date(t.date)
      return tDate.getMonth() === now.getMonth() && tDate.getFullYear() === now.getFullYear()
    })
    monthlyExpenses.value = thisMonth.reduce((sum: number, t: any) => sum + (t.amount || 0), 0)
    // Get last replenishment
    const lastRep = transactions.value.find((t: any) => t.type === 'replenishment')
    lastReplenishment.value = lastRep?.amount || 0
  }
  catch {
    transactions.value = [
      { id: '1', date: '2026-01-07', type: 'expense', category: 'Office Supplies', description: 'Printer Paper', amount: 150000, requested_by: 'Admin' },
      { id: '2', date: '2026-01-06', type: 'expense', category: 'Transportation', description: 'Courier Service', amount: 75000, requested_by: 'Sales' },
      { id: '3', date: '2026-01-05', type: 'replenishment', category: '-', description: 'Monthly Replenishment', amount: 3000000, requested_by: 'Finance' }
    ]
  } finally { loading.value = false }
}

const fetchBankAccounts = async () => { try { bankAccountsList.value = (await $api.get('/finance/banking/accounts')).data } catch {} }

const openExpenseForm = () => {
  Object.assign(expenseForm, { date: new Date().toISOString().split('T')[0], amount: 0, category: 'Office Supplies', description: '', requested_by: '' })
  showExpenseForm.value = true
}

const openReplenishForm = () => {
  Object.assign(replenishForm, { date: new Date().toISOString().split('T')[0], amount: 0, source_account_id: '', description: 'Petty Cash Replenishment' })
  showReplenishForm.value = true
}

const saveExpense = async () => {
  if (!expenseForm.date || !expenseForm.amount || !expenseForm.description) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try { await $api.post('/finance/banking/petty-cash/expense', expenseForm); toast.add({ title: 'Expense recorded', color: 'green' }); showExpenseForm.value = false; await fetchTransactions() }
  catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const saveReplenishment = async () => {
  if (!replenishForm.date || !replenishForm.amount) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try { await $api.post('/finance/banking/petty-cash/replenish', replenishForm); toast.add({ title: 'Replenishment recorded', color: 'green' }); showReplenishForm.value = false; await fetchTransactions() }
  catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const clearFilters = () => { search.value = ''; dateRange.value = [] }

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredTransactions.value, 'petty_cash', cols)
  else if (format === 'xlsx') exportToExcel(filteredTransactions.value, 'petty_cash', cols)
  else exportToPDF(filteredTransactions.value, 'petty_cash', cols, 'Petty Cash Transactions')
}

onMounted(() => { fetchTransactions(); fetchBankAccounts() })
</script>
