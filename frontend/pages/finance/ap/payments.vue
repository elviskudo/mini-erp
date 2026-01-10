<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">AP Payments</h1>
        <p class="text-xs text-gray-500">Record and manage vendor payments</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Payment</UButton>
      </div>
    </div>

    <!-- Filters -->
    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" placeholder="Select dates" />
        </div>
        <div class="w-48">
          <label class="block text-xs font-medium text-gray-600 mb-1">Vendor</label>
          <USelectMenu v-model="vendorFilter" :options="vendorOptions" placeholder="All Vendors" size="sm" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="Payment number, reference..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
        <UButton variant="ghost" size="sm" @click="clearFilters">Clear</UButton>
      </div>
    </UCard>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredPayments" :loading="loading">
        <template #payment_number-data="{ row }">
          <span class="font-medium text-primary-600 text-xs">{{ row.payment_number }}</span>
        </template>
        <template #payment_date-data="{ row }">
          <span class="text-xs">{{ formatDateShort(row.payment_date) }}</span>
        </template>
        <template #amount-data="{ row }">
          <span class="font-semibold text-green-600 text-xs">{{ formatCurrency(row.amount) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'completed' ? 'green' : 'yellow'" variant="soft" size="xs">
            {{ row.status }}
          </UBadge>
        </template>
      </UTable>
    </UCard>

    <FormSlideover v-model="showForm" title="Record Payment" :loading="saving" @submit="savePayment">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Record a payment made to a vendor for goods or services purchased.</p>
        
        <UFormGroup label="Vendor" required hint="Vendor receiving this payment" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.vendor_id" :options="vendorOptions" option-attribute="label" value-attribute="value" placeholder="Select vendor" size="sm" />
        </UFormGroup>

        <UFormGroup label="Bill (Optional)" hint="Link payment to a specific bill" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.invoice_id" :options="billOptions" option-attribute="label" value-attribute="value" placeholder="Select bill to pay" size="sm" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Payment Date" required hint="Date payment was made" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="form.payment_date" />
          </UFormGroup>
          <UFormGroup label="Amount" required hint="Payment amount in full" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.amount" type="number" placeholder="0" size="sm" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Payment Method" required hint="How payment was made" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.payment_method" :options="paymentMethods" size="sm" />
          </UFormGroup>
          <UFormGroup label="Bank Account" hint="Source account for payment" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.bank_account_id" :options="bankAccounts" option-attribute="label" value-attribute="value" placeholder="Select account" size="sm" />
          </UFormGroup>
        </div>

        <UFormGroup label="Reference Number" hint="Bank transfer ref, check no., giro no." :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.reference_number" placeholder="Transfer ref, check number..." size="sm" />
        </UFormGroup>

        <UFormGroup label="Notes" hint="Additional payment notes or memo" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" size="sm" />
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
const search = ref('')
const vendorFilter = ref('')
const dateRange = ref<string[]>([])
const payments = ref<any[]>([])
const vendors = ref<any[]>([])
const unpaidBills = ref<any[]>([])
const bankAccountsList = ref<any[]>([])

const columns = [
  { key: 'payment_number', label: 'Payment #', sortable: true },
  { key: 'vendor_name', label: 'Vendor', sortable: true },
  { key: 'payment_date', label: 'Date', sortable: true },
  { key: 'payment_method', label: 'Method' },
  { key: 'amount', label: 'Amount', sortable: true },
  { key: 'reference_number', label: 'Reference' },
  { key: 'status', label: 'Status' }
]

const paymentMethods = ['Bank Transfer', 'Check', 'Cash', 'Giro', 'Credit Card']

const vendorOptions = computed(() => [
  { label: 'All Vendors', value: '' },
  ...vendors.value.map(v => ({ label: v.name, value: v.id }))
])

const billOptions = computed(() => [
  { label: 'No specific bill', value: '' },
  ...unpaidBills.value.map(b => ({ 
    label: `${b.invoice_number} - ${formatCurrency(b.amount_due)}`, 
    value: b.id 
  }))
])

const bankAccounts = computed(() => [
  { label: 'Select account', value: '' },
  ...bankAccountsList.value.map(a => ({ label: a.name, value: a.id }))
])

const form = reactive({
  vendor_id: '',
  invoice_id: '',
  payment_date: '',
  amount: 0,
  payment_method: 'Bank Transfer',
  bank_account_id: '',
  reference_number: '',
  notes: ''
})

const filteredPayments = computed(() => {
  let result = payments.value
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter((p: any) => 
      p.payment_number?.toLowerCase().includes(s) || 
      p.reference_number?.toLowerCase().includes(s) ||
      p.vendor_name?.toLowerCase().includes(s)
    )
  }
  if (vendorFilter.value) {
    result = result.filter((p: any) => p.vendor_id === vendorFilter.value)
  }
  return result
})

const exportItems = [[
  { label: 'Export CSV', icon: 'i-heroicons-document-text', click: () => doExport('csv') },
  { label: 'Export Excel', icon: 'i-heroicons-table-cells', click: () => doExport('xlsx') },
  { label: 'Export PDF', icon: 'i-heroicons-document', click: () => doExport('pdf') }
]]

const formatDateShort = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const fetchPayments = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }
    const res = await $api.get('/ap/payments', { params })
    payments.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchVendors = async () => {
  try {
    const res = await $api.get('/procurement/vendors')
    vendors.value = res.data
  } catch (e) { console.error(e) }
}

const fetchUnpaidBills = async () => {
  try {
    const res = await $api.get('/ap/bills', { params: { status: 'Posted' } })
    unpaidBills.value = res.data.filter((b: any) => b.amount_due > 0)
  } catch (e) { console.error(e) }
}

const fetchBankAccounts = async () => {
  try {
    const res = await $api.get('/finance/banking/accounts')
    bankAccountsList.value = res.data
  } catch (e) { console.error(e) }
}

const openForm = () => {
  Object.assign(form, {
    vendor_id: '', invoice_id: route.query.invoice_id?.toString() || '',
    payment_date: new Date().toISOString().split('T')[0],
    amount: 0, payment_method: 'Bank Transfer', bank_account_id: '', reference_number: '', notes: ''
  })
  showForm.value = true
}

const savePayment = async () => {
  if (!form.vendor_id || !form.payment_date || !form.amount || !form.payment_method) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    await $api.post('/ap/payments', form)
    toast.add({ title: 'Payment recorded successfully', color: 'green' })
    showForm.value = false
    await fetchPayments()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to save payment', color: 'red' })
  } finally {
    saving.value = false
  }
}

const clearFilters = () => {
  search.value = ''
  vendorFilter.value = ''
  dateRange.value = []
}

const doExport = (format: string) => {
  const exportCols = columns.map(c => ({ key: c.key, label: c.label }))
  const data = filteredPayments.value.map((p: any) => ({ ...p, amount: p.amount?.toString() }))
  
  if (format === 'csv') exportToCSV(data, 'ap_payments', exportCols)
  else if (format === 'xlsx') exportToExcel(data, 'ap_payments', exportCols)
  else if (format === 'pdf') exportToPDF(data, 'ap_payments', exportCols, 'AP Payments Report')
}

onMounted(() => {
  fetchPayments()
  fetchVendors()
  fetchUnpaidBills()
  fetchBankAccounts()
})
</script>
