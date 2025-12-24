<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Purchase Orders</h2>
        <p class="text-gray-500">Manage purchase orders and receiving</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton color="gray" variant="outline" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchPos">Refresh</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard v-for="stat in stats" :key="stat.status" :ui="{ body: { padding: 'p-3' } }">
        <div class="flex items-center gap-2">
          <UBadge :color="stat.color" variant="soft" class="w-3 h-3 rounded-full p-0"></UBadge>
          <div>
            <p class="text-lg font-bold">{{ stat.count }}</p>
            <p class="text-xs text-gray-500">{{ stat.status }}</p>
          </div>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable :columns="columns" :rows="orders" :loading="loading" search-placeholder="Search orders...">
        <template #po_number-data="{ row }">
          <span class="font-mono text-sm">{{ row.po_number || row.id?.slice(0, 8) }}</span>
        </template>
        <template #vendor-data="{ row }">
          <div>
            <p class="font-medium">{{ row.vendor?.name || 'Unknown' }}</p>
            <UBadge v-if="row.vendor?.rating" :color="getRatingColor(row.vendor?.rating)" size="xs" variant="soft">
              {{ row.vendor?.rating }}
            </UBadge>
          </div>
        </template>
        <template #created_at-data="{ row }">
          <span class="text-sm text-gray-600">{{ formatDate(row.created_at) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #total-data="{ row }">
          <span class="font-medium">Rp {{ formatNumber(row.total_amount || 0) }}</span>
        </template>
        <template #progress-data="{ row }">
          <div class="flex items-center gap-2 w-24">
            <div class="flex-1 bg-gray-200 rounded-full h-2">
              <div class="bg-green-500 h-2 rounded-full" :style="{ width: (row.progress || 0) + '%' }"></div>
            </div>
            <span class="text-xs text-gray-500">{{ row.progress || 0 }}%</span>
          </div>
        </template>
        <template #payment_status-data="{ row }">
          <UBadge :color="getPaymentColor(row.payment_status)" variant="subtle">{{ row.payment_status || 'Unpaid' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="viewOrder(row)" title="View Details" />
            <UButton icon="i-heroicons-document-arrow-down" color="primary" variant="ghost" size="xs" @click="downloadPdf(row)" title="Download PDF" />
            <UButton v-if="row.status === 'Draft'" icon="i-heroicons-paper-airplane" color="blue" variant="ghost" size="xs" @click="openSendModal(row)" title="Send to Vendor" />
            <UButton v-if="row.status === 'Open' || row.status === 'Partial Receive'" icon="i-heroicons-inbox-arrow-down" color="green" variant="ghost" size="xs" @click="openReceive(row)" title="Receive Goods" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- View Order Modal -->
    <UModal v-model="showViewModal" :ui="{ width: 'w-full sm:max-w-3xl' }">
      <UCard v-if="selectedOrder">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold">PO: {{ selectedOrder.po_number || selectedOrder.id?.slice(0, 8) }}</h3>
              <p class="text-sm text-gray-500">{{ selectedOrder.vendor?.name }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedOrder.status)" variant="soft">{{ selectedOrder.status }}</UBadge>
          </div>
        </template>

        <div class="space-y-4">
          <!-- Items Table -->
          <div>
            <p class="text-sm font-medium text-gray-700 mb-2">Items</p>
            <div class="border rounded-lg overflow-hidden">
              <table class="w-full text-sm">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="text-left p-3">Product</th>
                    <th class="text-right p-3">Qty</th>
                    <th class="text-right p-3">Received</th>
                    <th class="text-right p-3">Unit Price</th>
                    <th class="text-right p-3">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in selectedOrder.items" :key="item.id" class="border-t">
                    <td class="p-3">{{ item.product?.name }}</td>
                    <td class="text-right p-3">{{ item.quantity }}</td>
                    <td class="text-right p-3">{{ item.received_qty || 0 }}</td>
                    <td class="text-right p-3">Rp {{ formatNumber(item.unit_price) }}</td>
                    <td class="text-right p-3 font-medium">Rp {{ formatNumber(item.line_total || item.quantity * item.unit_price) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Landed Cost -->
          <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <p class="text-sm text-gray-500">Subtotal</p>
              <p class="font-medium">Rp {{ formatNumber(selectedOrder.subtotal || 0) }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Shipping Cost</p>
              <p class="font-medium">Rp {{ formatNumber(selectedOrder.shipping_cost || 0) }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Insurance</p>
              <p class="font-medium">Rp {{ formatNumber(selectedOrder.insurance_cost || 0) }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Customs Duty</p>
              <p class="font-medium">Rp {{ formatNumber(selectedOrder.customs_duty || 0) }}</p>
            </div>
            <div class="col-span-2 pt-2 border-t">
              <p class="text-sm text-gray-500">Total Amount</p>
              <p class="text-xl font-bold text-green-600">Rp {{ formatNumber(selectedOrder.total_amount || 0) }}</p>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end">
            <UButton color="gray" variant="ghost" @click="showViewModal = false">Close</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Receive Goods Modal -->
    <UModal v-model="showReceiveModal" :ui="{ width: 'w-full sm:max-w-2xl' }">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Receive Goods - {{ receiveOrder?.po_number || receiveOrder?.id?.slice(0, 8) }}</h3>
        </template>

        <div class="space-y-4">
          <!-- Items to Receive -->
          <div class="space-y-3">
            <div v-for="(item, idx) in receiveForm.items" :key="idx" class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <div class="flex-1">
                <p class="font-medium">{{ item.product_name }}</p>
                <p class="text-sm text-gray-500">Ordered: {{ item.ordered_qty }} | Already Received: {{ item.already_received }}</p>
              </div>
              <UFormGroup label="Receive Qty" class="w-32">
                <UInput v-model="item.receive_qty" type="number" :max="item.ordered_qty - item.already_received" min="0" />
              </UFormGroup>
            </div>
          </div>

          <!-- Landed Cost Allocation -->
          <div class="border-t pt-4">
            <h4 class="text-sm font-medium mb-3">Landed Cost Allocation</h4>
            <div class="grid grid-cols-3 gap-4">
              <UFormGroup label="Shipping Cost" hint="Freight charges" :ui="{ hint: 'text-xs text-gray-400' }">
                <CurrencyInput v-model="receiveForm.shipping_cost" :currency="currencyCode" />
              </UFormGroup>
              <UFormGroup label="Insurance" hint="Cargo insurance" :ui="{ hint: 'text-xs text-gray-400' }">
                <CurrencyInput v-model="receiveForm.insurance_cost" :currency="currencyCode" />
              </UFormGroup>
              <UFormGroup label="Customs Duty" hint="Import taxes" :ui="{ hint: 'text-xs text-gray-400' }">
                <CurrencyInput v-model="receiveForm.customs_duty" :currency="currencyCode" />
              </UFormGroup>
            </div>
          </div>

          <!-- Cold Chain Check -->
          <div class="border border-blue-200 rounded-lg p-4 bg-blue-50">
            <h4 class="text-sm font-medium mb-2">Cold Chain Verification</h4>
            <div class="grid grid-cols-2 gap-4">
              <UFormGroup label="Received Temperature (°C)" hint="Actual temp on arrival" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="receiveForm.received_temp" type="number" step="0.1" placeholder="e.g. 4.5" />
              </UFormGroup>
              <UFormGroup label="Temperature Status">
                <div class="flex items-center gap-2 mt-2">
                  <UBadge v-if="receiveForm.received_temp !== null" :color="tempCheckPassed ? 'green' : 'red'" variant="soft">
                    {{ tempCheckPassed ? 'PASS' : 'FAIL - Over Max Temp' }}
                  </UBadge>
                </div>
              </UFormGroup>
            </div>
          </div>

          <UFormGroup label="Notes">
            <UTextarea v-model="receiveForm.notes" rows="2" placeholder="Additional notes..." />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showReceiveModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="submitReceive">Confirm Receipt</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Send to Vendor Modal -->
    <UModal v-model="showSendModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-paper-airplane" class="text-blue-500" />
            <h3 class="text-lg font-semibold">Send PO to Vendor</h3>
          </div>
        </template>
        
        <div class="space-y-4">
          <div v-if="sendingPo" class="bg-gray-50 rounded-lg p-4">
            <p class="text-sm text-gray-500">You're about to send:</p>
            <p class="font-semibold text-lg">{{ sendingPo.po_number }}</p>
            <p class="text-sm text-gray-600">to {{ sendingPo.vendor?.name || 'vendor' }}</p>
          </div>
          
          <UFormGroup label="Notes for Vendor" hint="Optional message to include">
            <UTextarea v-model="sendNotes" rows="3" placeholder="Add delivery instructions, special requirements, etc..." />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showSendModal = false">Cancel</UButton>
            <UButton color="blue" icon="i-heroicons-paper-airplane" @click="confirmSendToVendor">
              Send to Vendor
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const { currencyCode, formatCurrency } = useCurrency()
const toast = useToast()
const loading = ref(false)
const submitting = ref(false)
const orders = ref<any[]>([])
const showViewModal = ref(false)
const showReceiveModal = ref(false)
const selectedOrder = ref<any>(null)
const receiveOrder = ref<any>(null)

const columns = [
  { key: 'po_number', label: 'PO Number' },
  { key: 'vendor', label: 'Vendor' },
  { key: 'created_at', label: 'Date' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'payment_status', label: 'Payment' },
  { key: 'total', label: 'Total Amount' },
  { key: 'actions', label: '' }
]

const exportItems = [
  [{
    label: 'Export as Excel',
    icon: 'i-heroicons-table-cells',
    click: () => exportData('xlsx')
  }, {
    label: 'Export as CSV',
    icon: 'i-heroicons-document-text',
    click: () => exportData('csv')
  }, {
    label: 'Export as PDF',
    icon: 'i-heroicons-document',
    click: () => exportData('pdf')
  }]
]

const receiveForm = reactive({
  items: [] as any[],
  shipping_cost: 0,
  insurance_cost: 0,
  customs_duty: 0,
  received_temp: null as number | null,
  notes: ''
})

const stats = computed(() => {
  const statusCounts: Record<string, number> = {}
  orders.value.forEach(o => {
    statusCounts[o.status] = (statusCounts[o.status] || 0) + 1
  })
  return [
    { status: 'Draft', count: statusCounts['Draft'] || 0, color: 'gray' },
    { status: 'Pending Approval', count: statusCounts['Pending Approval'] || 0, color: 'yellow' },
    { status: 'Open', count: statusCounts['Open'] || 0, color: 'blue' },
    { status: 'Partial Receive', count: statusCounts['Partial Receive'] || 0, color: 'orange' },
    { status: 'Closed', count: statusCounts['Closed'] || 0, color: 'green' }
  ]
})

const tempCheckPassed = computed(() => {
  if (receiveForm.received_temp === null) return true
  // Check against max temp of items (simplified - use 8°C default for cold chain)
  return receiveForm.received_temp <= 8
})

const getStatusColor = (status: string) => {
  switch(status) {
    case 'Draft': return 'gray'
    case 'Pending Approval': return 'yellow'
    case 'Open': return 'blue'
    case 'Partial Receive': return 'orange'
    case 'Closed': return 'green'
    case 'Cancelled': return 'red'
    default: return 'primary'
  }
}

const getRatingColor = (rating: string) => {
  switch (rating) {
    case 'A': return 'green'
    case 'B': return 'yellow'
    case 'C': return 'red'
    default: return 'gray'
  }
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('id-ID').format(num)
}

const formatDate = (date: string | null) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric' 
  })
}

const getPaymentColor = (status: string) => {
  switch(status) {
    case 'Paid': return 'green'
    case 'Partial': return 'yellow'
    case 'Unpaid': return 'red'
    default: return 'gray'
  }
}

const exportData = async (format: string) => {
  const data = orders.value.map((po: any) => ({
    'PO Number': po.po_number || po.id?.slice(0, 8),
    'Vendor': po.vendor?.name || 'Unknown',
    'Date': po.created_at ? new Date(po.created_at).toLocaleDateString('id-ID') : '-',
    'Status': po.status,
    'Total': 'Rp ' + formatNumber(po.total_amount || 0)
  }))
  
  if (format === 'csv') {
    const headers = Object.keys(data[0] || {}).join(',')
    const rows = data.map((row: any) => Object.values(row).join(',')).join('\n')
    const csv = headers + '\n' + rows
    downloadFile(csv, 'purchase_orders.csv', 'text/csv')
  } else if (format === 'xlsx') {
    const headers = Object.keys(data[0] || {}).join('\t')
    const rows = data.map((row: any) => Object.values(row).join('\t')).join('\n')
    const xls = headers + '\n' + rows
    downloadFile(xls, 'purchase_orders.xls', 'application/vnd.ms-excel')
  } else if (format === 'pdf') {
    const companyName = authStore.user?.tenant_name || 'PT. Mini ERP Indonesia'
    const exportDate = new Date().toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' })
    const html = `
      <html><head><title>Purchase Orders</title>
      <style>
        body{font-family:Arial,sans-serif;margin:20px}
        .header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #2563eb;padding-bottom:15px;margin-bottom:20px}
        .company-name{font-size:20px;font-weight:bold;color:#1e40af}
        .report-info{text-align:right;color:#666}
        table{border-collapse:collapse;width:100%}
        th,td{border:1px solid #ddd;padding:10px;text-align:left}
        th{background:#2563eb;color:white}
        .footer{margin-top:20px;text-align:center;color:#666;font-size:12px}
      </style></head>
      <body>
        <div class="header">
          <div>
            <div class="company-name">${companyName}</div>
            <div style="color:#666">Jakarta, Indonesia</div>
          </div>
          <div class="report-info">
            <div style="font-size:18px;font-weight:bold;color:#2563eb">PURCHASE ORDERS</div>
            <div>Export Date: ${exportDate}</div>
          </div>
        </div>
        <table>
          <tr>${Object.keys(data[0] || {}).map(k => '<th>' + k + '</th>').join('')}</tr>
          ${data.map((row: any) => '<tr>' + Object.values(row).map(v => '<td>' + v + '</td>').join('') + '</tr>').join('')}
        </table>
        <div class="footer">Generated by Mini-ERP System on ${exportDate}</div>
      </body></html>
    `
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(html)
      win.document.close()
      win.print()
    }
  }
  toast.add({ title: 'Export', description: `Exported as ${format.toUpperCase()}`, color: 'green' })
}

const downloadFile = (content: string, filename: string, type: string) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const fetchPos = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const res: any = await $fetch('/api/procurement/orders', { headers })
    orders.value = res
  } catch (e) {
    console.error(e)
    orders.value = []
  } finally {
    loading.value = false
  }
}

const viewOrder = (row: any) => {
  selectedOrder.value = row
  showViewModal.value = true
}

const downloadPdf = async (row: any) => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const response = await fetch(`/api/procurement/orders/${row.id}/pdf`, { headers })
    
    if (!response.ok) throw new Error('Failed to download PDF')
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `PO-${row.po_number || row.id?.slice(0, 8)}.pdf`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    toast.add({ title: 'Downloaded', description: 'PDF downloaded successfully', color: 'green' })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to download PDF', color: 'red' })
  }
}

// Send to Vendor Modal
const showSendModal = ref(false)
const sendNotes = ref('')
const sendingPo = ref<any>(null)

const openSendModal = (row: any) => {
  sendingPo.value = row
  sendNotes.value = ''
  showSendModal.value = true
}

const confirmSendToVendor = async () => {
  if (!sendingPo.value) return
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/procurement/orders/${sendingPo.value.id}/send`, { 
      method: 'POST', 
      headers,
      body: { notes: sendNotes.value }
    })
    showSendModal.value = false
    toast.add({ 
      title: '✓ PO Sent!', 
      description: `${sendingPo.value.po_number} has been sent to ${sendingPo.value.vendor?.name || 'vendor'}`, 
      color: 'green' 
    })
    fetchPos()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to send PO', color: 'red' })
  }
}

const openReceive = (row: any) => {
  receiveOrder.value = row
  receiveForm.items = (row.items || []).map((item: any) => ({
    po_line_id: item.id,
    product_id: item.product_id,
    product_name: item.product?.name,
    ordered_qty: item.quantity,
    already_received: item.received_qty || 0,
    receive_qty: item.quantity - (item.received_qty || 0)
  }))
  receiveForm.shipping_cost = row.shipping_cost || 0
  receiveForm.insurance_cost = row.insurance_cost || 0
  receiveForm.customs_duty = row.customs_duty || 0
  receiveForm.received_temp = null
  receiveForm.notes = ''
  showReceiveModal.value = true
}

const submitReceive = async () => {
  if (!receiveOrder.value) return
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/procurement/orders/${receiveOrder.value.id}/receive`, {
      method: 'POST',
      headers,
      body: {
        items: receiveForm.items.filter(i => i.receive_qty > 0).map(i => ({
          po_line_id: i.po_line_id,
          product_id: i.product_id,
          quantity: i.receive_qty
        })),
        shipping_cost: receiveForm.shipping_cost,
        insurance_cost: receiveForm.insurance_cost,
        customs_duty: receiveForm.customs_duty,
        received_temp: receiveForm.received_temp,
        temp_check_passed: tempCheckPassed.value,
        notes: receiveForm.notes
      }
    })
    toast.add({ title: 'Received', description: 'Goods received successfully', color: 'green' })
    showReceiveModal.value = false
    fetchPos()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to receive goods', color: 'red' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchPos()
})
</script>
