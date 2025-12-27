<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Activities</h2>
        <p class="text-gray-500">Manage follow-ups, meetings, calls, and tasks</p>
      </div>
      <div class="flex gap-2">
        <USelect v-model="filterType" :options="typeFilterOptions" size="sm" placeholder="All Types" class="w-32" />
        <USelect v-model="filterStatus" :options="statusFilterOptions" size="sm" placeholder="All Status" class="w-32" />
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Activity</UButton>
      </div>
    </div>

    <!-- Today's Activities -->
    <UCard v-if="todayActivities.length > 0">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-calendar" class="text-blue-500" />
          <span class="font-medium">Today's Activities ({{ todayActivities.length }})</span>
        </div>
      </template>
      <div class="space-y-2">
        <div v-for="act in todayActivities" :key="act.id" class="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
          <div class="flex items-center gap-3">
            <UIcon :name="getTypeIcon(act.activity_type)" class="text-blue-600" />
            <div>
              <p class="font-medium">{{ act.title }}</p>
              <p class="text-xs text-gray-500">
                {{ act.due_time || '' }} • {{ act.lead_name || act.opportunity_name || act.customer_name || 'No link' }}
              </p>
            </div>
          </div>
          <div class="flex gap-1">
            <UButton v-if="act.status !== 'Completed'" icon="i-heroicons-check" size="xs" color="green" @click="completeActivity(act)" />
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(act)" />
          </div>
        </div>
      </div>
    </UCard>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="filteredActivities" 
        :loading="loading"
        searchable
        :search-keys="['title', 'lead_name', 'opportunity_name']"
        empty-message="No activities yet. Create a task or schedule a follow-up."
      >
        <template #title-data="{ row }">
          <div class="flex items-center gap-2">
            <UIcon :name="getTypeIcon(row.activity_type)" class="text-gray-400" />
            <div>
              <p class="font-medium">{{ row.title }}</p>
              <p class="text-xs text-gray-400">{{ row.description?.slice(0, 40) || '' }}</p>
            </div>
          </div>
        </template>
        <template #activity_type-data="{ row }">
          <UBadge :color="getTypeColor(row.activity_type)" variant="subtle" size="xs">{{ row.activity_type }}</UBadge>
        </template>
        <template #due_date-data="{ row }">
          <div :class="isOverdue(row) ? 'text-red-500' : ''">
            <p>{{ formatDate(row.due_date) }}</p>
            <p v-if="row.due_time" class="text-xs">{{ row.due_time }}</p>
          </div>
        </template>
        <template #link-data="{ row }">
          <span class="text-sm text-gray-500">
            {{ row.lead_name || row.opportunity_name || row.customer_name || '-' }}
          </span>
        </template>
        <template #priority-data="{ row }">
          <UBadge :color="getPriorityColor(row.priority)" variant="outline" size="xs">{{ row.priority }}</UBadge>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton v-if="row.status !== 'Completed'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="completeActivity(row)" title="Complete" />
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEditing ? 'Edit Activity' : 'Add Activity'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create a follow-up, meeting, call, or other task.</p>
        
        <UFormGroup label="Title" required hint="Activity name" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.title" placeholder="e.g., Follow-up call with ABC Corp" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Activity details" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" placeholder="Additional notes..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Type" required hint="Activity type" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.activity_type" :options="typeOptions" />
          </UFormGroup>
          <UFormGroup label="Priority" required hint="Urgency level" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.priority" :options="priorityOptions" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup :label="form.activity_type === 'Task' ? 'Due Date' : 'Schedule Date'" :hint="form.activity_type === 'Task' ? 'Task due date' : 'Scheduled date'" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.due_date" type="date" />
          </UFormGroup>
          <UFormGroup label="Time" hint="Time (optional)" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.due_time" type="time" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Duration (minutes)" hint="Estimated duration" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.duration_minutes" type="number" placeholder="e.g., 30" />
        </UFormGroup>
        
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3">Link To</h4>
          <div class="space-y-3">
            <UFormGroup label="Lead" hint="Link to a lead" :ui="{ hint: 'text-xs text-gray-400' }">
              <USelect v-model="form.lead_id" :options="leadOptions" placeholder="Select lead..." searchable />
            </UFormGroup>
            <UFormGroup label="Opportunity" hint="Link to an opportunity" :ui="{ hint: 'text-xs text-gray-400' }">
              <USelect v-model="form.opportunity_id" :options="opportunityOptions" placeholder="Select opportunity..." searchable />
            </UFormGroup>
            <UFormGroup label="Customer" hint="Link to a customer" :ui="{ hint: 'text-xs text-gray-400' }">
              <USelect v-model="form.customer_id" :options="customerOptions" placeholder="Select customer..." searchable />
            </UFormGroup>
          </div>
        </div>
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
const isEditing = ref(false)
const editingId = ref<string | null>(null)

const filterType = ref('')
const filterStatus = ref('')

const activities = ref<any[]>([])
const leads = ref<any[]>([])
const opportunities = ref<any[]>([])
const customers = ref<any[]>([])

