<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Work Orders</h2>
        <p class="text-gray-500">Manage maintenance work orders</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Work Order</UButton>
      </div>
    </div>

    <!-- Kanban View -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div v-for="col in kanbanColumns" :key="col.status" class="bg-gray-50 rounded-lg p-3">
        <div class="flex items-center gap-2 mb-3">
          <div :class="`w-3 h-3 rounded-full bg-${col.color}-500`"></div>
          <h3 class="font-semibold">{{ col.label }}</h3>
          <UBadge :color="col.color" variant="subtle" size="xs">{{ getByStatus(col.status).length }}</UBadge>
        </div>
        <div class="space-y-2 min-h-[200px]">
          <div v-for="wo in getByStatus(col.status)" :key="wo.id" class="bg-white border rounded-lg p-3 shadow-sm cursor-pointer hover:shadow-md transition-shadow" @click="openDetail(wo)">
            <div class="flex justify-between items-start mb-2">
              <span class="text-xs font-mono text-gray-400">{{ wo.code }}</span>
              <UBadge :color="getPriorityColor(wo.priority)" variant="outline" size="xs">{{ wo.priority }}</UBadge>
            </div>
            <p class="font-medium text-sm mb-1">{{ wo.title }}</p>
            <p class="text-xs text-gray-500">{{ wo.asset_name || 'No asset' }}</p>
            <div class="flex items-center justify-between mt-2 text-xs text-gray-400">
              <span v-if="wo.assigned_name">👤 {{ wo.assigned_name }}</span>
              <span v-else class="text-orange-500">Unassigned</span>
              <span v-if="wo.scheduled_date">📅 {{ formatDate(wo.scheduled_date) }}</span>
            </div>
            <div v-if="wo.task_count > 0" class="mt-2">
              <div class="w-full bg-gray-200 rounded-full h-1.5">
                <div class="bg-blue-600 h-1.5 rounded-full" :style="{ width: `${(wo.completed_tasks / wo.task_count) * 100}%` }"></div>
              </div>
              <p class="text-xs text-gray-400 mt-1">{{ wo.completed_tasks }}/{{ wo.task_count }} tasks</p>
            </div>
          </div>
          <div v-if="getByStatus(col.status).length === 0" class="text-center py-8 text-sm text-gray-400">
            No items
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingWO ? 'Edit Work Order' : 'New Work Order'" :loading="saving" @submit="saveWorkOrder">
      <UFormGroup label="Asset" required hint="Select asset for maintenance">
        <USelect v-model="form.asset_id" :options="assetOptions" option-attribute="label" value-attribute="value" placeholder="Select asset..." />
      </UFormGroup>
      <UFormGroup label="Title" required hint="Brief description">
        <UInput v-model="form.title" placeholder="Fix motor bearings" />
      </UFormGroup>
      <UFormGroup label="Description" hint="Detailed work description">
        <UTextarea v-model="form.description" :rows="3" />
      </UFormGroup>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Priority" hint="Urgency level">
          <USelect v-model="form.priority" :options="priorityOptions" />
        </UFormGroup>
        <UFormGroup label="Status">
          <USelect v-model="form.status" :options="statusOptions" />
        </UFormGroup>
      </div>
      <UFormGroup label="Scheduled Date" hint="When work is planned">
        <UInput v-model="form.scheduled_date" type="datetime-local" />
      </UFormGroup>
      <UFormGroup label="Assign To" hint="Technician responsible">
        <USelect v-model="form.assigned_to" :options="userOptions" option-attribute="label" value-attribute="value" placeholder="Select user..." />
      </UFormGroup>
      <UFormGroup label="Notes" hint="Additional notes">
        <UTextarea v-model="form.notes" :rows="2" />
      </UFormGroup>
    </FormSlideover>

    <!-- Detail Slideover -->
    <USlideover v-model="isDetailOpen" :ui="{ width: 'max-w-lg' }">
      <div v-if="selectedWO" class="p-6 space-y-4">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm text-gray-400 font-mono">{{ selectedWO.code }}</p>
            <h3 class="text-lg font-bold">{{ selectedWO.title }}</h3>
          </div>
          <UButton icon="i-heroicons-x-mark" variant="ghost" color="gray" @click="isDetailOpen = false" />
        </div>
        
        <div class="flex gap-2">
          <UBadge :color="getStatusColor(selectedWO.status)" variant="subtle">{{ selectedWO.status }}</UBadge>
          <UBadge :color="getPriorityColor(selectedWO.priority)" variant="outline">{{ selectedWO.priority }}</UBadge>
        </div>

        <p class="text-sm text-gray-600">{{ selectedWO.description || 'No description' }}</p>

        <div class="grid grid-cols-2 gap-4 text-sm">
          <div><span class="text-gray-500">Asset:</span> {{ selectedWO.asset_name }}</div>
          <div><span class="text-gray-500">Assigned:</span> {{ selectedWO.assigned_name || 'Unassigned' }}</div>
          <div><span class="text-gray-500">Scheduled:</span> {{ formatDateTime(selectedWO.scheduled_date) }}</div>
          <div><span class="text-gray-500">Total Cost:</span> {{ formatCurrency(selectedWO.total_cost) }}</div>
        </div>

        <UDivider />

        <!-- Status Actions -->
        <div class="flex gap-2 flex-wrap">
          <UButton v-if="selectedWO.status === 'DRAFT'" size="sm" color="blue" @click="updateStatus('SCHEDULED')">Schedule</UButton>
          <UButton v-if="selectedWO.status === 'SCHEDULED'" size="sm" color="yellow" @click="updateStatus('IN_PROGRESS')">Start Work</UButton>
          <UButton v-if="selectedWO.status === 'IN_PROGRESS'" size="sm" color="green" @click="updateStatus('COMPLETED')">Complete</UButton>
          <UButton size="sm" variant="ghost" @click="openEdit(selectedWO)">Edit</UButton>
          <UButton size="sm" variant="ghost" color="red" @click="deleteWO(selectedWO)">Delete</UButton>
        </div>

        <UDivider />

        <!-- Tasks -->
        <div>
          <h4 class="font-semibold text-sm mb-2">Tasks</h4>
          <div class="space-y-2">
            <div v-for="task in woTasks" :key="task.id" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <UCheckbox :model-value="task.is_completed" @update:model-value="toggleTask(task)" />
              <span :class="task.is_completed ? 'line-through text-gray-400' : ''">{{ task.description }}</span>
            </div>
          </div>
          <div class="flex gap-2 mt-2">
            <UInput v-model="newTask" placeholder="Add task..." size="sm" class="flex-1" @keyup.enter="addTask" />
            <UButton size="sm" @click="addTask">Add</UButton>
          </div>
        </div>

        <UDivider />

        <!-- Costs -->
        <div>
          <h4 class="font-semibold text-sm mb-2">Costs</h4>
          <div class="space-y-2">
            <div v-for="cost in woCosts" :key="cost.id" class="flex justify-between p-2 bg-gray-50 rounded text-sm">
              <span>{{ cost.description }} <UBadge size="xs" variant="subtle">{{ cost.category }}</UBadge></span>
              <span class="font-medium">{{ formatCurrency(cost.amount) }}</span>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 mt-2">
            <UInput v-model="newCost.description" placeholder="Description" size="sm" />
            <UInput v-model.number="newCost.amount" type="number" placeholder="Amount" size="sm" />
            <UButton size="sm" @click="addCost">Add Cost</UButton>
          </div>
        </div>
      </div>
    </USlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const isSlideoverOpen = ref(false)
