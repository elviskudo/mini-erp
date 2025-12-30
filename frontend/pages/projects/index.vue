<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Projects</h2>
        <p class="text-gray-500">Manage and track all your projects</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Project</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ projects.length }}</p>
          <p class="text-sm text-gray-500">Total Projects</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ planningCount }}</p>
          <p class="text-sm text-gray-500">Planning</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ inProgressCount }}</p>
          <p class="text-sm text-gray-500">In Progress</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ completedCount }}</p>
          <p class="text-sm text-gray-500">Completed</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-purple-600">{{ formatCurrency(totalBudget) }}</p>
          <p class="text-sm text-gray-500">Total Budget</p>
        </div>
      </UCard>
    </div>

    <!-- DataTable -->
    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="projects" 
        :loading="loading"
        searchable
        :search-keys="['name', 'code', 'description']"
        empty-message="No projects yet. Create your first project to get started."
      >
        <template #name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.name }}</p>
            <p class="text-xs text-gray-400 font-mono">{{ row.code }}</p>
          </div>
        </template>
        <template #type-data="{ row }">
          <UBadge color="gray" variant="subtle" size="xs">{{ formatType(row.type) }}</UBadge>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ formatStatus(row.status) }}</UBadge>
        </template>
        <template #priority-data="{ row }">
          <UBadge :color="getPriorityColor(row.priority)" variant="outline" size="xs">{{ row.priority }}</UBadge>
        </template>
        <template #budget-data="{ row }">
          <span class="font-medium text-green-600">{{ formatCurrency(row.budget) }}</span>
        </template>
        <template #progress-data="{ row }">
          <div class="flex items-center gap-2">
            <div class="w-16 bg-gray-200 rounded-full h-2">
              <div class="bg-blue-600 h-2 rounded-full" :style="{ width: `${calculateProgress(row)}%` }"></div>
            </div>
            <span class="text-xs">{{ calculateProgress(row) }}%</span>
          </div>
        </template>
        <template #timeline-data="{ row }">
          <div class="text-xs text-gray-500">
            {{ formatDate(row.start_date) }} - {{ formatDate(row.end_date) }}
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewProject(row)" />
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Modal -->
    <FormSlideover
      v-model="isSlideoverOpen"
      :title="editingProject ? 'Edit Project' : 'New Project'"
      :loading="saving"
      @submit="onSubmit"
      @close="isSlideoverOpen = false"
    >
      <UFormGroup label="Project Name" name="name" required hint="Descriptive project name" :ui="{ hint: 'text-xs text-gray-400' }">
        <UInput v-model="form.name" placeholder="e.g. New Product Development" />
      </UFormGroup>
      
      <UFormGroup label="Description" name="description" hint="Brief overview of the project" :ui="{ hint: 'text-xs text-gray-400' }">
        <UTextarea v-model="form.description" placeholder="Project description..." :rows="3" />
      </UFormGroup>
      
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Project Code" name="code" required hint="Unique identifier" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.code" placeholder="e.g. PRJ-2024-001" />
        </UFormGroup>
        <UFormGroup label="Type" name="type" required hint="Project category" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.type" :options="typeOptions" />
        </UFormGroup>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Status" name="status" hint="Current phase" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.status" :options="statusOptions" />
        </UFormGroup>
        <UFormGroup label="Priority" name="priority" hint="Importance level" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.priority" :options="priorityOptions" />
        </UFormGroup>
      </div>
      
      <UFormGroup label="Budget" name="budget" hint="Total project budget" :ui="{ hint: 'text-xs text-gray-400' }">
        <UInput v-model.number="form.budget" type="number" placeholder="0" />
      </UFormGroup>
      
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Start Date" name="start_date" hint="Project kick-off" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.start_date" type="date" />
        </UFormGroup>
        <UFormGroup label="End Date" name="end_date" hint="Target completion" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.end_date" type="date" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const router = useRouter()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(false)
const saving = ref(false)
const isSlideoverOpen = ref(false)
const projects = ref<any[]>([])
const editingProject = ref<any>(null)

const form = reactive({
  name: '',
  code: '',
  description: '',
  type: 'INTERNAL_IMPROVEMENT',
  status: 'DRAFT',
  priority: 'MEDIUM',
  budget: 0,
  start_date: '',
  end_date: ''
})

const columns = [
  { key: 'name', label: 'Project', sortable: true },
  { key: 'type', label: 'Type' },
  { key: 'status', label: 'Status' },
  { key: 'priority', label: 'Priority' },
  { key: 'budget', label: 'Budget', sortable: true },
  { key: 'progress', label: 'Progress' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'actions', label: '' }
]

