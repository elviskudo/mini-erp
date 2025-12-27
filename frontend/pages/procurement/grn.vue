<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Goods Receipt</h2>
        <p class="text-gray-500">Confirm goods received from vendors against purchase orders</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New GRN</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ grns.length }}</p>
          <p class="text-sm text-gray-500">Total GRNs</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ pendingPos }}</p>
          <p class="text-sm text-gray-500">POs Awaiting Receipt</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ receivedToday }}</p>
          <p class="text-sm text-gray-500">Received Today</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ partialReceipts }}</p>
          <p class="text-sm text-gray-500">Partial Receipts</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="grns" 
        :loading="loading"
        searchable
        :search-keys="['grn_number', 'po_number']"
        empty-message="No goods receipts yet. Create one when you receive goods from a vendor."
      >
        <template #grn_number-data="{ row }">
          <span class="font-mono font-medium text-blue-600">{{ row.grn_number }}</span>
        </template>
        <template #po_number-data="{ row }">
          <span class="font-mono text-gray-600">{{ row.po_number }}</span>
        </template>
        <template #receive_date-data="{ row }">
          {{ formatDate(row.receive_date) }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status || 'Received' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status !== 'Inspected'" icon="i-heroicons-clipboard-document-check" size="xs" color="green" variant="ghost" @click="inspectGRN(row)" title="Inspect" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create GRN Modal -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create Goods Receipt Note"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Record items received from a vendor. Select the PO and specify quantities received.</p>
        
        <UFormGroup label="Purchase Order" required hint="Select the PO for which you are receiving goods" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.po_id" :options="poOptions" placeholder="Select PO..." @change="loadPoItems" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Receive Date" hint="Date goods were received" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.receive_date" type="date" />
          </UFormGroup>
          <UFormGroup label="Warehouse" hint="Storage location for received goods" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.warehouse_id" :options="warehouseOptions" placeholder="Select warehouse..." />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Delivery Note Number" hint="Vendor's delivery order number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.delivery_note" placeholder="e.g., DO-2024-001" />
          </UFormGroup>
          <UFormGroup label="Vehicle Number" hint="Delivery vehicle plate number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.vehicle_number" placeholder="e.g., B 1234 ABC" />
          </UFormGroup>
        </div>
        
        <!-- Items Section -->
        <div class="border-t pt-4" v-if="form.items.length">
          <h4 class="font-medium mb-3">Items to Receive</h4>
          <div class="space-y-3">
            <div v-for="(item, idx) in form.items" :key="idx" class="p-3 border rounded-lg">
              <div class="flex justify-between items-start mb-2">
                <div>
                  <p class="font-medium">{{ item.product_name }}</p>
                  <p class="text-xs text-gray-500">Ordered: {{ item.ordered_qty }} | Already Received: {{ item.already_received }}</p>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <UFormGroup label="Receive Qty" hint="Quantity received this time" :ui="{ hint: 'text-xs text-gray-400' }">
                  <UInput v-model.number="item.receive_qty" type="number" size="sm" :max="item.ordered_qty - item.already_received" />
                </UFormGroup>
                <UFormGroup label="Batch No." hint="Batch/Lot number" :ui="{ hint: 'text-xs text-gray-400' }">
                  <UInput v-model="item.batch_number" size="sm" placeholder="LOT-001" />
                </UFormGroup>
                <UFormGroup label="Expiry Date" hint="Product expiration" :ui="{ hint: 'text-xs text-gray-400' }">
                  <UInput v-model="item.expiry_date" type="date" size="sm" />
                </UFormGroup>
              </div>
            </div>
          </div>
        </div>
        
        <UFormGroup label="Notes" hint="Additional notes about this receipt" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" placeholder="e.g., All items in good condition..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Detail Modal -->
    <UModal v-model="showDetailModal" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedGRN">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedGRN.grn_number }}</h3>
              <p class="text-sm text-gray-500">PO: {{ selectedGRN.po_number }} | Date: {{ formatDate(selectedGRN.receive_date) }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedGRN.status)" size="lg">{{ selectedGRN.status || 'Received' }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div><span class="text-gray-500">Warehouse:</span> {{ selectedGRN.warehouse_name || '-' }}</div>
            <div><span class="text-gray-500">Delivery Note:</span> {{ selectedGRN.delivery_note || '-' }}</div>
            <div><span class="text-gray-500">Vehicle:</span> {{ selectedGRN.vehicle_number || '-' }}</div>
            <div><span class="text-gray-500">Received By:</span> {{ selectedGRN.received_by_name || '-' }}</div>
          </div>
          
          <div class="border-t pt-4">
            <h4 class="font-medium mb-2">Received Items</h4>
            <UTable :columns="itemColumns" :rows="selectedGRN.items || []" />
          </div>
          
          <div v-if="selectedGRN.notes" class="border-t pt-4">
            <h4 class="font-medium mb-1">Notes</h4>
            <p class="text-sm text-gray-600">{{ selectedGRN.notes }}</p>
          </div>
        </div>
        
        <template #footer>
          <UButton variant="ghost" @click="showDetailModal = false">Close</UButton>
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
const showDetailModal = ref(false)

const grns = ref<any[]>([])
const purchaseOrders = ref<any[]>([])
const warehouses = ref<any[]>([])
const selectedGRN = ref<any>(null)

const columns = [
  { key: 'grn_number', label: 'GRN #', sortable: true },
  { key: 'po_number', label: 'PO #' },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'receive_date', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const itemColumns = [
  { key: 'product_name', label: 'Product' },
  { key: 'quantity_received', label: 'Qty Received' },
  { key: 'batch_number', label: 'Batch' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  po_id: '',
  receive_date: new Date().toISOString().split('T')[0],
  warehouse_id: '',
  delivery_note: '',
  vehicle_number: '',
  items: [] as any[],
  notes: ''
})

const pendingPos = computed(() => purchaseOrders.value.filter(p => p.status === 'OPEN' || p.status === 'PARTIAL_RECEIVE').length)
const receivedToday = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return grns.value.filter(g => g.receive_date?.startsWith(today)).length
})
const partialReceipts = computed(() => grns.value.filter(g => g.status === 'Partial').length)

