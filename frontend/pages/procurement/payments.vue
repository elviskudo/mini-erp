<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Payment Tracking</h2>
        <p class="text-gray-500">Monitor vendor payment status, outstanding balances, and payment history</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">Rp {{ formatNumber(totalOutstanding) }}</p>
          <p class="text-sm text-gray-500">Total Outstanding</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">Rp {{ formatNumber(overdueAmount) }}</p>
          <p class="text-sm text-gray-500">Overdue</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">Rp {{ formatNumber(paidThisMonth) }}</p>
          <p class="text-sm text-gray-500">Paid This Month</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ payments.length }}</p>
          <p class="text-sm text-gray-500">Total Payments</p>
        </div>
      </UCard>
    </div>

    <!-- Tabs -->
    <UTabs :items="tabs" v-model="activeTab">
      <template #outstanding>
        <UCard class="mt-4">
          <template #header>
            <h3 class="font-semibold">Outstanding Bills</h3>
          </template>
          <DataTable 
            :columns="outstandingColumns" 
            :rows="outstandingBills" 
            :loading="loading"
            searchable
            :search-keys="['bill_number', 'vendor_name']"
            empty-message="No outstanding bills"
          >
            <template #bill_number-data="{ row }">
              <span class="font-mono">{{ row.bill_number }}</span>
            </template>
            <template #due_date-data="{ row }">
              <span :class="isOverdue(row.due_date) ? 'text-red-600 font-medium' : ''">
                {{ formatDate(row.due_date) }}
                <span v-if="isOverdue(row.due_date)" class="text-xs"> (Overdue)</span>
              </span>
            </template>
            <template #balance_due-data="{ row }">
              <span class="font-medium text-orange-600">Rp {{ formatNumber(row.balance_due) }}</span>
            </template>
            <template #actions-data="{ row }">
              <UButton icon="i-heroicons-banknotes" size="xs" color="green" @click="openQuickPay(row)">Pay</UButton>
            </template>
          </DataTable>
        </UCard>
      </template>
      
      <template #history>
        <UCard class="mt-4">
          <template #header>
            <h3 class="font-semibold">Payment History</h3>
          </template>
          <DataTable 
            :columns="historyColumns" 
            :rows="payments" 
            :loading="loading"
            searchable
            :search-keys="['bill_number', 'vendor_name', 'reference']"
            empty-message="No payment history"
          >
            <template #payment_date-data="{ row }">
              {{ formatDate(row.payment_date) }}
            </template>
            <template #amount-data="{ row }">
              <span class="font-medium text-green-600">Rp {{ formatNumber(row.amount) }}</span>
            </template>
            <template #payment_method-data="{ row }">
              <UBadge color="gray" variant="subtle">{{ row.payment_method }}</UBadge>
            </template>
          </DataTable>
        </UCard>
      </template>
      
      <template #vendor>
        <UCard class="mt-4">
          <template #header>
            <h3 class="font-semibold">By Vendor</h3>
          </template>
          <div class="space-y-4">
            <div v-for="v in vendorSummary" :key="v.vendor_id" class="p-4 border rounded-lg">
              <div class="flex justify-between items-center">
                <div>
                  <p class="font-medium">{{ v.vendor_name }}</p>
                  <p class="text-sm text-gray-500">{{ v.bills_count }} bills</p>
                </div>
                <div class="text-right">
                  <p class="text-lg font-bold text-orange-600">Rp {{ formatNumber(v.total_outstanding) }}</p>
                  <p class="text-sm text-gray-500">Outstanding</p>
                </div>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-2 mt-2">
                <div class="h-2 rounded-full bg-green-500" :style="{ width: `${v.paid_percent}%` }"></div>
              </div>
              <p class="text-xs text-gray-400 mt-1">{{ v.paid_percent }}% paid</p>
            </div>
            <p v-if="!vendorSummary.length" class="text-center text-gray-400 py-8">No vendor data</p>
          </div>
        </UCard>
      </template>
    </UTabs>

    <!-- Quick Pay Modal -->
    <UModal v-model="showPayModal">
      <UCard v-if="selectedBill">
        <template #header>
          <h3 class="font-semibold">Quick Payment - {{ selectedBill.bill_number }}</h3>
        </template>
        <div class="space-y-4">
          <div class="p-3 bg-gray-50 rounded-lg">
            <p><strong>{{ selectedBill.vendor_name }}</strong></p>
            <p class="text-sm text-gray-500">Balance: Rp {{ formatNumber(selectedBill.balance_due) }}</p>
          </div>
          <UFormGroup label="Amount">
            <UInput v-model.number="payForm.amount" type="number" />
          </UFormGroup>
          <UFormGroup label="Method">
            <USelect v-model="payForm.payment_method" :options="['Bank Transfer', 'Cash', 'Check']" />
          </UFormGroup>
          <UFormGroup label="Reference">
            <UInput v-model="payForm.reference" placeholder="Bank ref / Check no" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showPayModal = false">Cancel</UButton>
            <UButton @click="submitPayment" :loading="submitting" color="green">Confirm Payment</UButton>
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
const activeTab = ref(0)
const showPayModal = ref(false)