const statusOptions = [
  { label: 'Draft', value: 'DRAFT' },
  { label: 'Planning', value: 'PLANNING' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'On Hold', value: 'ON_HOLD' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Cancelled', value: 'CANCELLED' }
]

const typeOptions = [
  { label: 'R&D', value: 'R_AND_D' },
  { label: 'Customer Order', value: 'CUSTOMER_ORDER' },
  { label: 'Internal', value: 'INTERNAL_IMPROVEMENT' },
  { label: 'Maintenance', value: 'MAINTENANCE' },
  { label: 'Consulting', value: 'CONSULTING' }
]

const priorityOptions = [
  { label: 'Low', value: 'LOW' },
  { label: 'Medium', value: 'MEDIUM' },
  { label: 'High', value: 'HIGH' },
  { label: 'Critical', value: 'CRITICAL' }
]

// Computed stats
const planningCount = computed(() => projects.value.filter(p => p.status === 'PLANNING' || p.status === 'DRAFT').length)
const inProgressCount = computed(() => projects.value.filter(p => p.status === 'IN_PROGRESS').length)
const completedCount = computed(() => projects.value.filter(p => p.status === 'COMPLETED').length)
const totalBudget = computed(() => projects.value.reduce((sum, p) => sum + (p.budget || 0), 0))

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/projects')
    projects.value = res.data
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Error', description: 'Failed to load projects', color: 'red' })
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingProject.value = null
  Object.assign(form, {
    name: '', code: '', description: '', type: 'INTERNAL_IMPROVEMENT',
    status: 'DRAFT', priority: 'MEDIUM', budget: 0, start_date: '', end_date: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (project: any) => {
  editingProject.value = project
  Object.assign(form, {
    name: project.name,
    code: project.code,
    description: project.description || '',
    type: project.type,
    status: project.status,
    priority: project.priority || 'MEDIUM',
    budget: project.budget || 0,
    start_date: project.start_date ? project.start_date.split('T')[0] : '',
    end_date: project.end_date ? project.end_date.split('T')[0] : ''
  })
  isSlideoverOpen.value = true
}

const onSubmit = async () => {
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.start_date) payload.start_date = new Date(payload.start_date).toISOString()
    if (payload.end_date) payload.end_date = new Date(payload.end_date).toISOString()
    
    if (editingProject.value) {
      await $api.put(`/projects/${editingProject.value.id}`, payload)
      toast.add({ title: 'Success', description: 'Project updated.' })
    } else {
      await $api.post('/projects', payload)
      toast.add({ title: 'Success', description: 'Project created.' })
    }
    isSlideoverOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save project', color: 'red' })
  } finally {
    saving.value = false
  }
}

const viewProject = (project: any) => {
  router.push(`/projects/${project.id}`)
}

const confirmDelete = async (project: any) => {
  if (!confirm(`Are you sure you want to delete "${project.name}"?`)) return
  
  try {
    await $api.delete(`/projects/${project.id}`)
    toast.add({ title: 'Success', description: 'Project deleted.' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to delete project', color: 'red' })
  }
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    DRAFT: 'gray', PLANNING: 'blue', IN_PROGRESS: 'orange',
    ON_HOLD: 'yellow', COMPLETED: 'green', CANCELLED: 'red'
  }
  return colors[status] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    LOW: 'gray', MEDIUM: 'blue', HIGH: 'orange', CRITICAL: 'red'
  }
  return colors[priority] || 'gray'
}

const formatStatus = (status: string) => {
  return status.split('_').map(s => s.charAt(0) + s.slice(1).toLowerCase()).join(' ')
}

const formatType = (type: string) => {
  const labels: Record<string, string> = {
    R_AND_D: 'R&D', CUSTOMER_ORDER: 'Customer', INTERNAL_IMPROVEMENT: 'Internal',
    MAINTENANCE: 'Maintenance', CONSULTING: 'Consulting'
  }
  return labels[type] || type
}

const formatCurrency = (value: number) => {
  if (!value) return 'Rp 0'
  if (value >= 1000000000) return `Rp ${(value / 1000000000).toFixed(1)}B`
  if (value >= 1000000) return `Rp ${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `Rp ${(value / 1000).toFixed(0)}k`
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)
}

const formatDate = (date: string) => {
  if (!date) return 'TBD'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}

const calculateProgress = (project: any) => {
  if (!project.task_count || project.task_count === 0) return 0
  return Math.round((project.completed_tasks || 0) / project.task_count * 100)
}

onMounted(() => {
  fetchData()
})
</script>
