<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Customer Invoices</h1>
        <p class="text-xs text-gray-500">Manage sales invoices and customer billing</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Invoice</UButton>
      </div>
    </div>

    <!-- Filters -->
    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-44">
          <label class="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <DatePicker v-model="dateRange" mode="range" placeholder="Select dates" />
        </div>
        <div class="w-36">
          <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <USelectMenu v-model="statusFilter" :options="statusOptions" size="sm" />
        </div>
        <div class="w-48">
          <label class="block text-xs font-medium text-gray-600 mb-1">Customer</label>
          <USelectMenu v-model="customerFilter" :options="customerOptions" size="sm" />
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
      <UTable :columns="columns" :rows="filteredInvoices" :loading="loading">
        <template #invoice_number-data="{ row }">
          <span class="font-medium text-primary-600 text-xs cursor-pointer hover:underline" @click="openForm(row)">
            {{ row.invoice_number }}
          </span>
        </template>
        <template #invoice_date-data="{ row }">
          <span class="text-xs">{{ formatDateShort(row.invoice_date) }}</span>
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
            <UButton size="2xs" variant="ghost" icon="i-heroicons-printer" />
            <UButton size="2xs" variant="ghost" icon="i-heroicons-banknotes" @click="goToReceipt(row)" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover v-model="showForm" :title="editingInvoice ? 'Edit Invoice' : 'New Customer Invoice'" 
                   :loading="saving" @submit="saveInvoice">
      <form class="space-y-4" @submit.prevent="saveInvoice">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">
            Customer <span class="text-red-500">*</span>
          </label>
          <USelectMenu v-model="form.customer_id" :options="customerOptions" placeholder="Select customer" size="sm" />
          <p class="text-xs text-gray-400 mt-0.5">Select billing customer</p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Invoice Number <span class="text-red-500">*</span>
            </label>
            <UInput v-model="form.invoice_number" placeholder="INV-2026-001" size="sm" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Payment Terms</label>
            <USelectMenu v-model="form.payment_terms" :options="paymentTermsOptions" size="sm" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Invoice Date <span class="text-red-500">*</span>
            </label>
            <DatePicker v-model="form.invoice_date" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Due Date <span class="text-red-500">*</span>
            </label>
            <DatePicker v-model="form.due_date" />
          </div>
        </div>

        <hr class="my-3" />

        <!-- Line Items -->
        <div class="border rounded-lg p-3 space-y-2">
          <div class="flex justify-between items-center">
            <label class="text-xs font-medium text-gray-700">Line Items</label>
            <UButton size="2xs" icon="i-heroicons-plus" @click="addLineItem">Add</UButton>
          </div>
          <div v-for="(item, idx) in form.items" :key="idx" class="grid grid-cols-12 gap-1 items-center">
            <div class="col-span-5">
              <UInput v-model="item.description" placeholder="Description" size="xs" />
            </div>
            <div class="col-span-2">
              <UInput v-model.number="item.qty" type="number" placeholder="Qty" size="xs" />
            </div>
            <div class="col-span-2">
              <UInput v-model.number="item.price" type="number" placeholder="Price" size="xs" />
            </div>
            <div class="col-span-2 text-right">
              <span class="text-xs font-medium">{{ formatCurrency(item.qty * item.price) }}</span>
            </div>
            <div class="col-span-1 text-right">
              <UButton size="2xs" color="red" variant="ghost" icon="i-heroicons-trash" @click="removeLineItem(idx)" />
            </div>
          </div>
          <div class="flex justify-end pt-2 border-t">
            <span class="font-bold text-sm">Total: {{ formatCurrency(invoiceTotal) }}</span>
          </div>
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

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editingInvoice = ref<any>(null)
const search = ref('')
const statusFilter = ref('')
const customerFilter = ref('')
const dateRange = ref<string[]>([])
const invoices = ref<any[]>([])
const customers = ref<any[]>([])

