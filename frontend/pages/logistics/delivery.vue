<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Delivery Orders</h2>
        <p class="text-gray-500">Manage outbound deliveries to customers</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Create DO</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ orders.length }}</p>
          <p class="text-sm text-gray-500">Total DOs</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ draftCount }}</p>
          <p class="text-sm text-gray-500">Draft</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ shippedCount }}</p>
          <p class="text-sm text-gray-500">Shipped</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ deliveredCount }}</p>
          <p class="text-sm text-gray-500">Delivered</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="orders" 
        :loading="loading"
        searchable
        :search-keys="['do_number', 'so_id', 'customer_name']"
        empty-message="No delivery orders yet. Create one to ship goods."
      >
        <template #do_number-data="{ row }">
          <span class="font-mono font-medium text-blue-600">{{ row.do_number }}</span>
        </template>
        <template #so_id-data="{ row }">
          <span class="text-gray-600">{{ row.so_id || '-' }}</span>
        </template>
        <template #customer_name-data="{ row }">
          <span>{{ row.customer_name || 'Walk-in' }}</span>
        </template>
        <template #items_count-data="{ row }">
          <span class="text-gray-500">{{ row.items_count }} items</span>
        </template>
        <template #created_at-data="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton 
              v-if="row.status === 'Draft'" 
              icon="i-heroicons-truck" 
              size="xs" 
              color="blue" 
              variant="ghost" 
              :loading="shippingId === row.id"
              @click="shipOrder(row)" 
              title="Ship Order" 
            />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create DO Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create Delivery Order"
      :loading="submitting"
      @submit="createDo"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create a delivery order to ship products to customers. Link to a Sales Order or create direct.</p>
        
        <UFormGroup label="Sales Order Reference" hint="Optional link to original SO" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu 
            v-model="form.so_id" 
            :options="soOptions" 
            placeholder="Search Sales Order (e.g., SO-001)..." 
            searchable
            clearable
            value-attribute="value"
            @change="onSoSelect"
          />
        </UFormGroup>
        
        <!-- Customer Section -->
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3 flex items-center gap-2">
            <UIcon name="i-heroicons-user" />
            Customer Information
          </h4>
          <p class="text-xs text-gray-400 mb-3">Select existing customer or enter manually. Customers are managed in <NuxtLink to="/crm/customers" class="text-blue-600 underline">CRM → Customers</NuxtLink></p>
          
          <UFormGroup label="Select Customer" hint="Choose from registered customers" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu 
              v-model="form.customer_id" 
              :options="customerOptions" 
              placeholder="Select existing customer..." 
              searchable 
              value-attribute="value"
              @change="onCustomerSelect"
            />
          </UFormGroup>
          
          <div class="text-center text-gray-400 text-xs my-2">— OR enter manually —</div>
          
          <UFormGroup label="Customer Name" hint="For walk-in or new customers" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.customer_name" placeholder="e.g., PT ABC" />
          </UFormGroup>
        </div>
        
        <!-- Shipping Address with OpenStreetMap -->
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3 flex items-center gap-2">
            <UIcon name="i-heroicons-map-pin" />
            Shipping Address
          </h4>
          
          <UFormGroup label="Search Address" hint="Search location via OpenStreetMap" :ui="{ hint: 'text-xs text-gray-400' }">
            <div class="relative">
              <UInput 
                v-model="addressSearch" 
                placeholder="Type address to search..." 
                @input="searchAddress"
              />
              <div v-if="addressLoading" class="absolute right-3 top-2">
                <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
              </div>
            </div>
          </UFormGroup>
          
          <!-- Address search results -->
          <div v-if="addressResults.length > 0" class="border rounded-lg max-h-40 overflow-y-auto mb-3">
            <button 
              v-for="(addr, idx) in addressResults" 
              :key="idx"
              type="button"
              class="w-full text-left p-2 hover:bg-gray-100 border-b last:border-b-0 text-sm"
              @click="selectAddress(addr)"
            >
              <UIcon name="i-heroicons-map-pin" class="text-gray-400 mr-1" />
              {{ addr.display_name }}
            </button>
          </div>
          
          <UFormGroup label="Full Address" hint="Delivery destination (can be edited)" :ui="{ hint: 'text-xs text-gray-400' }">
            <UTextarea v-model="form.shipping_address" rows="2" placeholder="Full delivery address..." />
          </UFormGroup>
          
          <!-- Mini map preview -->
          <div v-if="selectedCoords" class="mt-2 rounded-lg overflow-hidden border h-32">
            <iframe 
              :src="`https://www.openstreetmap.org/export/embed.html?bbox=${selectedCoords.lon - 0.005}%2C${selectedCoords.lat - 0.005}%2C${selectedCoords.lon + 0.005}%2C${selectedCoords.lat + 0.005}&layer=mapnik&marker=${selectedCoords.lat}%2C${selectedCoords.lon}`"
              class="w-full h-full"
              frameborder="0"
            ></iframe>
          </div>
        </div>
        
        <!-- Items Section -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium flex items-center gap-2">
                <UIcon name="i-heroicons-cube" />
                Items to Ship
              </h4>
              <p class="text-xs text-gray-400">Select products from available batches. Batches are created from <NuxtLink to="/procurement/grn" class="text-blue-600 underline">Goods Receipt</NuxtLink> or <NuxtLink to="/manufacturing/production" class="text-blue-600 underline">Production</NuxtLink></p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg">
            No items added. Click "Add Item" to select products.
          </div>
          
          <div class="space-y-3 max-h-60 overflow-y-auto">
            <div v-for="(item, index) in form.items" :key="index" class="p-3 border rounded-lg bg-gray-50">
              <div class="flex gap-2 items-start">
                <UFormGroup label="Product" required class="flex-1">
                  <USelect 
                    v-model="item.product_id" 
                    :options="productOptions" 
                    placeholder="Select Product..." 
                    size="sm"
                    @change="onProductChange(index)"
                  />
                </UFormGroup>
                <UFormGroup label="Qty" required class="w-20">
                  <UInput v-model.number="item.quantity" type="number" min="1" step="1" size="sm" />
                </UFormGroup>
                <UButton 
                  icon="i-heroicons-trash" 
                  color="red" 
                  variant="ghost" 
                  size="xs"
                  class="mt-6" 
                  @click="removeItem(index)" 
                />
              </div>
              <UFormGroup label="Batch to Pick From" class="mt-2" :ui="{ hint: 'text-xs text-gray-400' }">
                <template #hint>
                  Select stock batch. Created from GRN or Production. <NuxtLink to="/inventory/stock" class="text-blue-600 underline">View Stock</NuxtLink>
                </template>
                <USelectMenu 
                  v-model="item.batch_id" 
                  :options="getBatchesForProduct(item.product_id)" 
                  placeholder="Select Batch (FIFO recommended)..." 
                  size="sm"
                  searchable
                  value-attribute="value"
                  @change="onBatchChange(index)"
                />
              </UFormGroup>
              <p v-if="item.product_id && getBatchesForProduct(item.product_id).length === 0" class="text-xs text-red-500 mt-1">
                No batches available for this product. Receive stock first.
              </p>
            </div>
          </div>
        </div>
        
        <UFormGroup label="Notes" hint="Internal notes or special instructions" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" placeholder="e.g., Handle with care, priority shipment..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- View Details Modal -->
    <UModal v-model="showDetails" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedOrder">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedOrder.do_number }}</h3>
              <p class="text-sm text-gray-500">SO: {{ selectedOrder.so_id || 'Direct' }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedOrder.status)" size="lg">{{ selectedOrder.status }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-500">Customer:</span>
              <span class="ml-2 font-medium">{{ selectedOrder.customer_name || 'Walk-in' }}</span>
            </div>
            <div>
              <span class="text-gray-500">Created:</span>
              <span class="ml-2">{{ formatDate(selectedOrder.created_at) }}</span>
            </div>
          </div>
          
          <div v-if="selectedOrder.shipping_address" class="text-sm">
            <span class="text-gray-500">Address:</span>
            <p class="mt-1">{{ selectedOrder.shipping_address }}</p>
          </div>
          
          <div class="border-t pt-4">
            <h4 class="font-medium mb-2">Items ({{ selectedOrder.items?.length || 0 }})</h4>
            <div v-for="item in (selectedOrder.items || [])" :key="item.id" class="flex justify-between items-center py-2 border-b">
              <div>
                <p class="font-medium">{{ item.product_name }}</p>
                <p class="text-xs text-gray-400">Batch: {{ item.batch_number || 'N/A' }}</p>
              </div>
              <p class="font-bold">{{ item.quantity }}</p>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDetails = false">Close</UButton>
            <UButton 
              v-if="selectedOrder.status === 'Draft'" 
              icon="i-heroicons-truck" 
              color="blue"
              @click="shipOrder(selectedOrder); showDetails = false"
            >
              Ship Order
            </UButton>
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
const showDetails = ref(false)
const shippingId = ref<string | null>(null)

