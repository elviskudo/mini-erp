<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Work Orders</h2>
        <p class="text-gray-500">Manage shop floor operations, track work order progress and operator assignments</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData" :loading="loading">Refresh</UButton>
        <UButton icon="i-heroicons-plus" color="primary" @click="openCreate">New Work Order</UButton>
      </div>
    </div>

    <!-- Tabs -->
    <UTabs v-model="activeTab" :items="tabs" class="w-full">
      <template #item="{ item }">
        <!-- Dashboard Tab -->
        <div v-if="item.key === 'dashboard'" class="space-y-4 pt-4">
          <!-- Stats Cards -->
          <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <UCard :ui="{ body: { padding: 'p-4' } }">
              <div class="text-center">
                <p class="text-2xl font-bold">{{ workOrders.length }}</p>
                <p class="text-sm text-gray-500">Total WOs</p>
              </div>
            </UCard>
            <UCard :ui="{ body: { padding: 'p-4' } }" class="bg-blue-50">
              <div class="text-center">
                <p class="text-2xl font-bold text-blue-600">{{ statusCounts.pending }}</p>
                <p class="text-sm text-gray-500">Pending</p>
              </div>
            </UCard>
            <UCard :ui="{ body: { padding: 'p-4' } }" class="bg-yellow-50">
              <div class="text-center">
                <p class="text-2xl font-bold text-yellow-600">{{ statusCounts.in_progress }}</p>
                <p class="text-sm text-gray-500">In Progress</p>
              </div>
            </UCard>
            <UCard :ui="{ body: { padding: 'p-4' } }" class="bg-green-50">
              <div class="text-center">
                <p class="text-2xl font-bold text-green-600">{{ statusCounts.completed }}</p>
                <p class="text-sm text-gray-500">Completed</p>
              </div>
            </UCard>
            <UCard :ui="{ body: { padding: 'p-4' } }" class="bg-red-50">
              <div class="text-center">
                <p class="text-2xl font-bold text-red-600">{{ statusCounts.on_hold }}</p>
                <p class="text-sm text-gray-500">On Hold</p>
              </div>
            </UCard>
          </div>

          <!-- Work Center Status -->
          <UCard>
            <template #header><h3 class="font-semibold">Work Center Status</h3></template>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div v-for="wc in workCenterStats" :key="wc.id" class="p-4 border rounded-lg">
                <div class="flex justify-between items-start mb-2">
                  <h4 class="font-medium">{{ wc.name }}</h4>
                  <UBadge :color="wc.is_active ? 'green' : 'gray'" variant="subtle" size="xs">
                    {{ wc.is_active ? 'Active' : 'Idle' }}
                  </UBadge>
                </div>
                <div class="space-y-1 text-sm">
                  <p><span class="text-gray-500">Active WOs:</span> {{ wc.active_count }}</p>
                  <p><span class="text-gray-500">Utilization:</span> {{ wc.utilization }}%</p>
                </div>
                <div class="mt-2 w-full bg-gray-200 rounded h-2">
                  <div class="h-2 rounded bg-blue-500" :style="{ width: `${wc.utilization}%` }"></div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Today's Activity -->
          <UCard>
            <template #header><h3 class="font-semibold">Today's Work Orders</h3></template>
            <UTable :columns="columns" :rows="todaysOrders" :loading="loading">
              <template #work_order_no-data="{ row }">
                <span class="font-mono text-blue-600">{{ row.work_order_no }}</span>
              </template>
              <template #status-data="{ row }">
                <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
              </template>
              <template #progress-data="{ row }">
                <div class="flex items-center gap-2">
                  <div class="w-20 bg-gray-200 rounded h-2">
                    <div class="h-2 rounded bg-green-500" :style="{ width: `${row.progress}%` }"></div>
                  </div>
                  <span class="text-xs">{{ row.progress }}%</span>
                </div>
              </template>
              <template #actions-data="{ row }">
                <div class="flex gap-1">
                  <UButton v-if="row.status === 'Pending'" icon="i-heroicons-play" size="xs" color="green" variant="ghost" @click="startWO(row)" title="Start" />
                  <UButton v-if="row.status === 'In Progress'" icon="i-heroicons-pause" size="xs" color="yellow" variant="ghost" @click="pauseWO(row)" title="Pause" />
                  <UButton v-if="row.status === 'In Progress'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="completeWO(row)" title="Complete" />
                  <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewWO(row)" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>

        <!-- Open Work Orders Tab -->
        <div v-if="item.key === 'open'" class="space-y-4 pt-4">
          <!-- Filters -->
          <UCard :ui="{ body: { padding: 'p-4' } }">
            <div class="flex flex-wrap gap-4">
              <UFormGroup label="Work Center" class="w-48">
                <USelect v-model="filters.work_center" :options="workCenterOptions" placeholder="All" @change="applyFilters" />
              </UFormGroup>
              <UFormGroup label="Status" class="w-40">
                <USelect v-model="filters.status" :options="statusOptions" placeholder="All" @change="applyFilters" />
              </UFormGroup>
              <UFormGroup label="Search" class="flex-1">
                <UInput v-model="filters.search" placeholder="Search by WO# or operation..." icon="i-heroicons-magnifying-glass" @input="applyFilters" />
              </UFormGroup>
            </div>
          </UCard>

          <UCard>
            <UTable :columns="openColumns" :rows="filteredOrders" :loading="loading">
              <template #work_order_no-data="{ row }">
                <span class="font-mono text-blue-600">{{ row.work_order_no }}</span>
              </template>
              <template #operation_name-data="{ row }">
                <div>
                  <p class="font-medium">{{ row.operation_name }}</p>
                  <p class="text-xs text-gray-400">Seq: {{ row.sequence }}</p>
                </div>
              </template>
              <template #work_center-data="{ row }">
                <span>{{ row.work_center?.name || '-' }}</span>
              </template>
              <template #status-data="{ row }">
                <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
              </template>
              <template #planned_start-data="{ row }">
                {{ row.planned_start ? formatDate(row.planned_start) : '-' }}
              </template>
              <template #actions-data="{ row }">
                <UDropdown :items="getRowActions(row)">
                  <UButton icon="i-heroicons-ellipsis-vertical" size="xs" color="gray" variant="ghost" />
                </UDropdown>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>
    </UTabs>

    <!-- Create/Edit Modal -->
    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Work Order' : 'New Work Order'" :loading="submitting" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Production Order" required>
          <USelect v-model="form.production_order_id" :options="productionOrderOptions" placeholder="Select PO..." />
        </UFormGroup>
        <UFormGroup label="Work Center" required>
          <USelect v-model="form.work_center_id" :options="workCenterOptions" placeholder="Select work center..." />
        </UFormGroup>
        <UFormGroup label="Operation Name" required>
          <UInput v-model="form.operation_name" placeholder="e.g., Cutting, Assembly, Finishing" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Sequence">
            <UInput v-model.number="form.sequence" type="number" />
          </UFormGroup>
          <UFormGroup label="Planned Qty">
            <UInput v-model.number="form.planned_qty" type="number" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Planned Start">
            <UInput v-model="form.planned_start" type="datetime-local" />
          </UFormGroup>
          <UFormGroup label="Planned End">
            <UInput v-model="form.planned_end" type="datetime-local" />
          </UFormGroup>
        </div>
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="2" />
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
const editMode = ref(false)
const activeTab = ref(0)

