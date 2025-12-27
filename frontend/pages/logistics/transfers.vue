<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Stock Transfers</h2>
        <p class="text-gray-500">Move inventory between warehouses and locations</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Transfer</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ transfers.length }}</p>
          <p class="text-sm text-gray-500">Total Transfers</p>
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
          <p class="text-2xl font-bold text-blue-600">{{ inTransitCount }}</p>
          <p class="text-sm text-gray-500">In Transit</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ completedToday }}</p>
          <p class="text-sm text-gray-500">Completed Today</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="transfers" 
        :loading="loading"
        searchable
        :search-keys="['transfer_number', 'from_warehouse', 'to_warehouse']"
        empty-message="No transfers yet. Create one to move stock between locations."
      >
        <template #transfer_number-data="{ row }">
          <span class="font-mono font-medium text-blue-600">{{ row.transfer_number }}</span>
        </template>
        <template #from_warehouse-data="{ row }">
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-building-office" class="text-gray-400" />
            {{ row.from_warehouse }}
          </div>
        </template>
        <template #to_warehouse-data="{ row }">
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-arrow-right" class="text-gray-400" />
            {{ row.to_warehouse }}
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #transfer_date-data="{ row }">
          {{ formatDate(row.transfer_date) }}
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status === 'Pending'" icon="i-heroicons-play" size="xs" color="blue" variant="ghost" @click="startTransfer(row)" title="Start Transfer" />
            <UButton v-if="row.status === 'In Transit'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="completeTransfer(row)" title="Complete" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create Transfer Modal -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create Stock Transfer"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Transfer inventory from one location to another. Select source, destination, and items to move.</p>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Source Warehouse" required hint="Where stock is coming from" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.from_warehouse_id" :options="warehouseOptions" placeholder="Select source..." />
          </UFormGroup>
          <UFormGroup label="Destination Warehouse" required hint="Where stock is going to" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.to_warehouse_id" :options="warehouseOptions" placeholder="Select destination..." />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Transfer Date" hint="Planned transfer date" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.transfer_date" type="date" />
          </UFormGroup>
          <UFormGroup label="Transfer Type" hint="Type of movement" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.transfer_type" :options="transferTypes" />
          </UFormGroup>
        </div>
        
        <!-- Items Section -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium">Items to Transfer</h4>
              <p class="text-xs text-gray-400">Select products and quantities to move</p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg">
            No items added. Click "Add Item" to select products.
          </div>
          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center">
            <USelect v-model="item.product_id" :options="productOptions" placeholder="Select Product..." class="flex-1" size="sm" />
            <UInput v-model.number="item.quantity" type="number" placeholder="Qty" class="w-20" size="sm" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="form.items.splice(idx, 1)" />
          </div>
        </div>
        
        <UFormGroup label="Notes" hint="Reason for transfer or special instructions" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" placeholder="e.g., Rebalancing stock levels..." />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)

const transfers = ref<any[]>([])
const warehouses = ref<any[]>([])
const products = ref<any[]>([])

const columns = [
  { key: 'transfer_number', label: 'Transfer #', sortable: true },
  { key: 'from_warehouse', label: 'From' },
  { key: 'to_warehouse', label: 'To' },
  { key: 'transfer_date', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const transferTypes = [
  { label: 'Standard Transfer', value: 'Standard' },
  { label: 'Urgent Transfer', value: 'Urgent' },
  { label: 'Rebalancing', value: 'Rebalancing' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  from_warehouse_id: '',
  to_warehouse_id: '',
  transfer_date: new Date().toISOString().split('T')[0],
  transfer_type: 'Standard',
  items: [] as any[],
  notes: ''
})

const pendingCount = computed(() => transfers.value.filter(t => t.status === 'Pending').length)
const inTransitCount = computed(() => transfers.value.filter(t => t.status === 'In Transit').length)
const completedToday = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return transfers.value.filter(t => t.status === 'Completed' && t.completed_at?.startsWith(today)).length
})

const warehouseOptions = computed(() => warehouses.value.map(w => ({ label: w.name, value: w.id })))
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code} - ${p.name}`, value: p.id })))

const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Pending: 'yellow', 'In Transit': 'blue', Completed: 'green', Cancelled: 'red' }
  return colors[status] || 'gray'
}

const addItem = () => {
  form.items.push({ product_id: '', quantity: 1 })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [transferRes, whRes, prodRes] = await Promise.all([
      $api.get('/logistics/transfers').catch(() => ({ data: [] })),
      $api.get('/inventory/warehouses').catch(() => ({ data: [] })),
      $api.get('/manufacturing/products').catch(() => ({ data: [] }))
    ])
    transfers.value = transferRes.data || []
    warehouses.value = whRes.data || []
    products.value = prodRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { from_warehouse_id: '', to_warehouse_id: '', transfer_date: new Date().toISOString().split('T')[0], transfer_type: 'Standard', items: [], notes: '' })
  isOpen.value = true
}

const viewDetails = (row: any) => {
  toast.add({ title: row.transfer_number, description: `From ${row.from_warehouse} to ${row.to_warehouse}`, color: 'blue' })
}

const save = async () => {
  if (!form.from_warehouse_id || !form.to_warehouse_id) {
    toast.add({ title: 'Validation Error', description: 'Please select source and destination', color: 'red' })
    return
  }
  if (form.from_warehouse_id === form.to_warehouse_id) {
    toast.add({ title: 'Validation Error', description: 'Source and destination must be different', color: 'red' })
    return
  }
  if (form.items.length === 0) {
    toast.add({ title: 'Validation Error', description: 'Please add at least one item', color: 'red' })
    return
  }
  submitting.value = true
  try {
    await $api.post('/logistics/transfers', form)
    toast.add({ title: 'Created', description: 'Stock transfer created', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const startTransfer = async (row: any) => {
  try {
    await $api.put(`/logistics/transfers/${row.id}/start`)
    toast.add({ title: 'Started', description: 'Transfer in transit', color: 'blue' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const completeTransfer = async (row: any) => {
  try {
    await $api.put(`/logistics/transfers/${row.id}/complete`)
    toast.add({ title: 'Completed', description: 'Transfer completed, stock updated', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const exportData = (format: string) => {
  const data = transfers.value.map((t: any) => ({
    'Transfer #': t.transfer_number,
    'From': t.from_warehouse,
    'To': t.to_warehouse,
    'Date': formatDate(t.transfer_date),
    'Type': t.transfer_type || 'Standard',
    'Status': t.status
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `stock_transfers.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Stock transfers exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Stock Transfers</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Stock Transfers Report</h1>
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
