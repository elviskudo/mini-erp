<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Production Orders</h1>
        <p class="text-gray-500">Manage manufacturing production orders</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="showModal = true">
        New Production Order
      </UButton>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ stats.draft }}</p>
          <p class="text-sm text-gray-500">Draft</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ stats.inProgress }}</p>
          <p class="text-sm text-gray-500">In Progress</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.completed }}</p>
          <p class="text-sm text-gray-500">Completed</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ stats.cancelled }}</p>
          <p class="text-sm text-gray-500">Cancelled</p>
        </div>
      </UCard>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="flex flex-col sm:flex-row gap-4">
        <UInput v-model="search" placeholder="Search orders..." icon="i-heroicons-magnifying-glass" class="flex-1" />
        <USelect v-model="statusFilter" :options="statusOptions" placeholder="All Status" class="w-full sm:w-40" />
      </div>
    </UCard>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="filteredOrders" :loading="loading">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">
            {{ row.status }}
          </UBadge>
        </template>
        <template #progress-data="{ row }">
          <div class="w-24">
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  class="bg-primary-500 h-2 rounded-full" 
                  :style="{ width: `${row.progress}%` }"
                ></div>
              </div>
              <span class="text-xs text-gray-500">{{ row.progress }}%</span>
            </div>
          </div>
        </template>
        <template #actions-data="{ row }">
          <UDropdown :items="getActions(row)">
            <UButton icon="i-heroicons-ellipsis-vertical" color="gray" variant="ghost" />
          </UDropdown>
        </template>
      </UTable>
      
      <!-- Pagination -->
      <div class="flex items-center justify-between px-4 py-3 border-t">
        <p class="text-sm text-gray-500">Showing {{ filteredOrders.length }} of {{ orders.length }} orders</p>
        <UPagination v-model="page" :total="orders.length" :page-count="10" />
      </div>
    </UCard>

    <!-- Create Slideover -->
    <USlideover v-model="showModal">
      <div class="p-6 flex flex-col h-full">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold">New Production Order</h3>
          <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="showModal = false" />
        </div>
        
        <div class="flex-1 space-y-4 overflow-y-auto">
          <UFormGroup label="Product" required>
            <USelect v-model="form.productId" :options="products" placeholder="Select product" />
          </UFormGroup>
          
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Quantity" required>
              <UInput v-model="form.quantity" type="number" min="1" />
            </UFormGroup>
            <UFormGroup label="Work Center">
              <USelect v-model="form.workCenterId" :options="workCenters" placeholder="Select" />
            </UFormGroup>
          </div>
          
          <UFormGroup label="Scheduled Date">
            <UInput v-model="form.scheduledDate" type="date" />
          </UFormGroup>
          
          <UFormGroup label="Notes">
            <UTextarea v-model="form.notes" rows="3" placeholder="Additional notes..." />
          </UFormGroup>
        </div>
        
        <div class="flex justify-end gap-3 pt-6 border-t mt-6">
          <UButton variant="ghost" @click="showModal = false">Cancel</UButton>
          <UButton @click="createOrder">Create Order</UButton>
        </div>
      </div>
    </USlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const loading = ref(false)
const showModal = ref(false)
const search = ref('')
const statusFilter = ref('')
const page = ref(1)

const form = reactive({
  productId: '',
  quantity: 1,
  workCenterId: '',
  scheduledDate: '',
  notes: ''
})

const stats = reactive({
  draft: 2,
  inProgress: 5,
  completed: 12,
  cancelled: 1
})

const statusOptions = [
  { label: 'All Status', value: '' },
  { label: 'Draft', value: 'Draft' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Completed', value: 'Completed' },
  { label: 'Cancelled', value: 'Cancelled' }
]

const columns = [
  { key: 'orderNo', label: 'Order No' },
  { key: 'product', label: 'Product' },
  { key: 'quantity', label: 'Qty' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'scheduledDate', label: 'Scheduled' },
  { key: 'actions', label: '' }
]

const orders = ref([
  { id: 1, orderNo: 'PO-001', product: 'Widget A', quantity: 100, status: 'In Progress', progress: 45, scheduledDate: '2024-01-15' },
  { id: 2, orderNo: 'PO-002', product: 'Widget B', quantity: 50, status: 'Draft', progress: 0, scheduledDate: '2024-01-20' },
  { id: 3, orderNo: 'PO-003', product: 'Component X', quantity: 200, status: 'Completed', progress: 100, scheduledDate: '2024-01-10' },
  { id: 4, orderNo: 'PO-004', product: 'Widget A', quantity: 75, status: 'In Progress', progress: 80, scheduledDate: '2024-01-18' },
  { id: 5, orderNo: 'PO-005', product: 'Assembly Y', quantity: 25, status: 'Cancelled', progress: 0, scheduledDate: '2024-01-12' }
])

const products = [
  { label: 'Widget A', value: '1' },
  { label: 'Widget B', value: '2' },
  { label: 'Component X', value: '3' }
]

const workCenters = [
  { label: 'Assembly Line 1', value: '1' },
  { label: 'Assembly Line 2', value: '2' },
  { label: 'CNC Machine', value: '3' }
]

const filteredOrders = computed(() => {
  return orders.value.filter(order => {
    const matchSearch = !search.value || 
      order.orderNo.toLowerCase().includes(search.value.toLowerCase()) ||
      order.product.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !statusFilter.value || order.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

const getStatusColor = (status: string) => {
  switch (status) {
    case 'Draft': return 'gray'
    case 'In Progress': return 'yellow'
    case 'Completed': return 'green'
    case 'Cancelled': return 'red'
    default: return 'gray'
  }
}

const getActions = (row: any) => [[
  { label: 'View Details', icon: 'i-heroicons-eye', click: () => {} },
  { label: 'Edit', icon: 'i-heroicons-pencil', click: () => {} },
  { label: 'Start Production', icon: 'i-heroicons-play', click: () => {} }
], [
  { label: 'Cancel', icon: 'i-heroicons-x-mark', click: () => {} }
]]

const createOrder = () => {
  showModal.value = false
  // TODO: API call
}
</script>