const workOrders = ref<any[]>([])
const workCenters = ref<any[]>([])
const productionOrders = ref<any[]>([])

const filters = reactive({
  work_center: '',
  status: '',
  search: ''
})

const form = reactive({
  id: '',
  production_order_id: '',
  work_center_id: '',
  operation_name: '',
  sequence: 10,
  planned_qty: 0,
  planned_start: '',
  planned_end: '',
  notes: ''
})

const tabs = [
  { key: 'dashboard', label: 'Dashboard', icon: 'i-heroicons-squares-2x2' },
  { key: 'open', label: 'Open Work Orders', icon: 'i-heroicons-queue-list' }
]

const columns = [
  { key: 'work_order_no', label: 'WO #', sortable: true },
  { key: 'operation_name', label: 'Operation' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'actions', label: '' }
]

const openColumns = [
  { key: 'work_order_no', label: 'WO #', sortable: true },
  { key: 'operation_name', label: 'Operation' },
  { key: 'work_center', label: 'Work Center' },
  { key: 'status', label: 'Status' },
  { key: 'planned_start', label: 'Planned Start' },
  { key: 'actions', label: '' }
]

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'Pending' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Completed', value: 'Completed' },
  { label: 'On Hold', value: 'On Hold' }
]

const workCenterOptions = computed(() => [
  { label: 'All', value: '' },
  ...workCenters.value.map(wc => ({ label: wc.name, value: wc.id }))
])

const productionOrderOptions = computed(() => 
  productionOrders.value.map(po => ({ label: po.order_no, value: po.id }))
)

const statusCounts = computed(() => {
  const counts = { pending: 0, in_progress: 0, completed: 0, on_hold: 0 }
  workOrders.value.forEach(wo => {
    if (wo.status === 'Pending') counts.pending++
    else if (wo.status === 'In Progress') counts.in_progress++
    else if (wo.status === 'Completed') counts.completed++
    else if (wo.status === 'On Hold') counts.on_hold++
  })
  return counts
})

