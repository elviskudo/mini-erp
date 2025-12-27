<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Vendor Bills</h2>
        <p class="text-gray-500">Manage invoices received from vendors and track payment status</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Bill</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ bills.length }}</p>
          <p class="text-sm text-gray-500">Total Bills</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ pendingCount }}</p>
          <p class="text-sm text-gray-500">Pending</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">Rp {{ formatCompact(totalDue) }}</p>
          <p class="text-sm text-gray-500">Balance Due</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ overdueCount }}</p>
          <p class="text-sm text-gray-500">Overdue</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ paidCount }}</p>
          <p class="text-sm text-gray-500">Paid</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="bills" 
        :loading="loading"
        searchable
        :search-keys="['bill_number', 'vendor_name', 'vendor_invoice']"
        empty-message="No bills yet. Create one when you receive an invoice from a vendor."
      >
        <template #bill_number-data="{ row }">
          <span class="font-mono font-medium">{{ row.bill_number }}</span>
        </template>
        <template #vendor_name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.vendor_name }}</p>
            <p v-if="row.vendor_invoice" class="text-xs text-gray-400">Inv: {{ row.vendor_invoice }}</p>
          </div>
        </template>
        <template #due_date-data="{ row }">
          <span :class="isOverdue(row.due_date, row.status) ? 'text-red-600 font-medium' : ''">
            {{ formatDate(row.due_date) }}
            <span v-if="isOverdue(row.due_date, row.status)" class="text-xs"> (Overdue)</span>
          </span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #total_amount-data="{ row }">
          Rp {{ formatNumber(row.total_amount || 0) }}
        </template>
        <template #balance_due-data="{ row }">
          <span :class="row.balance_due > 0 ? 'text-orange-600 font-medium' : 'text-green-600'">
            Rp {{ formatNumber(row.balance_due || 0) }}
          </span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status === 'Pending'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="approveBill(row)" title="Approve" />
            <UButton v-if="row.balance_due > 0" icon="i-heroicons-banknotes" size="xs" color="blue" variant="ghost" @click="openPayment(row)" title="Record Payment" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create Bill Modal -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create Vendor Bill"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Record an invoice received from a vendor. Link it to a PO for easier tracking.</p>
        
        <UFormGroup label="Vendor" required hint="The supplier who issued this invoice" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.vendor_id" :options="vendorOptions" placeholder="Select vendor..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Vendor Invoice Number" hint="Invoice number from the vendor's document" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.vendor_invoice" placeholder="e.g., INV-2024-001" />
          </UFormGroup>
          <UFormGroup label="Bill Date" required hint="Date the invoice was issued" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.bill_date" type="date" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Due Date" required hint="Payment deadline for this bill" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.due_date" type="date" />
          </UFormGroup>
          <UFormGroup label="Purchase Order Reference" hint="Link to the original PO (optional)" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.po_id" :options="poOptions" placeholder="Link to PO..." />
          </UFormGroup>
        </div>
        
        <!-- Line Items -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium">Invoice Line Items</h4>
              <p class="text-xs text-gray-400">Add items from the vendor's invoice</p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" @click="addLine">Add Line</UButton>
          </div>
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg">
            No line items added yet. Click "Add Line" to add items.
          </div>
          <div v-for="(line, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center">
            <UInput v-model="line.description" placeholder="Item description" class="flex-1" size="sm" />
            <UInput v-model.number="line.quantity" type="number" placeholder="Qty" class="w-16" size="sm" />
            <UInput v-model.number="line.unit_price" type="number" placeholder="Unit Price" class="w-28" size="sm" />
            <span class="text-sm text-gray-600 w-28 text-right font-medium">Rp {{ formatNumber(line.quantity * line.unit_price) }}</span>
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="form.items.splice(idx, 1)" />
          </div>
          <div class="flex justify-between pt-3 border-t mt-3">
            <span class="text-gray-500">Subtotal:</span>
            <span class="font-bold text-lg">Rp {{ formatNumber(formTotal) }}</span>
          </div>
        </div>
        
        <UFormGroup label="Tax Amount (Rp)" hint="VAT or other applicable taxes" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.tax_amount" type="number" placeholder="0" />
        </UFormGroup>
        
        <div class="p-3 bg-blue-50 rounded-lg">
          <div class="flex justify-between">
            <span class="font-medium text-blue-700">Total Amount:</span>
            <span class="font-bold text-xl text-blue-700">Rp {{ formatNumber(formTotal + (form.tax_amount || 0)) }}</span>
          </div>
        </div>
        
        <UFormGroup label="Notes" hint="Additional notes or payment instructions" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" placeholder="e.g., Payment via bank transfer to account..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Payment Modal -->
    <UModal v-model="showPaymentModal">
      <UCard v-if="selectedBill">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <UIcon name="i-heroicons-banknotes" class="text-green-600 w-6 h-6" />
            </div>
            <div>
              <h3 class="text-lg font-semibold">Record Payment</h3>
              <p class="text-sm text-gray-500">{{ selectedBill.bill_number }} - {{ selectedBill.vendor_name }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="p-3 bg-orange-50 rounded-lg">
            <p class="text-sm text-orange-700">Outstanding Balance: <strong>Rp {{ formatNumber(selectedBill.balance_due) }}</strong></p>
          </div>
          
          <UFormGroup label="Payment Amount" required hint="Amount being paid for this bill" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="paymentForm.amount" type="number" placeholder="0" />
          </UFormGroup>
          
          <UFormGroup label="Payment Method" hint="How the payment was made" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="paymentForm.payment_method" :options="paymentMethods" />
          </UFormGroup>
          
          <UFormGroup label="Reference Number" hint="Bank transfer ref, check number, or receipt ID" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="paymentForm.reference" placeholder="e.g., TRF-20241227-001" />
          </UFormGroup>
          
          <UFormGroup label="Payment Notes" hint="Additional payment details or remarks" :ui="{ hint: 'text-xs text-gray-400' }">
            <UTextarea v-model="paymentForm.notes" rows="2" placeholder="e.g., Paid via company bank account..." />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showPaymentModal = false">Cancel</UButton>
            <UButton @click="recordPayment" :loading="submitting" color="green">Confirm Payment</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)
