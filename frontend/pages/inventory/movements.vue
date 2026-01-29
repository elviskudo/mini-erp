<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Stock Movements</h1>
        <p class="text-gray-500">Track inventory movements history</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">
          CSV
        </UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">
          XLS
        </UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">
          PDF
        </UButton>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="refreshData">
          Refresh
        </UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
            <UIcon name="i-heroicons-arrow-down-tray" class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats.inbound }}</p>
            <p class="text-sm text-gray-500">Inbound</p>
          </div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
            <UIcon name="i-heroicons-arrow-up-tray" class="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats.outbound }}</p>
            <p class="text-sm text-gray-500">Outbound</p>
          </div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
            <UIcon name="i-heroicons-arrows-right-left" class="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats.transfer }}</p>
            <p class="text-sm text-gray-500">Transfers</p>
          </div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center">
            <UIcon name="i-heroicons-clipboard-document-check" class="w-5 h-5 text-yellow-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats.adjustment }}</p>
            <p class="text-sm text-gray-500">Adjustments</p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="flex flex-col sm:flex-row gap-4 flex-wrap">
        <UInput v-model="search" placeholder="Search by item or reference..." icon="i-heroicons-magnifying-glass" class="flex-1 min-w-[200px]" />
        <USelectMenu v-model="filters.type" :options="typeOptions" placeholder="All Types" class="w-full sm:w-40" />
        <USelectMenu v-model="filters.warehouse" :options="warehouseOptions" placeholder="All Warehouses" class="w-full sm:w-48" />
        <UInput v-model="filters.dateFrom" type="date" class="w-full sm:w-40" placeholder="From" />
        <UInput v-model="filters.dateTo" type="date" class="w-full sm:w-40" placeholder="To" />
        <USelectMenu v-model="filters.limit" :options="limitOptions" class="w-full sm:w-24" />
        <UButton icon="i-heroicons-funnel" @click="applyFilters">Filter</UButton>
        <UButton variant="ghost" @click="resetFilters">Reset</UButton>
      </div>
    </UCard>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="filteredMovements" :loading="loading">
        <template #type-data="{ row }">
          <div class="flex items-center gap-2">
            <UIcon :name="getTypeIcon(row.movement_type)" :class="getTypeColor(row.movement_type)" class="w-4 h-4" />
            <span class="capitalize">{{ row.movement_type?.toLowerCase() }}</span>
          </div>
        </template>
        <template #item-data="{ row }">
          <div>
            <p class="font-medium">{{ row.product?.name || '-' }}</p>
            <p class="text-xs text-gray-500">{{ row.product?.code }}</p>
          </div>
        </template>
        <template #reference-data="{ row }">
          <div>
            <p class="text-sm font-medium">{{ row.reference_id || '-' }}</p>
            <p class="text-xs text-gray-400 capitalize">{{ row.reference_type?.toLowerCase() }}</p>
          </div>
        </template>
        <template #warehouse-data="{ row }">
          <span>{{ row.warehouse?.name || '-' }}</span>
        </template>
        <template #user-data="{ row }">
          <span class="text-xs text-gray-500">{{ row.created_by || 'System' }}</span>
        </template>
        <template #quantity-data="{ row }">
          <span :class="row.quantity > 0 ? 'text-green-600' : 'text-red-600'" class="font-medium">
            {{ row.quantity > 0 ? '+' : '' }}{{ row.quantity }}
          </span>
        </template>
        <template #timestamp-data="{ row }">
          <div>
            <p class="text-sm">{{ formatDate(row.timestamp) }}</p>
            <p class="text-xs text-gray-500">{{ formatTime(row.timestamp) }}</p>
          </div>
        </template>
      </UTable>
      
      <!-- Pagination -->
      <div class="flex items-center justify-between px-4 py-3 border-t">
        <p class="text-sm text-gray-500">Showing {{ movements.length }} of {{ total }} movements</p>
        <UPagination v-model="page" :total="total" :page-count="filters.limit" @update:modelValue="changePage" />
      </div>
    </UCard>
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
const page = ref(1)
const total = ref(0)

const stats = reactive({
  inbound: 0,
  outbound: 0,
  transfer: 0,
  adjustment: 0
})

const filters = reactive({
  type: '',
  warehouse: '',
  dateFrom: '',
  dateTo: '',
  limit: 20
})

const typeOptions = [
  { label: 'All Types', value: '' },
  { label: 'Inbound', value: 'Inbound' },
  { label: 'Outbound', value: 'Outbound' },
  { label: 'Transfer', value: 'Transfer' },
  { label: 'Adjustment', value: 'Adjustment' }
]

