<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Vendor Bills</h1>
        <p class="text-xs text-gray-500">Manage purchase invoices and vendor bills</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Bill</UButton>
      </div>
    </div>

    <!-- Filters -->
    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" placeholder="Select dates" />
        </div>
        <div class="w-40">
          <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <USelectMenu v-model="statusFilter" :options="statusOptions" option-attribute="label" value-attribute="value" placeholder="All" size="sm" />
        </div>
        <div class="w-48">
          <label class="block text-xs font-medium text-gray-600 mb-1">Vendor</label>
          <USelectMenu v-model="vendorFilter" :options="vendorOptions" option-attribute="label" value-attribute="value" placeholder="All Vendors" size="sm" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="Invoice number..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
        <UButton variant="ghost" size="sm" @click="clearFilters">Clear</UButton>
      </div>
    </UCard>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredBills" :loading="loading" :sort="{ column: 'date', direction: 'desc' }">
        <template #invoice_number-data="{ row }">
          <span class="font-medium text-primary-600 cursor-pointer hover:underline" @click="openForm(row)">
            {{ row.invoice_number }}
          </span>
        </template>
        <template #date-data="{ row }">
          <span class="text-xs">{{ formatDateShort(row.date) }}</span>
        </template>
        <template #due_date-data="{ row }">
          <span :class="['text-xs', isOverdue(row) ? 'text-red-600 font-medium' : '']">
            {{ formatDateShort(row.due_date) }}
          </span>
        </template>
        <template #total_amount-data="{ row }">
          <span class="font-medium text-xs">{{ formatCurrency(row.total_amount) }}</span>
        </template>
        <template #amount_due-data="{ row }">
          <span :class="['text-xs font-semibold', row.amount_due > 0 ? 'text-red-600' : 'text-green-600']">
            {{ formatCurrency(row.amount_due) }}
          </span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="soft" size="xs">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="2xs" variant="ghost" icon="i-heroicons-pencil" @click="openForm(row)" />
            <UButton size="2xs" variant="ghost" icon="i-heroicons-banknotes" @click="goToPayment(row)" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover v-model="showForm" :title="editingBill ? 'Edit Vendor Bill' : 'New Vendor Bill'" 
                   :loading="saving" @submit="saveBill">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Record a bill/invoice received from a vendor for goods or services purchased.</p>
        
        <UFormGroup label="Vendor" required hint="Select the supplier/vendor who issued this bill" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.vendor_id" :options="vendorOptions" option-attribute="label" value-attribute="value" placeholder="Select vendor" size="sm" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Invoice Number" required hint="Vendor's invoice/bill reference number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.invoice_number" placeholder="INV-2026-001" size="sm" />
          </UFormGroup>
          <UFormGroup label="Payment Terms" hint="When payment is due" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.payment_terms" :options="paymentTermsOptions" size="sm" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Invoice Date" required hint="Date on the vendor's invoice" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="form.date" />
          </UFormGroup>
          <UFormGroup label="Due Date" required hint="Payment deadline" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="form.due_date" />
          </UFormGroup>
        </div>

        <hr class="my-2" />
        <p class="text-xs font-medium text-gray-600">Amount Details</p>

        <div class="grid grid-cols-3 gap-3">
          <UFormGroup label="Subtotal" hint="Before tax" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.subtotal" type="number" placeholder="0" size="sm" />
          </UFormGroup>
          <UFormGroup label="Tax Amount" hint="PPN/VAT amount" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.tax_amount" type="number" placeholder="0" size="sm" />
          </UFormGroup>
          <UFormGroup label="Total Amount" required hint="Final amount to pay" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.total_amount" type="number" placeholder="0" size="sm" class="font-semibold" />
          </UFormGroup>
        </div>

        <UFormGroup label="Notes" hint="Internal notes or memo for this bill" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" placeholder="Additional notes..." rows="2" size="sm" />
        </UFormGroup>
      </div>
    </FormSlideover>

  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatDate, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

// State
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editingBill = ref<any>(null)
const search = ref('')
const statusFilter = ref('')
const vendorFilter = ref('')
const dateRange = ref<string[]>([])
const bills = ref<any[]>([])
const vendors = ref<any[]>([])