const showPaymentModal = ref(false)

const bills = ref<any[]>([])
const vendors = ref<any[]>([])
const purchaseOrders = ref<any[]>([])
const selectedBill = ref<any>(null)

const columns = [
  { key: 'bill_number', label: 'Bill #', sortable: true },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'due_date', label: 'Due Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'total_amount', label: 'Total' },
  { key: 'balance_due', label: 'Balance' },
  { key: 'actions', label: '' }
]

const paymentMethods = [
  { label: 'Bank Transfer', value: 'Bank Transfer' },
  { label: 'Cash', value: 'Cash' },
  { label: 'Check', value: 'Check' },
  { label: 'Credit Card', value: 'Credit Card' },
  { label: 'E-Wallet', value: 'E-Wallet' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  vendor_id: '',
  vendor_invoice: '',
  bill_date: new Date().toISOString().split('T')[0],
  due_date: '',
  po_id: '',
  items: [] as any[],
  tax_amount: 0,
  notes: ''
})

const paymentForm = reactive({
  amount: 0,
  payment_method: 'Bank Transfer',
  reference: '',
  notes: ''
})

const pendingCount = computed(() => bills.value.filter(b => b.status === 'Pending').length)
const paidCount = computed(() => bills.value.filter(b => b.status === 'Paid').length)
const overdueCount = computed(() => bills.value.filter(b => isOverdue(b.due_date, b.status)).length)
const totalDue = computed(() => bills.value.reduce((sum, b) => sum + (b.balance_due || 0), 0))
const vendorOptions = computed(() => vendors.value.map(v => ({ label: v.name, value: v.id })))
const poOptions = computed(() => [{ label: '-- No PO Link --', value: '' }, ...purchaseOrders.value.map(p => ({ label: p.po_number, value: p.id }))])
const formTotal = computed(() => form.items.reduce((sum, l) => sum + (l.quantity * l.unit_price), 0))

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num)
const formatCompact = (num: number) => {
  if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'B'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(0) + 'K'
  return formatNumber(num)
}
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const isOverdue = (date: string, status: string) => status !== 'Paid' && date && new Date(date) < new Date()

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Draft: 'gray', Pending: 'yellow', Approved: 'blue', 'Partial Paid': 'orange', Paid: 'green', Cancelled: 'red' }
  return colors[status] || 'gray'
}

