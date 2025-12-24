<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Stock Status</h1>
        <p class="text-gray-500">Current inventory levels</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchStock">Refresh</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-sm text-gray-500">Total Items</div>
        <div class="text-2xl font-bold">{{ stockItems.length }}</div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-sm text-gray-500">Total Quantity</div>
        <div class="text-2xl font-bold">{{ totalQty }}</div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-sm text-gray-500">Manufactured</div>
        <div class="text-2xl font-bold text-blue-600">{{ manufacturedCount }}</div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-sm text-gray-500">Purchased</div>
        <div class="text-2xl font-bold text-green-600">{{ purchasedCount }}</div>
      </UCard>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="flex flex-col sm:flex-row gap-4 flex-wrap">
        <UInput v-model="search" placeholder="Search batch or product..." icon="i-heroicons-magnifying-glass" class="flex-1 min-w-[200px]" />
        <USelectMenu v-model="filters.warehouse" :options="warehouseOptions" placeholder="All Warehouses" class="w-full sm:w-48" />
        <USelectMenu v-model="filters.origin" :options="originOptions" placeholder="All Origins" class="w-full sm:w-40" />
        <UInput v-model="filters.expiresFrom" type="date" class="w-full sm:w-36" placeholder="Expires From" />
        <UInput v-model="filters.expiresTo" type="date" class="w-full sm:w-36" placeholder="Expires To" />
        <USelectMenu v-model="filters.limit" :options="limitOptions" class="w-full sm:w-24" />
        <UButton icon="i-heroicons-funnel" @click="fetchStock">Filter</UButton>
        <UButton variant="ghost" @click="resetFilters">Reset</UButton>
      </div>
    </UCard>

    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="filteredItems" :loading="loading">
        <template #product-data="{ row }">
          <div class="flex items-center gap-2">
            <img v-if="row.product?.image_url" :src="row.product.image_url" class="w-8 h-8 rounded object-cover" />
            <div v-else class="w-8 h-8 rounded bg-gray-200 flex items-center justify-center">
              <UIcon name="i-heroicons-cube" class="text-gray-400" />
            </div>
            <span>{{ row.product?.name || 'Unknown' }}</span>
          </div>
        </template>
        <template #qr_code_data-data="{ row }">
          <UButton v-if="row.qr_code_data" size="xs" variant="ghost" icon="i-heroicons-qr-code" @click="showQR(row)" />
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #origin_type-data="{ row }">
          <UBadge :color="row.origin_type === 'MANUFACTURED' ? 'blue' : 'green'" size="sm">
            {{ row.origin_type }}
          </UBadge>
        </template>
        <template #expiration_date-data="{ row }">
          <span :class="{'text-red-500 font-bold': isExpired(row.expiration_date)}">
            {{ row.expiration_date ? new Date(row.expiration_date).toLocaleDateString() : 'N/A' }}
          </span>
        </template>
        <template #unit_cost-data="{ row }">
          {{ formatCurrency(row.unit_cost) }}
        </template>
        <template #actions-data="{ row }">
          <UDropdown :items="getRowActions(row)">
            <UButton icon="i-heroicons-ellipsis-vertical" variant="ghost" size="sm" />
          </UDropdown>
        </template>
      </UTable>
      
      <!-- Pagination info -->
      <div class="flex items-center justify-between px-4 py-3 border-t">
        <p class="text-sm text-gray-500">Showing {{ filteredItems.length }} items</p>
      </div>
    </UCard>

    <!-- Set Expiry Modal -->
    <UModal v-model="showExpiryModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Set Expiration Date</h3>
        </template>
        <div class="space-y-4">
          <p class="text-sm text-gray-600">Product: <strong>{{ selectedBatch?.product?.name }}</strong></p>
          <p class="text-sm text-gray-600">Batch: <strong>{{ selectedBatch?.batch_number }}</strong></p>
          <UFormGroup label="Expiration Date">
            <UInput v-model="expiryForm.expiration_date" type="date" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showExpiryModal = false">Cancel</UButton>
            <UButton @click="saveExpiry">Save</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Move Location Modal -->
    <UModal v-model="showMoveModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Move to Location</h3>
        </template>
        <div class="space-y-4">
          <p class="text-sm text-gray-600">Product: <strong>{{ selectedBatch?.product?.name }}</strong></p>
          <p class="text-sm text-gray-600">Current: <strong>{{ selectedBatch?.location?.name }}</strong></p>
          <UFormGroup label="New Location">
            <USelectMenu v-model="moveForm.location_id" :options="locations" option-attribute="name" value-attribute="id" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showMoveModal = false">Cancel</UButton>
            <UButton @click="moveLocation">Move</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- QR Code Modal -->
    <UModal v-model="showQRModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">QR Code Data</h3>
        </template>
        <div class="p-4 text-center">
          <p class="font-mono text-sm bg-gray-100 p-4 rounded break-all">{{ selectedBatch?.qr_code_data }}</p>
        </div>
        <template #footer>
          <div class="flex justify-end">
            <UButton @click="showQRModal = false">Close</UButton>
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
const toast = useToast()
const loading = ref(false)
const search = ref('')
const stockItems = ref<any[]>([])
const locations = ref<any[]>([])