const columns = [
  { key: 'invoice_number', label: 'Invoice #', sortable: true },
  { key: 'customer_name', label: 'Customer', sortable: true },
  { key: 'invoice_date', label: 'Date', sortable: true },
  { key: 'due_date', label: 'Due Date', sortable: true },
  { key: 'total_amount', label: 'Total', sortable: true },
  { key: 'amount_due', label: 'Balance', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const statusOptions = [
  { label: 'All Status', value: '' },
  { label: 'Draft', value: 'Draft' },
  { label: 'Sent', value: 'Sent' },
  { label: 'Partially Paid', value: 'Partially Paid' },
  { label: 'Paid', value: 'Paid' },
  { label: 'Overdue', value: 'Overdue' }
]

const paymentTermsOptions = ['Net 30', 'Net 15', 'Net 7', 'Due on Receipt', 'Net 60']

const customerOptions = computed(() => [
  { label: 'All Customers', value: '' },
  ...customers.value.map(c => ({ label: c.name, value: c.id }))
])

const form = reactive({
  customer_id: '',
  invoice_number: '',
  payment_terms: 'Net 30',
  invoice_date: '',
  due_date: '',
  notes: '',
  items: [{ description: '', qty: 1, price: 0 }] as any[]
})

const invoiceTotal = computed(() => form.items.reduce((sum, item) => sum + (item.qty * item.price), 0))

const filteredInvoices = computed(() => {
  let result = invoices.value
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter((inv: any) => inv.invoice_number?.toLowerCase().includes(s) || inv.customer_name?.toLowerCase().includes(s))
  }
  if (statusFilter.value) result = result.filter((inv: any) => inv.status === statusFilter.value)
  if (customerFilter.value) result = result.filter((inv: any) => inv.customer_id === customerFilter.value)
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

const isOverdue = (row: any) => !row.due_date || row.status === 'Paid' ? false : new Date(row.due_date) < new Date()
const getStatusColor = (status: string) => ({ Draft: 'gray', Sent: 'blue', 'Partially Paid': 'yellow', Paid: 'green', Overdue: 'red' }[status] || 'gray')

const fetchInvoices = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }
    const res = await $api.get('/ar/invoices', { params })
    invoices.value = res.data
  } catch (e) {
    // Use mock data if API not available
    invoices.value = [
      { id: '1', invoice_number: 'INV-2026-001', customer_name: 'PT Customer Satu', invoice_date: '2026-01-05', due_date: '2026-02-05', total_amount: 25000000, amount_due: 25000000, status: 'Sent' },
      { id: '2', invoice_number: 'INV-2026-002', customer_name: 'CV Pelanggan Dua', invoice_date: '2026-01-03', due_date: '2026-01-18', total_amount: 12000000, amount_due: 0, status: 'Paid' }
    ]
  } finally { loading.value = false }
}

const fetchCustomers = async () => {
  try {
    const res = await $api.get('/sales/customers')
    customers.value = res.data
  } catch (e) {
    customers.value = [{ id: '1', name: 'PT Customer Satu' }, { id: '2', name: 'CV Pelanggan Dua' }]
  }
}

const openForm = (invoice?: any) => {
  if (invoice) {
    editingInvoice.value = invoice
    Object.assign(form, {
      customer_id: invoice.customer_id,
      invoice_number: invoice.invoice_number,
      payment_terms: invoice.payment_terms || 'Net 30',
      invoice_date: invoice.invoice_date?.split('T')[0] || '',
      due_date: invoice.due_date?.split('T')[0] || '',
      notes: invoice.notes || '',
      items: invoice.items || [{ description: '', qty: 1, price: 0 }]
    })
  } else {
    editingInvoice.value = null
    Object.assign(form, {
      customer_id: '', invoice_number: '', payment_terms: 'Net 30',
      invoice_date: new Date().toISOString().split('T')[0], due_date: '',
      notes: '', items: [{ description: '', qty: 1, price: 0 }]
    })
  }
  showForm.value = true
}

const addLineItem = () => form.items.push({ description: '', qty: 1, price: 0 })
const removeLineItem = (idx: number) => form.items.splice(idx, 1)

const saveInvoice = async () => {
  if (!form.customer_id || !form.invoice_number || !form.invoice_date) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  saving.value = true
  try {
    const payload = { ...form, total_amount: invoiceTotal.value }
    if (editingInvoice.value) await $api.put(`/ar/invoices/${editingInvoice.value.id}`, payload)
    else await $api.post('/ar/invoices', payload)
    toast.add({ title: 'Invoice saved successfully', color: 'green' })
    showForm.value = false
    await fetchInvoices()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally { saving.value = false }
}

const goToReceipt = (inv: any) => navigateTo(`/finance/ar/receipts?invoice_id=${inv.id}`)
const clearFilters = () => { search.value = ''; statusFilter.value = ''; customerFilter.value = ''; dateRange.value = [] }

const doExport = (format: string) => {
  const exportCols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  const data = filteredInvoices.value.map((inv: any) => ({ ...inv, total_amount: inv.total_amount?.toString(), amount_due: inv.amount_due?.toString() }))
  if (format === 'csv') exportToCSV(data, 'customer_invoices', exportCols)
  else if (format === 'xlsx') exportToExcel(data, 'customer_invoices', exportCols)
  else if (format === 'pdf') exportToPDF(data, 'customer_invoices', exportCols, 'Customer Invoices Report')
}

onMounted(() => { fetchInvoices(); fetchCustomers() })
</script>
