<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Work Centers</h2>
        <p class="text-gray-500">Manage manufacturing work centers</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Add Work Center</UButton>
    </div>

    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="workCenters" :loading="loading">
        <template #status-data="{ row }">
            <UBadge :color="row.is_active ? 'green' : 'red'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="deleteWorkCenter(row.id)" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Work Center' : 'Add Work Center'"
      :loading="submitting"
      @submit="saveWorkCenter"
    >
      <div class="space-y-4">
        <UFormGroup label="Name" required>
          <UInput v-model="form.name" placeholder="e.g. Assembly Line 1" />
        </UFormGroup>
        
        <UFormGroup label="Code" required>
          <UInput v-model="form.code" placeholder="e.g. WC-001" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Hourly Rate">
            <UInput v-model="form.cost_per_hour" type="number" step="0.01" />
          </UFormGroup>
          <UFormGroup label="Capacity (Hrs/Day)">
            <UInput v-model="form.capacity_hours" type="number" step="0.1" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Location">
          <UInput v-model="form.location" placeholder="e.g. Building A" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const toast = useToast()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const editMode = ref(false)
const workCenters = ref<any[]>([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'cost_per_hour', label: 'Rate/hr' },
  { key: 'capacity_hours', label: 'Capacity' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const form = reactive({
    id: '',
    name: '',
    code: '',
    cost_per_hour: 0,
    capacity_hours: 8,
    location: ''
})

const resetForm = () => {
    Object.assign(form, {
        id: '',
        name: '',
        code: '',
        cost_per_hour: 0,
        capacity_hours: 8,
        location: ''
    })
}

const fetchWorkCenters = async () => {
    loading.value = true
    try {
        const res: any = await $fetch('/api/manufacturing/work-centers')
        workCenters.value = res
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const openCreate = () => {
    resetForm()
    editMode.value = false
    isOpen.value = true
}

const openEdit = (row: any) => {
    Object.assign(form, row)
    editMode.value = true
    isOpen.value = true
}

const saveWorkCenter = async () => {
    submitting.value = true
    try {
        if (editMode.value) {
            await $fetch(`/api/manufacturing/work-centers/${form.id}`, {
                method: 'PUT',
                body: form
            })
            toast.add({ title: 'Updated', description: 'Work center updated.' })
        } else {
            await $fetch('/api/manufacturing/work-centers', {
                method: 'POST',
                body: form
            })
            toast.add({ title: 'Created', description: 'Work center created.' })
        }
        isOpen.value = false
        fetchWorkCenters()
        resetForm()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to save.', color: 'red' })
    } finally {
        submitting.value = false
    }
}

const deleteWorkCenter = async (id: string) => {
    if(!confirm('Are you sure you want to delete this work center?')) return
    try {
        await $fetch(`/api/manufacturing/work-centers/${id}`, { method: 'DELETE' })
        toast.add({ title: 'Deleted', description: 'Work center deleted.' })
        fetchWorkCenters()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to delete.', color: 'red' })
    }
}

onMounted(() => {
    fetchWorkCenters()
})
</script>
