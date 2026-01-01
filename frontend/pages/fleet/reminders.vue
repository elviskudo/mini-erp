<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Reminders</h2>
        <p class="text-gray-500">Document expiry and service alert management</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchReminders">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Reminder</UButton>
      </div>
    </div>

    <!-- Alert Summary -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { background: overdueCount > 0 ? 'bg-red-50 dark:bg-red-900/20' : '' } }">
        <p class="text-sm text-gray-500">Overdue</p>
        <p class="text-2xl font-bold text-red-500">{{ overdueCount }}</p>
      </UCard>
      <UCard :ui="{ body: { background: dueSoonCount > 0 ? 'bg-yellow-50 dark:bg-yellow-900/20' : '' } }">
        <p class="text-sm text-gray-500">Due in 7 Days</p>
        <p class="text-2xl font-bold text-yellow-500">{{ dueSoonCount }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-gray-500">Upcoming</p>
        <p class="text-2xl font-bold text-blue-500">{{ upcomingCount }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-gray-500">Completed</p>
        <p class="text-2xl font-bold text-green-500">{{ completedCount }}</p>
      </UCard>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="reminders" :loading="loading" searchable :search-keys="['title', 'description']" empty-message="No reminders yet.">
        <template #vehicle_id-data="{ row }">
          <p class="font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #type-data="{ row }">
          <UBadge :color="getTypeColor(row.type)" variant="subtle" size="sm">{{ row.type }}</UBadge>
        </template>
        <template #title-data="{ row }">
          <div>
            <p class="font-medium">{{ row.title }}</p>
            <p class="text-xs text-gray-400 truncate max-w-48">{{ row.description }}</p>
          </div>
        </template>
        <template #due_date-data="{ row }">
          <div>
            <UBadge :color="getDueDateColor(row.due_date)" size="sm">{{ formatDate(row.due_date) }}</UBadge>
            <p class="text-xs text-gray-400 mt-1">{{ getDaysRemaining(row.due_date) }}</p>
          </div>
        </template>
        <template #is_completed-data="{ row }">
          <UToggle v-model="row.is_completed" @update:model-value="toggleComplete(row)" />
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteReminder(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingReminder ? 'Edit Reminder' : 'Add Reminder'" :loading="saving" @submit="saveReminder">
      <UFormGroup label="Vehicle" required hint="Select the vehicle for this reminder">
        <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." />
      </UFormGroup>

      <UFormGroup label="Type" required hint="Category of this reminder">
        <USelect v-model="form.type" :options="typeOptions" />
      </UFormGroup>

      <UFormGroup label="Title" required hint="Short title for the reminder">
        <UInput v-model="form.title" placeholder="e.g. STNK Renewal, Oil Change Due" />
      </UFormGroup>

      <UFormGroup label="Description" hint="Detailed description or notes">
        <UTextarea v-model="form.description" :rows="3" placeholder="Additional details about this reminder..." />
      </UFormGroup>

      <UFormGroup label="Due Date" required hint="When this task is due">
        <UInput v-model="form.due_date" type="date" />
      </UFormGroup>

      <UFormGroup label="Reminder Days Before" hint="Days before due date to start reminders">
        <UInput v-model.number="form.reminder_days" type="number" placeholder="7" />
      </UFormGroup>

      <UFormGroup label="Estimated Cost (Rp)" hint="Estimated cost if applicable">
        <UInput v-model.number="form.estimated_cost" type="number" placeholder="e.g. 500000" />
      </UFormGroup>

      <UFormGroup label="Reference Number" hint="Document or reference number">
        <UInput v-model="form.reference_number" placeholder="e.g. STNK number, Police number" />
      </UFormGroup>

      <UFormGroup label="Notes" hint="Additional notes">
        <UTextarea v-model="form.notes" :rows="2" />
      </UFormGroup>

      <UFormGroup v-if="editingReminder" label="Status">
        <UCheckbox v-model="form.is_completed" label="Mark as completed" />
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
const editingReminder = ref<any>(null)
const reminders = ref<any[]>([])
const vehicles = ref<any[]>([])

const columns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'type', label: 'Type' },
  { key: 'title', label: 'Title' },
  { key: 'due_date', label: 'Due Date' },
  { key: 'is_completed', label: 'Done' },
  { key: 'actions', label: '' }
]

const typeOptions = [
  { label: 'Tax (Pajak)', value: 'TAX' },
  { label: 'Service', value: 'SERVICE' },
  { label: 'Insurance', value: 'INSURANCE' },
  { label: 'KIR', value: 'KIR' },
  { label: 'STNK', value: 'STNK' },
  { label: 'Other', value: 'OTHER' }
]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const overdueCount = computed(() => 
  reminders.value.filter(r => !r.is_completed && new Date(r.due_date) < new Date()).length
)
const dueSoonCount = computed(() => {
  const now = new Date()
  const week = new Date(Date.now() + 7*24*60*60*1000)
  return reminders.value.filter(r => !r.is_completed && new Date(r.due_date) >= now && new Date(r.due_date) <= week).length
})
const upcomingCount = computed(() => {
  const week = new Date(Date.now() + 7*24*60*60*1000)
  return reminders.value.filter(r => !r.is_completed && new Date(r.due_date) > week).length
})
const completedCount = computed(() => reminders.value.filter(r => r.is_completed).length)

const form = reactive({
  vehicle_id: '',
  type: 'OTHER',
  title: '',
  description: '',
  due_date: '',
  reminder_days: 7,
  estimated_cost: null as number | null,
  reference_number: '',
  notes: '',
  is_completed: false
})

const fetchReminders = async () => {
  loading.value = true
  try {
    const res = await $api.get('/fleet/reminders')
    reminders.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchVehicles = async () => {
  try {
    const res = await $api.get('/fleet/vehicles')
    vehicles.value = res.data
  } catch (e) { console.error(e) }
}

const getVehicleName = (id: string) => {
  const v = vehicles.value.find((v: any) => v.id === id)
  return v ? v.plate_number : '-'
}

const openCreate = () => {
  editingReminder.value = null
  const nextMonth = new Date(Date.now() + 30*24*60*60*1000).toISOString().slice(0, 10)
  Object.assign(form, {
    vehicle_id: '', type: 'OTHER', title: '', description: '',
    due_date: nextMonth, reminder_days: 7, estimated_cost: null,
    reference_number: '', notes: '', is_completed: false
  })
  isSlideoverOpen.value = true
}

const openEdit = (reminder: any) => {
  editingReminder.value = reminder
  Object.assign(form, {
    vehicle_id: reminder.vehicle_id,
    type: reminder.type,
    title: reminder.title,
    description: reminder.description || '',
    due_date: reminder.due_date,
    reminder_days: reminder.reminder_days || 7,
    estimated_cost: reminder.estimated_cost,
    reference_number: reminder.reference_number || '',
    notes: reminder.notes || '',
    is_completed: reminder.is_completed
  })
  isSlideoverOpen.value = true
}

const saveReminder = async () => {
  if (!form.vehicle_id || !form.title || !form.due_date) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.estimated_cost) delete payload.estimated_cost
    
    if (editingReminder.value) {
      await $api.put(`/fleet/reminders/${editingReminder.value.id}`, payload)
      toast.add({ title: 'Reminder updated!' })
    } else {
      await $api.post('/fleet/reminders', payload)
      toast.add({ title: 'Reminder created!' })
    }
    isSlideoverOpen.value = false
    fetchReminders()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const toggleComplete = async (reminder: any) => {
  try {
    await $api.put(`/fleet/reminders/${reminder.id}`, { is_completed: reminder.is_completed })
    toast.add({ title: reminder.is_completed ? 'Marked as complete!' : 'Marked as incomplete' })
    fetchReminders()
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const deleteReminder = async (reminder: any) => {
  if (!confirm(`Delete reminder "${reminder.title}"?`)) return
  try {
    await $api.delete(`/fleet/reminders/${reminder.id}`)
    toast.add({ title: 'Reminder deleted!' })
    fetchReminders()
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    TAX: 'red', SERVICE: 'blue', INSURANCE: 'green', KIR: 'yellow', STNK: 'purple'
  }
  return colors[type] || 'gray'
}

const getDueDateColor = (dueDate: string) => {
  const d = new Date(dueDate)
  const now = new Date()
  const week = new Date(Date.now() + 7*24*60*60*1000)
  if (d < now) return 'red'
  if (d <= week) return 'yellow'
  return 'gray'
}

const getDaysRemaining = (dueDate: string) => {
  const d = new Date(dueDate)
  const now = new Date()
  const diff = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return `${Math.abs(diff)} days overdue`
  if (diff === 0) return 'Due today'
  if (diff === 1) return 'Due tomorrow'
  return `${diff} days remaining`
}

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'

onMounted(() => {
  fetchReminders()
  fetchVehicles()
})
</script>