const isDetailOpen = ref(false)
const editingWO = ref<any>(null)
const selectedWO = ref<any>(null)

const workOrders = ref<any[]>([])
const assets = ref<any[]>([])
const users = ref<any[]>([])
const woTasks = ref<any[]>([])
const woCosts = ref<any[]>([])
const newTask = ref('')
const newCost = reactive({ description: '', amount: 0, category: 'OTHER' })

const kanbanColumns = [
  { status: 'DRAFT', label: 'Draft', color: 'gray' },
  { status: 'SCHEDULED', label: 'Scheduled', color: 'blue' },
  { status: 'IN_PROGRESS', label: 'In Progress', color: 'yellow' },
  { status: 'COMPLETED', label: 'Completed', color: 'green' }
]

const priorityOptions = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
const statusOptions = ['DRAFT', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']

const form = reactive({
  asset_id: '', title: '', description: '', priority: 'MEDIUM', status: 'DRAFT',
  scheduled_date: '', assigned_to: '', notes: ''
})

const assetOptions = computed(() => assets.value.map(a => ({ label: `${a.code} - ${a.name}`, value: a.id })))
const userOptions = computed(() => [{ label: 'Unassigned', value: '' }, ...users.value.map(u => ({ label: u.username, value: u.id }))])

const getByStatus = (status: string) => workOrders.value.filter(wo => wo.status === status)

const fetchData = async () => {
  loading.value = true
  try {
    const [woRes, assetsRes, usersRes] = await Promise.all([
      $api.get('/maintenance/work-orders'),
      $api.get('/maintenance/assets'),
      $api.get('/users')
    ])
    workOrders.value = woRes.data
    assets.value = assetsRes.data
    users.value = usersRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingWO.value = null
  Object.assign(form, { asset_id: '', title: '', description: '', priority: 'MEDIUM', status: 'DRAFT', scheduled_date: '', assigned_to: '', notes: '' })
  isSlideoverOpen.value = true
}

const openEdit = (wo: any) => {
  editingWO.value = wo
  Object.assign(form, {
    asset_id: wo.asset_id, title: wo.title, description: wo.description || '', priority: wo.priority, status: wo.status,
    scheduled_date: wo.scheduled_date?.slice(0, 16) || '', assigned_to: wo.assigned_to || '', notes: wo.notes || ''
  })
  isDetailOpen.value = false
  isSlideoverOpen.value = true
}

const openDetail = async (wo: any) => {
  selectedWO.value = wo
  isDetailOpen.value = true
  const [tasksRes, costsRes] = await Promise.all([
    $api.get(`/maintenance/work-orders/${wo.id}/tasks`),
    $api.get(`/maintenance/work-orders/${wo.id}/costs`)
  ])
  woTasks.value = tasksRes.data
  woCosts.value = costsRes.data
}

const saveWorkOrder = async () => {
  saving.value = true
  try {
    const payload = { ...form, scheduled_date: form.scheduled_date ? new Date(form.scheduled_date).toISOString() : null }
    if (!payload.assigned_to) delete payload.assigned_to
    
    if (editingWO.value) {
      await $api.put(`/maintenance/work-orders/${editingWO.value.id}`, payload)
      toast.add({ title: 'Work order updated!' })
    } else {
      await $api.post('/maintenance/work-orders', payload)
      toast.add({ title: 'Work order created!' })
    }
    isSlideoverOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const updateStatus = async (newStatus: string) => {
  if (!selectedWO.value) return
  await $api.put(`/maintenance/work-orders/${selectedWO.value.id}`, { status: newStatus })
  toast.add({ title: `Status changed to ${newStatus}` })
  isDetailOpen.value = false
  fetchData()
}

const deleteWO = async (wo: any) => {
  if (!confirm(`Delete work order "${wo.code}"?`)) return
  await $api.delete(`/maintenance/work-orders/${wo.id}`)
  toast.add({ title: 'Work order deleted!' })
  isDetailOpen.value = false
  fetchData()
}

const addTask = async () => {
  if (!newTask.value.trim() || !selectedWO.value) return
  await $api.post(`/maintenance/work-orders/${selectedWO.value.id}/tasks`, { description: newTask.value })
  newTask.value = ''
  openDetail(selectedWO.value)
}

const toggleTask = async (task: any) => {
  if (!selectedWO.value) return
  await $api.put(`/maintenance/work-orders/${selectedWO.value.id}/tasks/${task.id}/complete`)
  openDetail(selectedWO.value)
}

const addCost = async () => {
  if (!newCost.description || !selectedWO.value) return
  await $api.post(`/maintenance/work-orders/${selectedWO.value.id}/costs`, newCost)
  newCost.description = ''; newCost.amount = 0
  openDetail(selectedWO.value)
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { DRAFT: 'gray', SCHEDULED: 'blue', IN_PROGRESS: 'yellow', COMPLETED: 'green', CANCELLED: 'red' }
  return colors[status] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = { LOW: 'gray', MEDIUM: 'blue', HIGH: 'orange', URGENT: 'red' }
  return colors[priority] || 'gray'
}

const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }) : '-'
const formatDateTime = (date: string) => date ? new Date(date).toLocaleString('id-ID', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'
const formatCurrency = (v: number) => v ? `Rp ${v.toLocaleString()}` : 'Rp 0'

onMounted(() => {
  fetchData()
})
</script>