const columns = [
  { key: 'title', label: 'Activity', sortable: true },
  { key: 'activity_type', label: 'Type' },
  { key: 'due_date', label: 'Due', sortable: true },
  { key: 'link', label: 'Linked To' },
  { key: 'priority', label: 'Priority' },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'actions', label: '' }
]

const typeOptions = [
  { label: 'Call', value: 'Call' },
  { label: 'Email', value: 'Email' },
  { label: 'Meeting', value: 'Meeting' },
  { label: 'Task', value: 'Task' },
  { label: 'Follow Up', value: 'Follow Up' },
  { label: 'Demo', value: 'Demo' },
  { label: 'Reminder', value: 'Reminder' }
]

const priorityOptions = [
  { label: 'Low', value: 'Low' },
  { label: 'Normal', value: 'Normal' },
  { label: 'High', value: 'High' },
  { label: 'Urgent', value: 'Urgent' }
]

const typeFilterOptions = [{ label: 'All Types', value: '' }, ...typeOptions]
const statusFilterOptions = [
  { label: 'All Status', value: '' },
  { label: 'Planned', value: 'Planned' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Completed', value: 'Completed' },
  { label: 'Cancelled', value: 'Cancelled' }
]

const form = reactive({
  title: '',
  description: '',
  activity_type: 'Task',
  priority: 'Normal',
  due_date: '',
  due_time: '',
  duration_minutes: null as number | null,
  lead_id: '',
  opportunity_id: '',
  customer_id: ''
})

const leadOptions = computed(() => leads.value.map(l => ({ label: l.name, value: l.id })))
const opportunityOptions = computed(() => opportunities.value.map(o => ({ label: o.name, value: o.id })))
const customerOptions = computed(() => customers.value.map(c => ({ label: c.name, value: c.id })))

const filteredActivities = computed(() => {
  let result = activities.value
  if (filterType.value) result = result.filter(a => a.activity_type === filterType.value)
  if (filterStatus.value) result = result.filter(a => a.status === filterStatus.value)
  return result
})

const todayActivities = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return activities.value.filter(a => a.due_date?.startsWith(today) && a.status !== 'Completed')
})

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    'Call': 'i-heroicons-phone',
    'Email': 'i-heroicons-envelope',
    'Meeting': 'i-heroicons-users',
    'Task': 'i-heroicons-clipboard-document-check',
    'Follow Up': 'i-heroicons-arrow-path',
    'Demo': 'i-heroicons-presentation-chart-bar',
    'Reminder': 'i-heroicons-bell'
  }
  return icons[type] || 'i-heroicons-clipboard'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = { 'Call': 'blue', 'Email': 'purple', 'Meeting': 'green', 'Task': 'gray', 'Follow Up': 'yellow', 'Demo': 'pink', 'Reminder': 'orange' }
  return colors[type] || 'gray'
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { 'Planned': 'blue', 'In Progress': 'yellow', 'Completed': 'green', 'Cancelled': 'red' }
  return colors[status] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = { 'Low': 'gray', 'Normal': 'blue', 'High': 'orange', 'Urgent': 'red' }
  return colors[priority] || 'gray'
}

const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short' }) : '-'
const isOverdue = (row: any) => row.due_date && row.status !== 'Completed' && new Date(row.due_date) < new Date()

const fetchData = async () => {
  loading.value = true
  try {
    const [actRes, leadRes, oppRes, custRes] = await Promise.all([
      $api.get('/crm/activities').catch(() => ({ data: [] })),
      $api.get('/crm/leads').catch(() => ({ data: [] })),
      $api.get('/crm/opportunities').catch(() => ({ data: [] })),
      $api.get('/ar/customers').catch(() => ({ data: [] }))
    ])
    activities.value = actRes.data || []
    leads.value = leadRes.data || []
    opportunities.value = oppRes.data || []
    customers.value = custRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, { title: '', description: '', activity_type: 'Task', priority: 'Normal', due_date: new Date().toISOString().split('T')[0], due_time: '', duration_minutes: null, lead_id: '', opportunity_id: '', customer_id: '' })
  isOpen.value = true
}

const openEdit = (row: any) => {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    ...row,
    due_date: row.due_date ? row.due_date.split('T')[0] : ''
  })
  isOpen.value = true
}

const save = async () => {
  if (!form.title) {
    toast.add({ title: 'Error', description: 'Title is required', color: 'red' })
    return
  }
  submitting.value = true
  try {
    const payload = { ...form, due_date: form.due_date ? new Date(form.due_date).toISOString() : null }
    if (isEditing.value && editingId.value) {
      await $api.put(`/crm/activities/${editingId.value}`, payload)
      toast.add({ title: 'Updated', description: 'Activity updated successfully', color: 'green' })
    } else {
      await $api.post('/crm/activities', payload)
      toast.add({ title: 'Created', description: 'Activity created successfully', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const completeActivity = async (row: any) => {
  try {
    await $api.put(`/crm/activities/${row.id}/complete`)
    toast.add({ title: 'Completed', description: 'Activity marked as complete', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const confirmDelete = async (row: any) => {
  if (!confirm(`Delete activity "${row.title}"?`)) return
  try {
    await $api.delete(`/crm/activities/${row.id}`)
    toast.add({ title: 'Deleted', description: 'Activity deleted successfully', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

onMounted(() => { fetchData() })
</script>