const addLine = () => {
  form.items.push({ description: '', quantity: 1, unit_price: 0 })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [billsRes, vendorRes, poRes] = await Promise.all([
      $api.get('/procurement/bills'),
      $api.get('/procurement/vendors'),
      $api.get('/procurement/orders')
    ])
    bills.value = billsRes.data || []
    vendors.value = vendorRes.data || []
    purchaseOrders.value = poRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { vendor_id: '', vendor_invoice: '', bill_date: new Date().toISOString().split('T')[0], due_date: '', po_id: '', items: [], tax_amount: 0, notes: '' })
  isOpen.value = true
}

const viewDetails = (row: any) => {
  selectedBill.value = row
}

const openPayment = (row: any) => {
  selectedBill.value = row
  Object.assign(paymentForm, { amount: row.balance_due, payment_method: 'Bank Transfer', reference: '', notes: '' })
  showPaymentModal.value = true
}

const save = async () => {
  if (!form.vendor_id) {
    toast.add({ title: 'Validation Error', description: 'Please select a vendor', color: 'red' })
    return
  }
  submitting.value = true
  try {
    const totalAmount = formTotal.value + (form.tax_amount || 0)
    await $api.post('/procurement/bills', { ...form, total_amount: totalAmount, balance_due: totalAmount })
    toast.add({ title: 'Created', description: 'Bill created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const approveBill = async (row: any) => {
  try {
    await $api.put(`/procurement/bills/${row.id}/approve`)
    toast.add({ title: 'Approved', description: 'Bill has been approved', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const recordPayment = async () => {
  if (!selectedBill.value) return
  if (paymentForm.amount <= 0) {
    toast.add({ title: 'Validation Error', description: 'Payment amount must be greater than 0', color: 'red' })
    return
  }
  submitting.value = true
  try {
    await $api.post(`/procurement/bills/${selectedBill.value.id}/payments`, paymentForm)
    toast.add({ title: 'Payment Recorded', description: 'Payment has been recorded successfully', color: 'green' })
    showPaymentModal.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const exportData = (format: string) => {
  const data = bills.value.map(b => ({
    'Bill #': b.bill_number,
    'Vendor Invoice': b.vendor_invoice || '',
    'Vendor': b.vendor_name,
    'Bill Date': formatDate(b.bill_date),
    'Due Date': formatDate(b.due_date),
    'Status': b.status,
    'Total Amount': b.total_amount,
    'Amount Paid': b.amount_paid,
    'Balance Due': b.balance_due
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map(row => headers.map(h => `"${row[h as keyof typeof row] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `vendor_bills.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Vendor bills exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Vendor Bills</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Vendor Bills Report</h1>
        <p>Exported: ${new Date().toLocaleDateString()}</p>
        <p>Total Outstanding: Rp ${formatNumber(totalDue.value)}</p>
        <table><tr>${Object.keys(data[0] || {}).map(h => `<th>${h}</th>`).join('')}</tr>
        ${data.map(row => `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}
        </table></body></html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }
}

onMounted(() => { fetchData() })
</script>