const bills = ref<any[]>([])
const payments = ref<any[]>([])
const selectedBill = ref<any>(null)

const tabs = [
  { label: 'Outstanding', slot: 'outstanding' },
  { label: 'Payment History', slot: 'history' },
  { label: 'By Vendor', slot: 'vendor' }
]

const outstandingColumns = [
  { key: 'bill_number', label: 'Bill #' },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'due_date', label: 'Due Date', sortable: true },
  { key: 'balance_due', label: 'Balance' },
  { key: 'actions', label: '' }
]

const historyColumns = [
  { key: 'payment_date', label: 'Date', sortable: true },
  { key: 'bill_number', label: 'Bill #' },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'amount', label: 'Amount' },
  { key: 'payment_method', label: 'Method' },
  { key: 'reference', label: 'Reference' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const payForm = reactive({
  amount: 0,
  payment_method: 'Bank Transfer',
  reference: ''
})

const outstandingBills = computed(() => bills.value.filter(b => b.balance_due > 0))
const totalOutstanding = computed(() => outstandingBills.value.reduce((sum, b) => sum + b.balance_due, 0))
const overdueAmount = computed(() => outstandingBills.value.filter(b => isOverdue(b.due_date)).reduce((sum, b) => sum + b.balance_due, 0))
const paidThisMonth = computed(() => {
  const now = new Date()
  return payments.value.filter(p => {
    const d = new Date(p.payment_date)
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
  }).reduce((sum, p) => sum + p.amount, 0)
})

const vendorSummary = computed(() => {
  const map = new Map()
  bills.value.forEach(b => {
    if (!map.has(b.vendor_id)) {
      map.set(b.vendor_id, { vendor_id: b.vendor_id, vendor_name: b.vendor_name, total: 0, paid: 0, bills_count: 0 })
    }
    const v = map.get(b.vendor_id)
    v.total += b.total_amount || 0
    v.paid += b.amount_paid || 0
    v.bills_count++
  })
  return Array.from(map.values()).map(v => ({
    ...v,
    total_outstanding: v.total - v.paid,
    paid_percent: v.total > 0 ? Math.round((v.paid / v.total) * 100) : 0
  })).filter(v => v.total_outstanding > 0)
})

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num || 0)
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const isOverdue = (date: string) => date && new Date(date) < new Date()

const fetchData = async () => {
  loading.value = true
  try {
    const [billsRes, paymentsRes] = await Promise.all([
      $api.get('/procurement/bills'),
      $api.get('/procurement/payments')
    ])
    bills.value = billsRes.data.data || []
    payments.value = paymentsRes.data.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openQuickPay = (bill: any) => {
  selectedBill.value = bill
  Object.assign(payForm, { amount: bill.balance_due, payment_method: 'Bank Transfer', reference: '' })
  showPayModal.value = true
}

const submitPayment = async () => {
  if (!selectedBill.value) return
  submitting.value = true
  try {
    await $api.post(`/procurement/bills/${selectedBill.value.id}/payments`, payForm)
    toast.add({ title: 'Payment Recorded', color: 'green' })
    showPayModal.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const exportData = (format: string) => {
  const data = payments.value.map((p: any) => ({
    'Date': formatDate(p.payment_date), 'Bill': p.bill_number, 'Vendor': p.vendor_name,
    'Amount': p.amount, 'Method': p.payment_method, 'Reference': p.reference || ''
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `payment_history.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Payment history exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Payment History</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Payment History Report</h1>
        <p>Exported: ${new Date().toLocaleDateString()}</p>
        <p>Total Outstanding: Rp ${formatNumber(totalOutstanding.value)}</p>
        <table><tr>${Object.keys(data[0] || {}).map(h => `<th>${h}</th>`).join('')}</tr>
        ${data.map((row: any) => `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}
        </table></body></html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }
}

onMounted(() => { fetchData() })
</script>