const poOptions = computed(() => purchaseOrders.value.filter(p => p.status === 'OPEN' || p.status === 'PARTIAL_RECEIVE').map(p => ({ label: `${p.po_number} - ${p.vendor?.name || 'Unknown'}`, value: p.id })))
const warehouseOptions = computed(() => warehouses.value.map(w => ({ label: w.name, value: w.id })))

const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Received: 'blue', Inspected: 'green', 'Partial': 'yellow', Rejected: 'red' }
  return colors[status] || 'gray'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [grnRes, poRes, whRes] = await Promise.all([
      $api.get('/procurement/grns').catch(() => ({ data: [] })),
      $api.get('/procurement/orders').catch(() => ({ data: [] })),
      $api.get('/inventory/warehouses').catch(() => ({ data: [] }))
    ])
    grns.value = grnRes.data || []
    purchaseOrders.value = poRes.data || []
    warehouses.value = whRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { po_id: '', receive_date: new Date().toISOString().split('T')[0], warehouse_id: '', delivery_note: '', vehicle_number: '', items: [], notes: '' })
  isOpen.value = true
}

const loadPoItems = async () => {
  if (!form.po_id) return
  try {
    const po = purchaseOrders.value.find(p => p.id === form.po_id)
    if (po && po.items) {
      form.items = po.items.map((item: any) => ({
        po_line_id: item.id,
        product_id: item.product_id,
        product_name: item.product?.name || 'Product',
        ordered_qty: item.quantity,
        already_received: item.received_qty || 0,
        receive_qty: item.quantity - (item.received_qty || 0),
        batch_number: '',
        expiry_date: ''
      }))
    }
  } catch (e) {
    console.error(e)
  }
}

const viewDetails = (row: any) => {
  selectedGRN.value = row
  showDetailModal.value = true
}

const save = async () => {
  if (!form.po_id) {
    toast.add({ title: 'Validation Error', description: 'Please select a Purchase Order', color: 'red' })
    return
  }
  submitting.value = true
  try {
    await $api.post('/procurement/grns', form)
    toast.add({ title: 'Created', description: 'Goods Receipt created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to create GRN', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const inspectGRN = async (row: any) => {
  try {
    await $api.put(`/procurement/grns/${row.id}/inspect`)
    toast.add({ title: 'Inspected', description: 'GRN marked as inspected', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const exportData = (format: string) => {
  const data = grns.value.map((g: any) => ({
    'GRN #': g.grn_number,
    'PO #': g.po_number,
    'Vendor': g.vendor_name,
    'Date': formatDate(g.receive_date),
    'Warehouse': g.warehouse_name || '',
    'Status': g.status || 'Received'
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `goods_receipts.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Goods receipts exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Goods Receipts</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Goods Receipts Report</h1>
        <p>Exported: ${new Date().toLocaleDateString()}</p>
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
