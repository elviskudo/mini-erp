<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Stock Movements</h1>
        <p class="text-gray-500">Track inventory movements history</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" variant="outline" @click="refreshData">
        Refresh
      </UButton>
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
      <div class="flex flex-col sm:flex-row gap-4">
        <UInput v-model="search" placeholder="Search by item or reference..." icon="i-heroicons-magnifying-glass" class="flex-1" />
        <USelect v-model="typeFilter" :options="typeOptions" placeholder="All Types" class="w-full sm:w-40" />
        <UInput v-model="dateFrom" type="date" class="w-full sm:w-40" />
        <UInput v-model="dateTo" type="date" class="w-full sm:w-40" />
      </div>
    </UCard>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="filteredMovements" :loading="loading">
        <template #type-data="{ row }">
          <div class="flex items-center gap-2">
            <UIcon :name="getTypeIcon(row.type)" :class="getTypeColor(row.type)" class="w-4 h-4" />
            <span>{{ row.type }}</span>
          </div>
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
        <p class="text-sm text-gray-500">Showing {{ filteredMovements.length }} movements</p>
        <UPagination v-model="page" :total="movements.length" :page-count="20" />
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const loading = ref(false)
const search = ref('')
const typeFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const page = ref(1)

const stats = reactive({
  inbound: 156,
  outbound: 98,
  transfer: 23,
  adjustment: 12
})

const typeOptions = [
  { label: 'All Types', value: '' },
  { label: 'Inbound', value: 'Inbound' },
  { label: 'Outbound', value: 'Outbound' },
  { label: 'Transfer', value: 'Transfer' },
  { label: 'Adjustment', value: 'Adjustment' }
]

const columns = [
  { key: 'reference', label: 'Reference' },
  { key: 'type', label: 'Type' },
  { key: 'item', label: 'Item' },
  { key: 'quantity', label: 'Qty' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'timestamp', label: 'Date/Time' },
  { key: 'user', label: 'By' }
]

const movements = ref([
  { id: 1, reference: 'GR-001', type: 'Inbound', item: 'Raw Material A', quantity: 500, warehouse: 'Main Warehouse', timestamp: '2024-01-15T09:30:00', user: 'John' },
  { id: 2, reference: 'DO-045', type: 'Outbound', item: 'Widget A', quantity: -100, warehouse: 'Main Warehouse', timestamp: '2024-01-15T10:15:00', user: 'Jane' },
  { id: 3, reference: 'TR-012', type: 'Transfer', item: 'Component X', quantity: 50, warehouse: 'WH-2 → WH-1', timestamp: '2024-01-15T11:00:00', user: 'Bob' },
  { id: 4, reference: 'ADJ-003', type: 'Adjustment', item: 'Screw M5', quantity: -25, warehouse: 'Main Warehouse', timestamp: '2024-01-14T16:45:00', user: 'Admin' },
  { id: 5, reference: 'GR-002', type: 'Inbound', item: 'Packaging Box', quantity: 1000, warehouse: 'Main Warehouse', timestamp: '2024-01-14T14:20:00', user: 'John' },
  { id: 6, reference: 'DO-046', type: 'Outbound', item: 'Widget B', quantity: -75, warehouse: 'Secondary WH', timestamp: '2024-01-14T13:00:00', user: 'Jane' }
])

const filteredMovements = computed(() => {
  return movements.value.filter(m => {
    const matchSearch = !search.value || 
      m.item.toLowerCase().includes(search.value.toLowerCase()) ||
      m.reference.toLowerCase().includes(search.value.toLowerCase())
    const matchType = !typeFilter.value || m.type === typeFilter.value
    return matchSearch && matchType
  })
})

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'Inbound': return 'i-heroicons-arrow-down-tray'
    case 'Outbound': return 'i-heroicons-arrow-up-tray'
    case 'Transfer': return 'i-heroicons-arrows-right-left'
    case 'Adjustment': return 'i-heroicons-clipboard-document-check'
    default: return 'i-heroicons-question-mark-circle'
  }
}

const getTypeColor = (type: string) => {
  switch (type) {
    case 'Inbound': return 'text-green-600'
    case 'Outbound': return 'text-red-600'
    case 'Transfer': return 'text-blue-600'
    case 'Adjustment': return 'text-yellow-600'
    default: return 'text-gray-600'
  }
}

const formatDate = (timestamp: string) => {
  return new Date(timestamp).toLocaleDateString()
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const refreshData = () => {
  loading.value = true
  setTimeout(() => loading.value = false, 1000)
}
</script>