const workCenterStats = computed(() => 
  workCenters.value.slice(0, 4).map(wc => ({
    ...wc,
    active_count: workOrders.value.filter(wo => wo.work_center_id === wc.id && wo.status === 'In Progress').length,
    utilization: Math.round(Math.random() * 80 + 20) // Placeholder for real IoT data
  }))
)

const todaysOrders = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return workOrders.value.filter(wo => 
    wo.status !== 'Completed' || wo.actual_end?.startsWith(today)
  ).slice(0, 10).map(wo => ({
    ...wo,
    progress: wo.status === 'Completed' ? 100 : wo.status === 'In Progress' ? Math.round((wo.completed_qty / (wo.planned_qty || 1)) * 100) : 0
  }))
})

const filteredOrders = computed(() => {
  return workOrders.value.filter(wo => {
    if (filters.work_center && wo.work_center_id !== filters.work_center) return false
    if (filters.status && wo.status !== filters.status) return false
    if (filters.search) {
      const q = filters.search.toLowerCase()
      if (!wo.work_order_no?.toLowerCase().includes(q) && !wo.operation_name?.toLowerCase().includes(q)) return false
    }
    return true
  })
})

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Pending': 'blue',
    'In Progress': 'yellow',
    'Completed': 'green',
    'On Hold': 'red',
    'Cancelled': 'gray'
  }
  return colors[status] || 'gray'
}

const formatDate = (d: string) => d ? new Date(d).toLocaleString('id-ID', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'

const applyFilters = () => { /* Computed handles it */ }

const getRowActions = (row: any) => [[
  { label: 'View Details', icon: 'i-heroicons-eye', click: () => viewWO(row) },
  { label: 'Edit', icon: 'i-heroicons-pencil', click: () => openEdit(row) },
  ...(row.status === 'Pending' ? [{ label: 'Start', icon: 'i-heroicons-play', click: () => startWO(row) }] : []),
  ...(row.status === 'In Progress' ? [
    { label: 'Complete', icon: 'i-heroicons-check', click: () => completeWO(row) },
    { label: 'Put on Hold', icon: 'i-heroicons-pause', click: () => pauseWO(row) }
  ] : [])
]]

const fetchData = async () => {
  loading.value = true
  try {
    const [woRes, wcRes, poRes] = await Promise.all([
      $api.get('/manufacturing/work-orders').catch(() => ({ data: { data: [] } })),
      $api.get('/manufacturing/work-centers').catch(() => ({ data: { data: [] } })),
      $api.get('/manufacturing/production-orders').catch(() => ({ data: { data: [] } }))
    ])
    workOrders.value = woRes.data?.data || woRes.data || []
    workCenters.value = wcRes.data?.data || wcRes.data || []
    productionOrders.value = poRes.data?.data || poRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editMode.value = false
  Object.assign(form, { id: '', production_order_id: '', work_center_id: '', operation_name: '', sequence: 10, planned_qty: 0, planned_start: '', planned_end: '', notes: '' })
  isOpen.value = true
}

const openEdit = (row: any) => {
  editMode.value = true
  Object.assign(form, row)
  isOpen.value = true
}

const viewWO = (row: any) => {
  toast.add({ title: 'Work Order Details', description: `WO: ${row.work_order_no || row.id}`, color: 'blue' })
}

const save = async () => {
  submitting.value = true
  try {
    if (editMode.value) {
      await $api.put(`/manufacturing/work-orders/${form.id}`, form)
      toast.add({ title: 'Updated', description: 'Work order updated', color: 'green' })
    } else {
      await $api.post('/manufacturing/work-orders', form)
      toast.add({ title: 'Created', description: 'Work order created', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const startWO = async (row: any) => {
  try {
    await $api.put(`/manufacturing/work-orders/${row.id}/status`, { status: 'In Progress' })
    toast.add({ title: 'Started', description: 'Work order started', color: 'green' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to start', color: 'red' })
  }
}

const pauseWO = async (row: any) => {
  try {
    await $api.put(`/manufacturing/work-orders/${row.id}/status`, { status: 'On Hold' })
    toast.add({ title: 'Paused', description: 'Work order put on hold', color: 'yellow' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to pause', color: 'red' })
  }
}

const completeWO = async (row: any) => {
  try {
    await $api.put(`/manufacturing/work-orders/${row.id}/status`, { status: 'Completed' })
    toast.add({ title: 'Completed', description: 'Work order completed', color: 'green' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to complete', color: 'red' })
  }
}

onMounted(() => { fetchData() })
</script>
