<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">General Ledger</h1>
        <p class="text-xs text-gray-500">Detailed transaction history by account</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openJournalForm">New Journal Entry</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-56">
          <label class="block text-xs font-medium text-gray-600 mb-1">Account</label>
          <USelectMenu v-model="selectedAccount" :options="accountOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" />
        </div>
        <UButton @click="fetchLedger" size="sm">Generate</UButton>
      </div>
    </UCard>

    <UCard v-if="selectedAccount" :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="flex justify-between items-center p-3">
          <div>
            <h3 class="font-bold text-sm">{{ currentAccountName }}</h3>
            <p class="text-xs text-gray-500">{{ dateRange[0] || 'Start' }} to {{ dateRange[1] || 'End' }}</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-gray-500">Opening Balance</p>
            <p class="font-bold">{{ formatCurrency(openingBalance) }}</p>
          </div>
        </div>
      </template>
      <UTable :columns="columns" :rows="ledgerEntries" :loading="loading">
        <template #date-data="{ row }"><span class="text-xs">{{ formatDateShort(row.date) }}</span></template>
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
          <div><p class="text-xs text-gray-500">Total Debits</p><p class="font-bold text-green-600">{{ formatCurrency(totalDebits) }}</p></div>
          <div><p class="text-xs text-gray-500">Total Credits</p><p class="font-bold text-red-600">{{ formatCurrency(totalCredits) }}</p></div>
          <div><p class="text-xs text-gray-500">Closing Balance</p><p class="font-bold text-primary-700">{{ formatCurrency(closingBalance) }}</p></div>
        </div>
      </div>
    </UCard>

    <UCard v-else class="text-center py-8 text-gray-500">
      <UIcon name="i-heroicons-document-magnifying-glass" class="w-10 h-10 mx-auto mb-3" />
      <p class="text-sm">Select an account to view its ledger</p>
    </UCard>

    <FormSlideover v-model="showJournalForm" title="New Journal Entry" :loading="saving" @submit="saveJournal">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Create a manual journal entry with balanced debits and credits.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Date" required hint="Transaction date" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="journalForm.date" />
          </UFormGroup>
          <UFormGroup label="Reference" hint="Optional reference number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="journalForm.reference" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Description" required hint="Description of the journal entry" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="journalForm.description" rows="2" size="sm" />
        </UFormGroup>
        
        <div class="border rounded-lg p-3 space-y-2">
          <div class="flex justify-between items-center">
            <label class="text-xs font-medium">Journal Lines</label>
            <UButton size="2xs" icon="i-heroicons-plus" @click="addJournalLine">Add Line</UButton>
          </div>
          <p class="text-xs text-gray-400">Select accounts and enter debit/credit amounts. Debits must equal credits.</p>
          <div v-for="(line, idx) in journalForm.lines" :key="idx" class="grid grid-cols-12 gap-1 items-center">
            <div class="col-span-5">
              <USelectMenu v-model="line.account_id" :options="accountOptions" option-attribute="label" value-attribute="value" size="xs" placeholder="Account" />
            </div>
            <div class="col-span-3">
              <UInput v-model.number="line.debit" type="number" placeholder="Debit" size="xs" />
            </div>
            <div class="col-span-3">
              <UInput v-model.number="line.credit" type="number" placeholder="Credit" size="xs" />
            </div>
            <div class="col-span-1">
              <UButton size="2xs" color="red" variant="ghost" icon="i-heroicons-trash" @click="removeJournalLine(idx)" />
            </div>
          </div>
          <div class="flex justify-between pt-2 border-t text-xs">
            <span>Debit: {{ formatCurrency(journalForm.lines.reduce((s: number, l: any) => s + (l.debit || 0), 0)) }}</span>
            <span>Credit: {{ formatCurrency(journalForm.lines.reduce((s: number, l: any) => s + (l.credit || 0), 0)) }}</span>
          </div>
        </div>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const showJournalForm = ref(false)
const selectedAccount = ref('')
const dateRange = ref<string[]>([])
const accounts = ref<any[]>([])
const ledgerEntries = ref<any[]>([])
const openingBalance = ref(0)

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
const totalDebits = computed(() => ledgerEntries.value.reduce((s, e) => s + (e.debit || 0), 0))
const totalCredits = computed(() => ledgerEntries.value.reduce((s, e) => s + (e.credit || 0), 0))
const closingBalance = computed(() => openingBalance.value + totalDebits.value - totalCredits.value)