// Table columns
const columns = [
  { key: 'invoice_number', label: 'Invoice #', sortable: true },
  { key: 'vendor_name', label: 'Vendor', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'due_date', label: 'Due Date', sortable: true },
  { key: 'total_amount', label: 'Total', sortable: true },
  { key: 'amount_due', label: 'Balance', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const statusOptions = [
  { label: 'All Status', value: '' },
  { label: 'Draft', value: 'Draft' },
  { label: 'Posted', value: 'Posted' },
  { label: 'Partially Paid', value: 'Partially Paid' },
  { label: 'Paid', value: 'Paid' }
]

const paymentTermsOptions = ['Cash', 'Net 30', 'Net 15', 'Net 7', 'Due on Receipt', 'Net 60']

const vendorOptions = computed(() => [
  { label: 'All Vendors', value: '' },
  ...vendors.value.map(v => ({ label: v.name, value: v.id }))
])

// Form
const form = reactive({
  vendor_id: '',
  invoice_number: '',
  payment_terms: 'Net 30',
  date: '',
  due_date: '',
  subtotal: 0,
  tax_amount: 0,
  total_amount: 0,
  notes: ''
})

// Computed
const filteredBills = computed(() => {
  let result = bills.value
  // Search filter
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter((b: any) => 
      b.invoice_number?.toLowerCase().includes(s) || 
      b.vendor_name?.toLowerCase().includes(s)
    )
  }
  // Status filter
  const status = typeof statusFilter.value === 'object' ? statusFilter.value?.value : statusFilter.value
  if (status) {
    result = result.filter((b: any) => b.status === status)
  }
  // Vendor filter
  const vendorId = typeof vendorFilter.value === 'object' ? vendorFilter.value?.value : vendorFilter.value
  if (vendorId) {
    result = result.filter((b: any) => b.vendor_id === vendorId)
  }
  // Date range filter
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    if (startDate && endDate) {
      result = result.filter((b: any) => {
        if (!b.date) return false
        const bDate = b.date.split('T')[0]
        return bDate >= startDate && bDate <= endDate
      })
    }
  }
  return result
})

// Export items
const exportItems = [[
  { label: 'Export CSV', icon: 'i-heroicons-document-text', click: () => doExport('csv') },
  { label: 'Export Excel', icon: 'i-heroicons-table-cells', click: () => doExport('xlsx') },
  { label: 'Export PDF', icon: 'i-heroicons-document', click: () => doExport('pdf') }
]]

// Methods
const formatDateShort = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const isOverdue = (row: any) => {
  if (!row.due_date || row.status === 'Paid') return false
  return new Date(row.due_date) < new Date()
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Draft: 'gray', Posted: 'blue', 'Partially Paid': 'yellow', Paid: 'green' }
  return colors[status] || 'gray'
}

const fetchBills = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }
    const res = await $api.get('/ap/bills', { params })
    bills.value = res.data
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
  } catch (e) {
    console.error(e)
  }
}

const openForm = (bill?: any) => {
  if (bill) {
    editingBill.value = bill
    Object.assign(form, {
      vendor_id: bill.vendor_id,
      invoice_number: bill.invoice_number,
      payment_terms: bill.payment_terms || 'Net 30',
      date: bill.date?.split('T')[0] || '',
      due_date: bill.due_date?.split('T')[0] || '',
      subtotal: bill.subtotal || 0,
      tax_amount: bill.tax_amount || 0,
      total_amount: bill.total_amount || 0,
      notes: bill.notes || ''
    })
  } else {
    editingBill.value = null
    Object.assign(form, {
      vendor_id: '', invoice_number: '', payment_terms: 'Net 30',
      date: new Date().toISOString().split('T')[0],
      due_date: '', subtotal: 0, tax_amount: 0, total_amount: 0, notes: ''
    })
  }
  showForm.value = true
}

const saveBill = async () => {
  if (!form.vendor_id || !form.invoice_number || !form.date || !form.total_amount) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    if (editingBill.value) {
      await $api.put(`/ap/bills/${editingBill.value.id}`, form)
      toast.add({ title: 'Bill updated successfully', color: 'green' })
    } else {
      await $api.post('/ap/invoices', { ...form, items: [] })
      toast.add({ title: 'Bill created successfully', color: 'green' })
    }
    showForm.value = false
    await fetchBills()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to save bill', color: 'red' })
  } finally {
    saving.value = false
  }
}

const goToPayment = (bill: any) => {
  navigateTo(`/finance/ap/payments?invoice_id=${bill.id}`)
}

const clearFilters = () => {
  search.value = ''
  statusFilter.value = ''
  vendorFilter.value = ''
  dateRange.value = []
}

const doExport = (format: string) => {
  const exportCols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  const data = filteredBills.value.map((b: any) => ({
    ...b,
    total_amount: b.total_amount?.toString() || '0',
    amount_due: b.amount_due?.toString() || '0'
  }))
  
  if (format === 'csv') exportToCSV(data, 'vendor_bills', exportCols)
  else if (format === 'xlsx') exportToExcel(data, 'vendor_bills', exportCols)
  else if (format === 'pdf') exportToPDF(data, 'vendor_bills', exportCols, 'Vendor Bills Report')
}

onMounted(() => {
  fetchBills()
  fetchVendors()
})
</script>