// Filters
const filters = reactive({
  warehouse: '',
  origin: '',
  expiresFrom: '',
  expiresTo: '',
  limit: 50
})

const warehouseOptions = ref([{ label: 'All Warehouses', value: '' }])
const originOptions = [
  { label: 'All Origins', value: '' },
  { label: 'Manufactured', value: 'MANUFACTURED' },
  { label: 'Purchased', value: 'PURCHASED' }
]
const limitOptions = [
  { label: '20', value: 20 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
  { label: '200', value: 200 }
]

// Modal states
const showExpiryModal = ref(false)
const showMoveModal = ref(false)
const showQRModal = ref(false)
const selectedBatch = ref<any>(null)

// Forms
const expiryForm = reactive({ expiration_date: '' })
const moveForm = reactive({ location_id: '' })

const columns = [
  { key: 'product', label: 'Product' },
  { key: 'batch_number', label: 'Batch' },
  { key: 'qr_code_data', label: 'QR' },
  { key: 'quantity_on_hand', label: 'Qty' },
  { key: 'warehouse.name', label: 'Warehouse' },
  { key: 'location.name', label: 'Location' },
  { key: 'origin_type', label: 'Origin' },
  { key: 'unit_cost', label: 'Unit Cost' },
  { key: 'expiration_date', label: 'Expires' },
  { key: 'actions', label: '' }
]

const totalQty = computed(() => stockItems.value.reduce((sum: number, item: any) => sum + (item.quantity_on_hand || 0), 0))
const manufacturedCount = computed(() => stockItems.value.filter((item: any) => item.origin_type === 'MANUFACTURED').length)
const purchasedCount = computed(() => stockItems.value.filter((item: any) => item.origin_type === 'PURCHASED').length)

const filteredItems = computed(() => {
  let items = stockItems.value
  if (search.value) {
    const s = search.value.toLowerCase()
    items = items.filter((item: any) =>
      item.batch_number?.toLowerCase().includes(s) ||
      item.product?.name?.toLowerCase().includes(s)
    )
  }
  return items
})

const isExpired = (date: string) => {
  if (!date) return false
  return new Date(date) < new Date()
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0)
}

const getRowActions = (row: any) => [
  [{
    label: 'Set Expiry',
    icon: 'i-heroicons-calendar',
    click: () => {
      selectedBatch.value = row
      expiryForm.expiration_date = row.expiration_date ? row.expiration_date.split('T')[0] : ''
      showExpiryModal.value = true
    }
  }, {
    label: 'Move Location',
    icon: 'i-heroicons-arrow-right',
    click: () => {
      selectedBatch.value = row
      moveForm.location_id = ''
      showMoveModal.value = true
    }
  }]
]

const showQR = (row: any) => {
  selectedBatch.value = row
  showQRModal.value = true
}

const fetchWarehouses = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const res: any = await $fetch('/api/inventory/warehouses', { headers })
    warehouseOptions.value = [
      { label: 'All Warehouses', value: '' },
      ...res.map((w: any) => ({ label: w.name, value: w.id }))
    ]
  } catch (e) {
    console.error('Failed to fetch warehouses', e)
  }
}

const fetchLocations = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    locations.value = await $fetch('/api/inventory/locations-for-move', { headers })
  } catch (e) {
    console.error('Failed to fetch locations', e)
  }
}

const fetchStock = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    stockItems.value = await $fetch('/api/inventory/stock', { headers })
  } catch (e) {
    console.error('Failed to fetch stock', e)
    toast.add({ title: 'Error', description: 'Failed to load stock data', color: 'red' })
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.warehouse = ''
  filters.origin = ''
  filters.expiresFrom = ''
  filters.expiresTo = ''
  filters.limit = 50
  search.value = ''
  fetchStock()
}

const saveExpiry = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/inventory/stock/${selectedBatch.value.id}/set-expiry`, {
      method: 'PUT',
      headers,
      body: { expiration_date: expiryForm.expiration_date }
    })
    toast.add({ title: 'Success', description: 'Expiration date updated', color: 'green' })
    showExpiryModal.value = false
    fetchStock()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to update expiration date', color: 'red' })
  }
}

const moveLocation = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/inventory/stock/${selectedBatch.value.id}/move-location`, {
      method: 'PUT',
      headers,
      body: { location_id: moveForm.location_id }
    })
    toast.add({ title: 'Success', description: 'Location updated', color: 'green' })
    showMoveModal.value = false
    fetchStock()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to move location', color: 'red' })
  }
}

const exportData = async (format: string) => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const params = new URLSearchParams()
    if (filters.origin) params.append('origin_type', filters.origin)
    if (filters.warehouse) params.append('warehouse_id', filters.warehouse)
    params.append('format', format)
    
    const res = await $fetch(`/api/export/stock?${params.toString()}`, { 
      headers,
      responseType: 'blob'
    })
    
    const blob = res as Blob
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `stock_${new Date().toISOString().split('T')[0]}.${format}`
    a.click()
    window.URL.revokeObjectURL(url)
    toast.add({ title: 'Exported', description: `Data exported to ${format.toUpperCase()}`, color: 'green' })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to export data', color: 'red' })
  }
}

onMounted(() => {
  fetchStock()
  fetchLocations()
  fetchWarehouses()
})
</script>
