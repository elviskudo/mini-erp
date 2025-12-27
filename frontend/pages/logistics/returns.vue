<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Return Management</h2>
        <p class="text-gray-500">Process sales returns and vendor returns</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Return</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ returns.length }}</p>
          <p class="text-sm text-gray-500">Total Returns</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ salesReturns }}</p>
          <p class="text-sm text-gray-500">Sales Returns</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ purchaseReturns }}</p>
          <p class="text-sm text-gray-500">Purchase Returns</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ pendingReturns }}</p>
          <p class="text-sm text-gray-500">Pending Processing</p>
        </div>
      </UCard>
    </div>

    <UTabs :items="tabs" v-model="activeTab">
      <template #sales>
        <UCard class="mt-4">
          <template #header>
            <h3 class="font-semibold">Sales Returns (Inbound)</h3>
            <p class="text-sm text-gray-500">Goods returned by customers</p>
          </template>
          <DataTable 
            :columns="columns" 
            :rows="salesReturnsList" 
            :loading="loading"
            searchable
            :search-keys="['return_number', 'customer_name']"
            empty-message="No sales returns"
          >
            <template #return_number-data="{ row }">
              <span class="font-mono font-medium text-orange-600">{{ row.return_number }}</span>
            </template>
            <template #status-data="{ row }">
              <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
            </template>
            <template #actions-data="{ row }">
              <div class="flex gap-1">
                <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
                <UButton v-if="row.status === 'Pending'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="processReturn(row)" title="Process" />
              </div>
            </template>
          </DataTable>
        </UCard>
      </template>
      
      <template #purchase>
        <UCard class="mt-4">
          <template #header>
            <h3 class="font-semibold">Purchase Returns (Outbound)</h3>
            <p class="text-sm text-gray-500">Goods returned to vendors</p>
          </template>
          <DataTable 
            :columns="purchaseColumns" 
            :rows="purchaseReturnsList" 
            :loading="loading"
            searchable
            :search-keys="['return_number', 'vendor_name']"
            empty-message="No purchase returns"
          >
            <template #return_number-data="{ row }">
              <span class="font-mono font-medium text-blue-600">{{ row.return_number }}</span>
            </template>
            <template #status-data="{ row }">
              <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
            </template>
            <template #actions-data="{ row }">
              <div class="flex gap-1">
                <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
                <UButton v-if="row.status === 'Pending'" icon="i-heroicons-truck" size="xs" color="blue" variant="ghost" @click="shipReturn(row)" title="Ship to Vendor" />
              </div>
            </template>
          </DataTable>
        </UCard>
      </template>
    </UTabs>

    <!-- Create Return Modal -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create Return"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create a return record for goods coming back from customer or going back to vendor.</p>
        
        <UFormGroup label="Return Type" required hint="Direction of the return" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.return_type" :options="returnTypes" />
        </UFormGroup>
        
        <UFormGroup v-if="form.return_type === 'Sales'" label="Customer" hint="Customer returning goods" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.customer_name" placeholder="Customer name" />
        </UFormGroup>
        
        <UFormGroup v-if="form.return_type === 'Purchase'" label="Vendor" hint="Vendor receiving returned goods" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.vendor_id" :options="vendorOptions" placeholder="Select vendor..." />
        </UFormGroup>
        
        <UFormGroup label="Original Reference" hint="SO/DO for sales, PO/GRN for purchase" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.reference" placeholder="e.g., SO-001 or PO-001" />
        </UFormGroup>
        
        <UFormGroup label="Return Reason" required hint="Why goods are being returned" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.reason" :options="reasonOptions" />
        </UFormGroup>
        
        <!-- Items Section -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium">Items to Return</h4>
              <p class="text-xs text-gray-400">Products being returned</p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center">
            <USelect v-model="item.product_id" :options="productOptions" placeholder="Product..." class="flex-1" size="sm" />
            <UInput v-model.number="item.quantity" type="number" placeholder="Qty" class="w-20" size="sm" />
            <USelect v-model="item.condition" :options="conditionOptions" class="w-28" size="sm" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="form.items.splice(idx, 1)" />
          </div>
        </div>
        
        <UFormGroup label="Notes" hint="Additional details about the return" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" placeholder="Reason details, damage description, etc." />
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
const activeTab = ref(0)

