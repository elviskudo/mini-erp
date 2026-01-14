<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Payment Receipts</h1>
        <p class="text-xs text-gray-500">Record customer payment receipts</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Receipt</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" />
        </div>
        <div class="w-48">
          <label class="block text-xs font-medium text-gray-600 mb-1">Customer</label>
          <USelectMenu v-model="customerFilter" :options="customerOptions" size="sm" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="Receipt number..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
        <UButton variant="ghost" size="sm" @click="clearFilters">Clear</UButton>
      </div>
    </UCard>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredReceipts" :loading="loading">
        <template #receipt_number-data="{ row }">
          <span class="font-medium text-primary-600 text-xs">{{ row.receipt_number }}</span>
        </template>
        <template #payment_date-data="{ row }">
          <span class="text-xs">{{ formatDateShort(row.payment_date) }}</span>
        </template>
        <template #amount-data="{ row }">
          <span class="font-semibold text-green-600 text-xs">{{ formatCurrency(row.amount) }}</span>
        </template>
      </UTable>
    </UCard>

    <FormSlideover v-model="showForm" title="Record Payment Receipt" :loading="saving" @submit="saveReceipt">
      <form class="space-y-4" @submit.prevent="saveReceipt">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Customer <span class="text-red-500">*</span></label>
          <USelectMenu v-model="form.customer_id" :options="customerOptions" size="sm" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Invoice (Optional)</label>
          <USelectMenu v-model="form.invoice_id" :options="invoiceOptions" size="sm" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Receipt Date <span class="text-red-500">*</span></label>
            <DatePicker v-model="form.payment_date" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Amount <span class="text-red-500">*</span></label>
            <UInput v-model.number="form.amount" type="number" size="sm" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Payment Method <span class="text-red-500">*</span></label>
            <USelectMenu v-model="form.payment_method" :options="paymentMethods" size="sm" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Deposit to Account</label>
            <USelectMenu v-model="form.bank_account_id" :options="bankAccounts" size="sm" />
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Reference Number</label>
          <UInput v-model="form.reference_number" size="sm" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Notes</label>
          <UTextarea v-model="form.notes" rows="2" size="sm" />
        </div>
      </form>
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
const search = ref('')
const customerFilter = ref('')
const dateRange = ref<string[]>([])
const receipts = ref<any[]>([])
const customers = ref<any[]>([])
const invoicesList = ref<any[]>([])
const bankAccountsList = ref<any[]>([])

const columns = [
  { key: 'receipt_number', label: 'Receipt #' },
  { key: 'customer_name', label: 'Customer' },
  { key: 'payment_date', label: 'Date' },
  { key: 'payment_method', label: 'Method' },
  { key: 'amount', label: 'Amount' },
  { key: 'invoice_number', label: 'Applied to Invoice' }
]

const paymentMethods = ['Bank Transfer', 'Cash', 'Check', 'Credit Card', 'Digital Wallet']
const customerOptions = computed(() => [{ label: 'All', value: '' }, ...customers.value.map(c => ({ label: c.name, value: c.id }))])
const invoiceOptions = computed(() => [{ label: 'No specific invoice', value: '' }, ...invoicesList.value.map(i => ({ label: `${i.invoice_number} - ${formatCurrency(i.amount_due)}`, value: i.id }))])
const bankAccounts = computed(() => [{ label: 'Select', value: '' }, ...bankAccountsList.value.map(a => ({ label: a.name, value: a.id }))])

const form = reactive({ customer_id: '', invoice_id: '', payment_date: '', amount: 0, payment_method: 'Bank Transfer', bank_account_id: '', reference_number: '', notes: '' })

const filteredReceipts = computed(() => {
  let result = receipts.value
  // Search filter
  if (search.value) { 
    const s = search.value.toLowerCase()
    result = result.filter((r: any) => 
      r.receipt_number?.toLowerCase().includes(s) ||
      r.customer_name?.toLowerCase().includes(s) ||
      r.payment_method?.toLowerCase().includes(s)
    )
  }
  // Customer filter
  const customerId = typeof customerFilter.value === 'object' ? customerFilter.value?.value : customerFilter.value
  if (customerId) {
    result = result.filter((r: any) => r.customer_id === customerId)
  }
  // Date range filter
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    if (startDate && endDate) {
      result = result.filter((r: any) => {
        if (!r.payment_date) return false
        const rDate = r.payment_date.split('T')[0]
        return rDate >= startDate && rDate <= endDate
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

const fetchReceipts = async () => {
  loading.value = true
  try { const res = await $api.get('/ar/receipts'); receipts.value = res.data }
  catch { receipts.value = [{ id: '1', receipt_number: 'REC-2026-001', customer_name: 'PT Customer Satu', payment_date: '2026-01-06', payment_method: 'Bank Transfer', amount: 12000000, invoice_number: 'INV-2026-002' }] }
  finally { loading.value = false }
}

const fetchCustomers = async () => { try { customers.value = (await $api.get('/sales/customers')).data } catch { customers.value = [{ id: '1', name: 'PT Customer' }] } }
const fetchInvoices = async () => { try { invoicesList.value = (await $api.get('/ar/invoices')).data.filter((i: any) => i.amount_due > 0) } catch {} }
const fetchBankAccounts = async () => { try { bankAccountsList.value = (await $api.get('/finance/banking/accounts')).data } catch {} }

const openForm = () => {
  Object.assign(form, { customer_id: '', invoice_id: route.query.invoice_id?.toString() || '', payment_date: new Date().toISOString().split('T')[0], amount: 0, payment_method: 'Bank Transfer', bank_account_id: '', reference_number: '', notes: '' })
  showForm.value = true
}

const saveReceipt = async () => {
  if (!form.customer_id || !form.payment_date || !form.amount) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try { await $api.post('/ar/receipts', form); toast.add({ title: 'Receipt saved', color: 'green' }); showForm.value = false; await fetchReceipts() }
  catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const clearFilters = () => { search.value = ''; customerFilter.value = ''; dateRange.value = [] }

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredReceipts.value, 'ar_receipts', cols)
  else if (format === 'xlsx') exportToExcel(filteredReceipts.value, 'ar_receipts', cols)
  else exportToPDF(filteredReceipts.value, 'ar_receipts', cols, 'AR Receipts')
}

onMounted(() => { fetchReceipts(); fetchCustomers(); fetchInvoices(); fetchBankAccounts() })
</script>