const orders = ref<any[]>([])
const salesOrders = ref<any[]>([])
const products = ref<any[]>([])
const stock = ref<any[]>([])
const customers = ref<any[]>([])
const selectedOrder = ref<any>(null)

// Address search
const addressSearch = ref('')
const addressLoading = ref(false)
const addressResults = ref<any[]>([])
const selectedCoords = ref<{lat: number, lon: number} | null>(null)

const columns = [
  { key: 'do_number', label: 'DO Number', sortable: true },
  { key: 'so_id', label: 'SO Ref' },
  { key: 'customer_name', label: 'Customer' },
  { key: 'items_count', label: 'Items' },
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  so_id: '',
  customer_id: '',
  customer_name: '',
  shipping_address: '',
  notes: '',
  items: [] as any[]
})

const draftCount = computed(() => orders.value.filter(o => o.status === 'Draft').length)
const shippedCount = computed(() => orders.value.filter(o => o.status === 'Shipped').length)
const deliveredCount = computed(() => orders.value.filter(o => o.status === 'Delivered').length)

const productOptions = computed(() => products.value.map(p => ({ label: `${p.code || ''} - ${p.name}`, value: p.id })))
const customerOptions = computed(() => customers.value.map(c => ({ label: `${c.name}${c.phone ? ' - ' + c.phone : ''}`, value: c.id })))
const soOptions = computed(() => salesOrders.value.map(s => ({ label: `${s.order_number} (${s.customer_name || 'No Customer'})`, value: s.id, order_number: s.order_number, data: s })))

