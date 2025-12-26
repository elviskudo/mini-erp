<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Vendor Bills</h2>
        <p class="text-gray-500">Manage invoices from vendors</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
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
          <p class="text-2xl font-bold text-orange-600">Rp {{ formatNumber(totalDue) }}</p>
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
      title="New Vendor Bill"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <UFormGroup label="Vendor" required>
          <USelect v-model="form.vendor_id" :options="vendorOptions" placeholder="Select vendor..." />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Vendor Invoice #">
            <UInput v-model="form.vendor_invoice" placeholder="INV-001" />
          </UFormGroup>
          <UFormGroup label="Bill Date">
            <UInput v-model="form.bill_date" type="date" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Due Date">
            <UInput v-model="form.due_date" type="date" />
          </UFormGroup>
          <UFormGroup label="PO Reference">
            <USelect v-model="form.po_id" :options="poOptions" placeholder="Link to PO (optional)" />
          </UFormGroup>
        </div>
        
        <!-- Line Items -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium">Line Items</h4>
            <UButton size="xs" icon="i-heroicons-plus" @click="addLine">Add Line</UButton>
          </div>
          <div v-for="(line, idx) in form.items" :key="idx" class="flex gap-2 mb-2">
            <UInput v-model="line.description" placeholder="Description" class="flex-1" size="sm" />
            <UInput v-model.number="line.quantity" type="number" placeholder="Qty" class="w-16" size="sm" />
            <UInput v-model.number="line.unit_price" type="number" placeholder="Price" class="w-24" size="sm" />
            <span class="text-sm text-gray-600 w-24 text-right">{{ formatNumber(line.quantity * line.unit_price) }}</span>
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="form.items.splice(idx, 1)" />
          </div>
          <div class="flex justify-end pt-2 border-t mt-2">
            <span class="font-medium">Total: Rp {{ formatNumber(formTotal) }}</span>
          </div>
        </div>
        
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="2" />
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
            <p class="text-sm text-orange-700">Balance Due: <strong>Rp {{ formatNumber(selectedBill.balance_due) }}</strong></p>
          </div>
          
          <UFormGroup label="Payment Amount" required>
            <UInput v-model.number="paymentForm.amount" type="number" placeholder="0" />
          </UFormGroup>
          <UFormGroup label="Payment Method">
            <USelect v-model="paymentForm.payment_method" :options="['Bank Transfer', 'Cash', 'Check', 'Credit Card']" />
          </UFormGroup>
          <UFormGroup label="Reference / Notes">
            <UInput v-model="paymentForm.reference" placeholder="Bank ref, check no, etc." />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showPaymentModal = false">Cancel</UButton>
            <UButton @click="recordPayment" :loading="submitting" color="green">Record Payment</UButton>
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

const form = reactive({
  vendor_id: '',
  vendor_invoice: '',
  bill_date: new Date().toISOString().split('T')[0],
  due_date: '',
  po_id: '',
  items: [] as any[],
  notes: ''
})

const paymentForm = reactive({
  amount: 0,
  payment_method: 'Bank Transfer',
  reference: ''
})

const pendingCount = computed(() => bills.value.filter(b => b.status === 'Pending').length)
const paidCount = computed(() => bills.value.filter(b => b.status === 'Paid').length)
const overdueCount = computed(() => bills.value.filter(b => isOverdue(b.due_date, b.status)).length)
const totalDue = computed(() => bills.value.reduce((sum, b) => sum + (b.balance_due || 0), 0))
const vendorOptions = computed(() => vendors.value.map(v => ({ label: v.name, value: v.id })))
const poOptions = computed(() => [{ label: 'None', value: '' }, ...purchaseOrders.value.map(p => ({ label: p.po_number, value: p.id }))])
const formTotal = computed(() => form.items.reduce((sum, l) => sum + (l.quantity * l.unit_price), 0))

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num)
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
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
  Object.assign(form, { vendor_id: '', vendor_invoice: '', bill_date: new Date().toISOString().split('T')[0], due_date: '', po_id: '', items: [], notes: '' })
  isOpen.value = true
}

const viewDetails = (row: any) => {
  selectedBill.value = row
}

const openPayment = (row: any) => {
  selectedBill.value = row
  Object.assign(paymentForm, { amount: row.balance_due, payment_method: 'Bank Transfer', reference: '' })
  showPaymentModal.value = true
}

const save = async () => {
  submitting.value = true
  try {
    await $api.post('/procurement/bills', { ...form, total_amount: formTotal.value, balance_due: formTotal.value })
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
    toast.add({ title: 'Approved', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const recordPayment = async () => {
  if (!selectedBill.value) return
  submitting.value = true
  try {
    await $api.post(`/procurement/bills/${selectedBill.value.id}/payments`, paymentForm)
    toast.add({ title: 'Payment Recorded', color: 'green' })
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
    'Bill #': b.bill_number, 'Vendor': b.vendor_name, 'Due Date': formatDate(b.due_date),
    'Status': b.status, 'Total': b.total_amount, 'Balance': b.balance_due
  }))
  if (format === 'csv') {
    const headers = Object.keys(data[0] || {})
    const csv = [headers.join(','), ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'vendor_bills.csv'; a.click()
  }
}

onMounted(() => { fetchData() })
</script>