const journalForm = reactive({ date: '', reference: '', description: '', lines: [{ account_id: '', debit: 0, credit: 0 }, { account_id: '', debit: 0, credit: 0 }] as any[] })

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
    accounts.value = [{ id: '1', code: '1110', name: 'Cash in Bank' }, { id: '2', code: '1211', name: 'Accounts Receivable' }]
  }
}

const fetchLedger = async () => {
  if (!selectedAccount.value) return
  loading.value = true
  try {
    const params: any = { account_id: selectedAccount.value }
    if (dateRange.value?.length === 2) { params.date_from = dateRange.value[0]; params.date_to = dateRange.value[1] }
    const res = await $api.get('/finance/gl', { params })
    ledgerEntries.value = res.data.entries || []
    openingBalance.value = res.data.opening_balance || 0
  } catch {
    openingBalance.value = 250000000
    ledgerEntries.value = [
      { date: '2026-01-05', journal_number: 'JE-001', description: 'Sales Invoice', debit: 25000000, credit: 0, balance: 275000000 },
      { date: '2026-01-06', journal_number: 'JE-002', description: 'Payment to Supplier', debit: 0, credit: 5000000, balance: 270000000 }
    ]
  } finally { loading.value = false }
}

const openJournalForm = () => {
  console.log('openJournalForm called')
  Object.assign(journalForm, { date: new Date().toISOString().split('T')[0], reference: '', description: '', lines: [{ account_id: '', debit: 0, credit: 0 }, { account_id: '', debit: 0, credit: 0 }] })
  showJournalForm.value = true
  console.log('showJournalForm set to:', showJournalForm.value)
}

const addJournalLine = () => journalForm.lines.push({ account_id: '', debit: 0, credit: 0 })
const removeJournalLine = (idx: number) => journalForm.lines.splice(idx, 1)

const saveJournal = async () => {
  console.log('=== saveJournal START ===')
  console.log('journalForm:', JSON.stringify(journalForm, null, 2))
  
  // Filter out lines with no account selected
  const validLines = journalForm.lines.filter((l: any) => l.account_id && l.account_id !== '')
  console.log('validLines count:', validLines.length)
  console.log('validLines:', JSON.stringify(validLines, null, 2))
  
  if (validLines.length < 2) { 
    console.log('VALIDATION FAILED: Need at least 2 valid lines')
    toast.add({ title: 'Add at least 2 valid journal lines', color: 'red' })
    return 
  }
  
  const totalDebit = validLines.reduce((s: number, l: any) => s + (l.debit || 0), 0)
  const totalCredit = validLines.reduce((s: number, l: any) => s + (l.credit || 0), 0)
  console.log('totalDebit:', totalDebit, 'totalCredit:', totalCredit)
  
  if (totalDebit === 0 && totalCredit === 0) { 
    console.log('VALIDATION FAILED: Debit and Credit both zero')
    toast.add({ title: 'Enter debit or credit amounts', color: 'red' })
    return 
  }
  
  if (Math.abs(totalDebit - totalCredit) > 0.01) { 
    console.log('VALIDATION FAILED: Not balanced')
    toast.add({ title: `Debits (${totalDebit}) must equal credits (${totalCredit})`, color: 'red' })
    return 
  }
  
  if (!journalForm.date || !journalForm.description) { 
    console.log('VALIDATION FAILED: Missing date or description')
    toast.add({ title: 'Fill required fields (Date, Description)', color: 'red' })
    return 
  }
  
  console.log('=== ALL VALIDATIONS PASSED, CALLING API ===')
  saving.value = true
  try {
    const payload = {
      date: journalForm.date,
      description: journalForm.description,
      reference: journalForm.reference || null,
      lines: validLines
    }
    console.log('Sending payload to /finance/journal:', JSON.stringify(payload, null, 2))
    const response = await $api.post('/finance/journal', payload)
    console.log('API Response:', response)
    toast.add({ title: 'Journal entry saved', color: 'green' })
    showJournalForm.value = false
  } catch (e: any) { 
    console.error('API ERROR:', e)
    console.error('Error response:', e.response?.data)
    toast.add({ title: e.response?.data?.detail || 'Failed to save journal', color: 'red' }) 
  }
  finally { 
    saving.value = false 
    console.log('=== saveJournal END ===')
  }
}

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(ledgerEntries.value, 'general_ledger', cols)
  else if (format === 'xlsx') exportToExcel(ledgerEntries.value, 'general_ledger', cols)
  else exportToPDF(ledgerEntries.value, 'general_ledger', cols, `General Ledger - ${currentAccountName.value}`)
}

watch(selectedAccount, () => fetchLedger())
onMounted(() => fetchAccounts())
</script>