const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Draft: 'yellow', Shipped: 'blue', Delivered: 'green' }
  return colors[status] || 'gray'
}

const getBatchesForProduct = (productId: string) => {
  if (!productId) return []
  return stock.value
    .filter((b: any) => b.product_id === productId && b.quantity_on_hand > 0)
    .map((b: any) => ({
      value: b.id,
      label: `${b.batch_number} (Qty: ${b.quantity_on_hand})${b.expiration_date ? ' - Exp: ' + new Date(b.expiration_date).toLocaleDateString() : ''}`
    }))
}

// OpenStreetMap address search with debounce
let searchTimeout: any = null
const searchAddress = () => {
  clearTimeout(searchTimeout)
  if (addressSearch.value.length < 3) {
    addressResults.value = []
    return
  }
  
  searchTimeout = setTimeout(async () => {
    addressLoading.value = true
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(addressSearch.value)}&countrycodes=id&limit=5`,
        { headers: { 'Accept-Language': 'id' } }
      )
      addressResults.value = await response.json()
    } catch (e) {
      console.error('Address search failed:', e)
    } finally {
      addressLoading.value = false
    }
  }, 500)
}

const selectAddress = (addr: any) => {
  form.shipping_address = addr.display_name
  selectedCoords.value = { lat: parseFloat(addr.lat), lon: parseFloat(addr.lon) }
  addressResults.value = []
  addressSearch.value = ''
}

const onCustomerSelect = () => {
  const customer = customers.value.find(c => c.id === form.customer_id)
  if (customer) {
    form.customer_name = customer.name
    if (customer.address) {
      form.shipping_address = customer.address
    }
  }
}

const onSoSelect = (val: string) => {
  if (!val) return
  
  // val is the UUID of the selected Sales Order
  const so = salesOrders.value.find(s => s.id === val)
  if (!so) return

  // Auto-fill customer info
  form.customer_name = so.customer_name || ''
  if (so.customer_id) {
    form.customer_id = so.customer_id
    const customer = customers.value.find(c => c.id === so.customer_id)
    if (customer?.address) {
      form.shipping_address = customer.address
    }
  }

  // Auto-fill items
  if (so.Items && so.Items.length > 0) {
    form.items = so.Items.map((item: any) => {
      const product = products.value.find(p => p.id === item.product_id)
      const batches = getBatchesForProduct(item.product_id)
      const batch = batches.length > 0 ? batches[0] : null
      return {
        product_id: item.product_id,
        product_name: product?.name || '',
        quantity: item.quantity,
        batch_id: batch ? batch.value : '',
        batch_number: batch ? batch.batch_number : ''
      }
    })
  } else {
    form.items = [{ product_id: '', product_name: '', quantity: 1, batch_id: '', batch_number: '' }]
  }

  toast.add({ title: 'Sales Order Linked', description: `Loaded info from ${so.order_number}`, color: 'blue' })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [doRes, prodRes, stockRes, custRes, soRes] = await Promise.all([
      $api.get('/delivery/orders').catch(() => ({ data: [] })),
      $api.get('/manufacturing/products').catch(() => ({ data: [] })),
      $api.get('/inventory/stock').catch(() => ({ data: [] })),
      $api.get('/crm/customers').catch(() => ({ data: [] })),
      $api.get('/sales/orders').catch(() => ({ data: [] }))
    ])
    orders.value = doRes.data?.data || []
    products.value = prodRes.data?.data || []
    stock.value = stockRes.data?.data || []
    salesOrders.value = soRes.data?.data || []
    const cData = custRes.data?.data
    customers.value = Array.isArray(cData) ? cData : (cData?.data || [])
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, {
    so_id: '',
    customer_id: '',
    customer_name: '',
    shipping_address: '',
    notes: '',
    items: [{ product_id: '', product_name: '', quantity: 1, batch_id: '', batch_number: '' }]
  })
  addressSearch.value = ''
  addressResults.value = []
  selectedCoords.value = null
  isOpen.value = true
}

const addItem = () => form.items.push({ product_id: '', product_name: '', quantity: 1, batch_id: '', batch_number: '' })
const removeItem = (idx: number) => form.items.splice(idx, 1)

const onProductChange = (idx: number) => {
  const p = products.value.find(prod => prod.id === form.items[idx].product_id)
  if (p) {
    form.items[idx].product_name = p.name
  }
  // Reset batch when product changes
  form.items[idx].batch_id = ''
  form.items[idx].batch_number = ''
}

const onBatchChange = (idx: number) => {
  const batches = getBatchesForProduct(form.items[idx].product_id)
  const b = batches.find(batch => batch.value === form.items[idx].batch_id)
  if (b) {
    form.items[idx].batch_number = b.batch_number
  }
}

const viewDetails = async (row: any) => {
  try {
    const res = await $api.get(`/delivery/${row.id}`)
    selectedOrder.value = res.data?.data || res.data
    showDetails.value = true
  } catch (e) {
    selectedOrder.value = row
    showDetails.value = true
  }
}

const createDo = async () => {
  if (form.items.length === 0 || !form.items.some(i => i.product_id)) {
    toast.add({ title: 'Validation Error', description: 'Please add at least one item with product selected', color: 'red' })
    return
  }
  
  // Filter out empty items
  const validItems = form.items.filter(i => i.product_id && i.quantity > 0)
  
  submitting.value = true
  try {
    await $api.post('/delivery/create', {
      ...form,
      items: validItems
    })
    toast.add({ title: 'Created', description: 'Delivery order created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to create delivery order', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const shipOrder = async (row: any) => {
  if (!confirm('Ship this order? Stock will be deducted from selected batches.')) return
  
  shippingId.value = row.id
  try {
    await $api.post(`/delivery/${row.id}/ship`)
    toast.add({ title: 'Shipped', description: 'Order shipped successfully, stock deducted', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to ship (Check stock availability)', color: 'red' })
  } finally {
    shippingId.value = null
  }
}

const exportData = (format: string) => {
  const data = orders.value.map((o: any) => ({
    'DO Number': o.do_number || '',
    'SO Ref': o.so_id || '',
    'Customer': o.customer_name || 'Walk-in',
    'Items': o.items_count || 0,
    'Status': o.status,
    'Date': formatDate(o.created_at)
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `delivery_orders.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `DOs exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Delivery Orders</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Delivery Orders Report</h1>
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