const returns = ref<any[]>([])
const products = ref<any[]>([])
const vendors = ref<any[]>([])

const tabs = [
  { label: 'Sales Returns', slot: 'sales' },
  { label: 'Purchase Returns', slot: 'purchase' }
]

const columns = [
  { key: 'return_number', label: 'Return #', sortable: true },
  { key: 'customer_name', label: 'Customer' },
  { key: 'reason', label: 'Reason' },
  { key: 'return_date', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const purchaseColumns = [
  { key: 'return_number', label: 'Return #', sortable: true },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'reason', label: 'Reason' },
  { key: 'return_date', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const returnTypes = [
  { label: 'Sales Return (from Customer)', value: 'Sales' },
  { label: 'Purchase Return (to Vendor)', value: 'Purchase' }
]

const reasonOptions = [
  { label: 'Defective Product', value: 'Defective' },
  { label: 'Wrong Item Sent', value: 'Wrong Item' },
  { label: 'Damaged in Transit', value: 'Damaged' },
  { label: 'Quality Issue', value: 'Quality' },
  { label: 'Customer Changed Mind', value: 'Changed Mind' },
  { label: 'Expired Product', value: 'Expired' },
  { label: 'Other', value: 'Other' }
]

const conditionOptions = [
  { label: 'Good', value: 'Good' },
  { label: 'Damaged', value: 'Damaged' },
  { label: 'Defective', value: 'Defective' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  return_type: 'Sales',
  customer_name: '',
  vendor_id: '',
  reference: '',
  reason: 'Defective',
  items: [] as any[],
  notes: ''
})

const salesReturnsList = computed(() => returns.value.filter(r => r.return_type === 'Sales'))
const purchaseReturnsList = computed(() => returns.value.filter(r => r.return_type === 'Purchase'))
const salesReturns = computed(() => salesReturnsList.value.length)
const purchaseReturns = computed(() => purchaseReturnsList.value.length)
const pendingReturns = computed(() => returns.value.filter(r => r.status === 'Pending').length)

const productOptions = computed(() => products.value.map(p => ({ label: `${p.code} - ${p.name}`, value: p.id })))
const vendorOptions = computed(() => vendors.value.map(v => ({ label: v.name, value: v.id })))

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Pending: 'yellow', 'In Transit': 'blue', Processed: 'green', Completed: 'green', Cancelled: 'red' }
  return colors[status] || 'gray'
}

const addItem = () => {
  form.items.push({ product_id: '', quantity: 1, condition: 'Good' })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [returnRes, prodRes, vendorRes] = await Promise.all([
      $api.get('/logistics/returns').catch(() => ({ data: [] })),
      $api.get('/manufacturing/products').catch(() => ({ data: [] })),
      $api.get('/procurement/vendors').catch(() => ({ data: [] }))
    ])
    returns.value = returnRes.data || []
    products.value = prodRes.data || []
    vendors.value = vendorRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { return_type: 'Sales', customer_name: '', vendor_id: '', reference: '', reason: 'Defective', items: [], notes: '' })
  isOpen.value = true
}

const viewDetails = (row: any) => {
  toast.add({ title: row.return_number, description: `Reason: ${row.reason}`, color: 'blue' })
}

const save = async () => {
  if (form.items.length === 0) {
    toast.add({ title: 'Validation Error', description: 'Please add at least one item', color: 'red' })
    return
  }
  submitting.value = true
  try {
    await $api.post('/logistics/returns', form)
    toast.add({ title: 'Created', description: 'Return created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const processReturn = async (row: any) => {
  try {
    await $api.put(`/logistics/returns/${row.id}/process`)
    toast.add({ title: 'Processed', description: 'Return processed, stock updated', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const shipReturn = async (row: any) => {
  try {
    await $api.put(`/logistics/returns/${row.id}/ship`)
    toast.add({ title: 'Shipped', description: 'Return shipped to vendor', color: 'blue' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const exportData = (format: string) => {
  const data = returns.value.map((r: any) => ({
    'Return #': r.return_number,
    'Type': r.return_type,
    'Party': r.customer_name || r.vendor_name || '',
    'Reason': r.reason,
    'Date': r.return_date || '',
    'Status': r.status
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `returns.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Returns exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Returns</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Return Management Report</h1>
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