const limitOptions = [
  { label: '10', value: 10 },
  { label: '20', value: 20 },
  { label: '50', value: 50 },
  { label: '100', value: 100 }
]

const warehouseOptions = ref([{ label: 'All Warehouses', value: '' }])

const columns = [
  { key: 'reference', label: 'Reference' },
  { key: 'type', label: 'Type' },
  { key: 'item', label: 'Item' },
  { key: 'quantity', label: 'Qty' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'timestamp', label: 'Date/Time' },
  { key: 'user', label: 'By' }
]

const movements = ref<any[]>([])

const filteredMovements = computed(() => {
  if (!search.value) return movements.value
  return movements.value.filter((m: any) => {
    const term = search.value.toLowerCase()
    return m.product?.name?.toLowerCase().includes(term) ||
      m.product?.code?.toLowerCase().includes(term) ||
      m.reference_id?.toLowerCase().includes(term) ||
      m.warehouse?.name?.toLowerCase().includes(term)
  })
})

const getTypeIcon = (type: string) => {
  if (!type) return 'i-heroicons-question-mark-circle'
  const t = type.toUpperCase()
  if (t === 'IN' || t === 'INBOUND') return 'i-heroicons-arrow-down-tray'
  if (t === 'OUT' || t === 'OUTBOUND') return 'i-heroicons-arrow-up-tray'
  if (t === 'TRANSFER') return 'i-heroicons-arrows-right-left'
  if (t === 'ADJUSTMENT') return 'i-heroicons-clipboard-document-check'
  return 'i-heroicons-question-mark-circle'
}

const getTypeColor = (type: string) => {
  if (!type) return 'text-gray-600'
  const t = type.toUpperCase()
  if (t === 'IN' || t === 'INBOUND') return 'text-green-600'
  if (t === 'OUT' || t === 'OUTBOUND') return 'text-red-600'
  if (t === 'TRANSFER') return 'text-blue-600'
  if (t === 'ADJUSTMENT') return 'text-yellow-600'
  return 'text-gray-600'
}

const formatDate = (timestamp: string) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleDateString()
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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

const refreshData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    const params = new URLSearchParams()
    if (filters.type) params.append('movement_type', filters.type)
    if (filters.warehouse) params.append('warehouse_id', filters.warehouse)
    if (filters.dateFrom) params.append('date_from', new Date(filters.dateFrom).toISOString())
    if (filters.dateTo) params.append('date_to', new Date(filters.dateTo + 'T23:59:59').toISOString())
    params.append('limit', String(filters.limit))
    params.append('offset', String((page.value - 1) * filters.limit))
    
    const res: any = await $fetch(`/api/inventory/movements?${params.toString()}`, { headers })
    
    // API returns { "success": true, "data": { "movements": [], "total": 10, "stats": {...} } }
    if (res.data) {
      movements.value = res.data.movements || []
      total.value = res.data.total || 0
      if (res.data.stats) {
        stats.inbound = res.data.stats.inbound || 0
        stats.outbound = res.data.stats.outbound || 0
        stats.transfer = res.data.stats.transfer || 0
        stats.adjustment = res.data.stats.adjustment || 0
      }
    }
  } catch (e) {
    console.error('Failed to fetch movements', e)
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  page.value = 1
  refreshData()
}

const resetFilters = () => {
  filters.type = ''
  filters.warehouse = ''
  filters.dateFrom = ''
  filters.dateTo = ''
  filters.limit = 20
  page.value = 1
  search.value = ''
  refreshData()
}

const changePage = (newPage: number) => {
  page.value = newPage
  refreshData()
}

const exportData = async (format: string) => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const params = new URLSearchParams()
    if (filters.type) params.append('movement_type', filters.type)
    if (filters.warehouse) params.append('warehouse_id', filters.warehouse)
    if (filters.dateFrom) params.append('date_from', new Date(filters.dateFrom).toISOString())
    if (filters.dateTo) params.append('date_to', new Date(filters.dateTo + 'T23:59:59').toISOString())
    params.append('format', format)
    
    const res = await $fetch(`/api/export/movements?${params.toString()}`, { 
      headers,
      responseType: 'blob'
    })
    
    const blob = res as Blob
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `movements_${new Date().toISOString().split('T')[0]}.${format}`
    a.click()
    window.URL.revokeObjectURL(url)
    toast.add({ title: 'Exported', description: `Data exported to ${format.toUpperCase()}`, color: 'green' })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to export data', color: 'red' })
  }
}

onMounted(() => {
  fetchWarehouses()
  refreshData()
})
</script>
