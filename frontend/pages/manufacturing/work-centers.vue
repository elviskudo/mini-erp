<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Work Centers</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="isOpen = true">Add Work Center</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="workCenters" :loading="loading">
        <template #status-data="{ row }">
            <UBadge :color="row.is_active ? 'green' : 'red'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
             <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="deleteWorkCenter(row.id)" />
        </template>
      </UTable>
    </UCard>

    <!-- Create Modal -->
    <UModal v-model="isOpen">
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }">
        <template #header>
          <h3 class="text-base font-semibold leading-6 text-gray-900">
            Create Work Center
          </h3>
        </template>

        <form @submit.prevent="createWorkCenter" class="space-y-4">
            <UFormGroup label="Name" name="name" required>
                <UInput v-model="form.name" placeholder="e.g. Assembly Line 1" />
            </UFormGroup>
            
            <UFormGroup label="Code" name="code" required>
                <UInput v-model="form.code" placeholder="e.g. WC-001" />
            </UFormGroup>

            <div class="grid grid-cols-2 gap-4">
                 <UFormGroup label="Hourly Rate ($)" name="cost_per_hour">
                    <UInput v-model="form.cost_per_hour" type="number" step="0.01" />
                </UFormGroup>
                 <UFormGroup label="Capacity (Hrs/Day)" name="capacity_hours">
                    <UInput v-model="form.capacity_hours" type="number" step="0.1" />
                </UFormGroup>
            </div>
             <UFormGroup label="Location Ref" name="location">
                <UInput v-model="form.location" placeholder="e.g. Building A" />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Save</UButton>
            </div>
        </form>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const workCenters = ref([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'cost_per_hour', label: 'Rate ($/hr)' },
  { key: 'capacity_hours', label: 'Capacity' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const form = reactive({
    name: '',
    code: '',
    cost_per_hour: 0,
    capacity_hours: 8,
    location: ''
})

const fetchWorkCenters = async () => {
    loading.value = true
    try {
        const res = await $api.get('/manufacturing/work-centers')
        workCenters.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const createWorkCenter = async () => {
    submitting.value = true
    try {
        await $api.post('/manufacturing/work-centers', form)
        isOpen.value = false
        // Reset form
        form.name = ''
        form.code = ''
        form.cost_per_hour = 0
        fetchWorkCenters()
    } catch (e) {
        alert('Failed to create')
    } finally {
        submitting.value = false
    }
}

const deleteWorkCenter = async (id: string) => {
    if(!confirm('Are you sure?')) return
    try {
         // Assuming delete endpoint exists, if not need to add it or skip
         // Checked backend: router has delete /{wc_id}
         await $api.delete(`/manufacturing/work-centers/${id}`)
         fetchWorkCenters()
    } catch (e) {
        alert('Failed to delete')
    }
}

onMounted(() => {
    fetchWorkCenters()
})
</script>
