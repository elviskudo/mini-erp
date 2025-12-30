<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Maintenance Schedules</h2>
        <p class="text-gray-500">Preventive maintenance planning</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Schedule</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ schedules.length }}</p>
          <p class="text-sm text-gray-500">Total Schedules</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ schedules.filter(s => s.is_active).length }}</p>
          <p class="text-sm text-gray-500">Active</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ overdueCount }}</p>
          <p class="text-sm text-gray-500">Overdue</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ upcomingCount }}</p>
          <p class="text-sm text-gray-500">Due This Week</p>
        </div>
      </UCard>
    </div>

    <!-- Data Table -->
    <UCard>
      <DataTable :columns="columns" :rows="schedules" :loading="loading" searchable :search-keys="['title', 'asset_name', 'frequency']" empty-message="No schedules yet. Create a preventive maintenance schedule.">
        <template #title-data="{ row }">
          <div>
            <p class="font-medium">{{ row.title }}</p>
            <p class="text-xs text-gray-400">{{ row.asset_name }} ({{ row.asset_code }})</p>
          </div>
        </template>
        <template #frequency-data="{ row }">
          <UBadge color="blue" variant="subtle" size="xs">{{ row.frequency }}</UBadge>
        </template>
        <template #next_due-data="{ row }">
          <span :class="isOverdue(row.next_due) ? 'text-red-600 font-medium' : ''">{{ formatDate(row.next_due) }}</span>
          <span v-if="isOverdue(row.next_due)" class="ml-1 text-xs text-red-500">(Overdue)</span>
        </template>
        <template #last_performed-data="{ row }">
          {{ row.last_performed ? formatDate(row.last_performed) : 'Never' }}
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-clipboard-document-list" variant="ghost" color="green" title="Create Work Order" @click="createWOFromSchedule(row)" />
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteSchedule(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingSchedule ? 'Edit Schedule' : 'New Schedule'" :loading="saving" @submit="saveSchedule">
      <UFormGroup label="Asset" required hint="Select asset for maintenance">
        <USelect v-model="form.asset_id" :options="assetOptions" option-attribute="label" value-attribute="value" placeholder="Select asset..." />
      </UFormGroup>
      <UFormGroup label="Title" required hint="Schedule name">
        <UInput v-model="form.title" placeholder="Monthly lubrication check" />
      </UFormGroup>
      <UFormGroup label="Description" hint="Maintenance tasks">
        <UTextarea v-model="form.description" :rows="3" />
      </UFormGroup>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Frequency" hint="How often">
          <USelect v-model="form.frequency" :options="frequencyOptions" />
        </UFormGroup>
        <UFormGroup label="Interval (days)" hint="Days between">
          <UInput v-model.number="form.interval_days" type="number" />
        </UFormGroup>
      </div>
      <UFormGroup label="Next Due Date" hint="When next maintenance is due">
        <UInput v-model="form.next_due" type="date" />
      </UFormGroup>
      <UFormGroup label="Active">
        <UToggle v-model="form.is_active" />
      </UFormGroup>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const isSlideoverOpen = ref(false)
const editingSchedule = ref<any>(null)
const schedules = ref<any[]>([])
const assets = ref<any[]>([])

const columns = [
  { key: 'title', label: 'Schedule' },
  { key: 'frequency', label: 'Frequency' },
  { key: 'next_due', label: 'Next Due' },
  { key: 'last_performed', label: 'Last Performed' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const frequencyOptions = [
  { label: 'Daily', value: 'DAILY' },
  { label: 'Weekly', value: 'WEEKLY' },
  { label: 'Monthly', value: 'MONTHLY' },
  { label: 'Quarterly', value: 'QUARTERLY' },
  { label: 'Yearly', value: 'YEARLY' }
]

const form = reactive({
  asset_id: '', title: '', description: '', frequency: 'MONTHLY', interval_days: 30, next_due: '', is_active: true
})

const assetOptions = computed(() => assets.value.map(a => ({ label: `${a.code} - ${a.name}`, value: a.id })))

const overdueCount = computed(() => schedules.value.filter(s => s.is_active && isOverdue(s.next_due)).length)
const upcomingCount = computed(() => {
  const today = new Date()
  const weekLater = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
  return schedules.value.filter(s => {
    if (!s.next_due || !s.is_active) return false
    const due = new Date(s.next_due)
    return due >= today && due <= weekLater
  }).length
})

const isOverdue = (dateStr: string) => {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

const fetchData = async () => {
  loading.value = true
  try {
    const [schedulesRes, assetsRes] = await Promise.all([
      $api.get('/maintenance/schedules'),
      $api.get('/maintenance/assets')
    ])
    schedules.value = schedulesRes.data
    assets.value = assetsRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingSchedule.value = null
  Object.assign(form, { asset_id: '', title: '', description: '', frequency: 'MONTHLY', interval_days: 30, next_due: '', is_active: true })
  isSlideoverOpen.value = true
}

const openEdit = (schedule: any) => {
  editingSchedule.value = schedule
  Object.assign(form, {
    asset_id: schedule.asset_id, title: schedule.title, description: schedule.description || '',
    frequency: schedule.frequency, interval_days: schedule.interval_days,
    next_due: schedule.next_due?.split('T')[0] || '', is_active: schedule.is_active
  })
  isSlideoverOpen.value = true
}

const saveSchedule = async () => {
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.next_due) delete payload.next_due
    
    if (editingSchedule.value) {
      await $api.put(`/maintenance/schedules/${editingSchedule.value.id}`, payload)
      toast.add({ title: 'Schedule updated!' })
    } else {
      await $api.post('/maintenance/schedules', payload)
      toast.add({ title: 'Schedule created!' })
    }
    isSlideoverOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteSchedule = async (schedule: any) => {
  if (!confirm(`Delete schedule "${schedule.title}"?`)) return
  try {
    await $api.delete(`/maintenance/schedules/${schedule.id}`)
    toast.add({ title: 'Schedule deleted!' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const createWOFromSchedule = async (schedule: any) => {
  try {
    await $api.post('/maintenance/work-orders', {
      asset_id: schedule.asset_id,
      title: `[PM] ${schedule.title}`,
      description: schedule.description,
      priority: 'MEDIUM',
      status: 'SCHEDULED'
    })
    toast.add({ title: 'Work Order created from schedule!' })
    // Update last_performed
    await $api.put(`/maintenance/schedules/${schedule.id}`, {
      last_performed: new Date().toISOString().split('T')[0]
    })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error creating work order', color: 'red' })
  }
}

const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

onMounted(() => {
  fetchData()
})
</script>
