<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Warehouses</h2>
        <p class="text-gray-500">Manage warehouse locations</p>
      </div>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">Add Warehouse</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable :columns="columns" :rows="warehouses" :loading="loading" search-placeholder="Search warehouses...">
         <template #actions-data="{ row }">
            <div class="flex gap-1">
              <UButton icon="i-heroicons-map-pin" color="gray" variant="ghost" size="xs" @click="viewLocations(row)" />
              <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="editWarehouse(row)" />
            </div>
         </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Warehouse Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Warehouse' : 'Add Warehouse'"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="createWarehouse"
    >
      <div class="space-y-4">
        <UFormGroup label="Warehouse Name" name="name" required hint="Unique warehouse identifier" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g. Central Warehouse" />
        </UFormGroup>
        <UFormGroup label="Address" name="address" required hint="Physical location address" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.address" placeholder="e.g. 123 Industrial Park" rows="3" />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- View Locations Slideover -->
    <USlideover v-model="isLocationsOpen">
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <h3 class="text-lg font-semibold">Locations in {{ selectedWarehouse?.name }}</h3>
          <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="isLocationsOpen = false" />
        </div>
        
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <UButton size="sm" icon="i-heroicons-plus" @click="openCreateLocation">Add Location</UButton>
          
          <div class="space-y-2">
            <div v-for="loc in locations" :key="loc.id" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <div>
                <p class="font-medium">{{ loc.name }}</p>
                <p class="text-sm text-gray-500">{{ loc.code }}</p>
              </div>
              <UBadge color="gray" variant="subtle">{{ loc.type }}</UBadge>
            </div>
            <div v-if="locations.length === 0" class="text-sm text-gray-400 text-center py-8">
              No locations found.
            </div>
          </div>
          
          <!-- Nested Create Location Form -->
          <div v-if="isCreatingLocation" class="p-4 border rounded-lg bg-white">
            <h4 class="text-sm font-medium mb-3">New Location</h4>
            <form @submit.prevent="createLocation" class="space-y-3">
              <UFormGroup label="Name" required>
                <UInput v-model="locForm.name" placeholder="Location Name" size="sm" />
              </UFormGroup>
              <UFormGroup label="Code" required>
                <UInput v-model="locForm.code" placeholder="e.g. A-01" size="sm" />
              </UFormGroup>
              <UFormGroup label="Type">
                <USelect v-model="locForm.type" :options="['Receiving', 'Storage', 'Picking', 'Production', 'Quarantine']" size="sm" />
              </UFormGroup>
              <div class="flex justify-end gap-2">
                <UButton size="sm" color="gray" variant="ghost" @click="isCreatingLocation = false">Cancel</UButton>
                <UButton size="sm" type="submit" :loading="locSubmitting">Add Location</UButton>
              </div>
            </form>
          </div>
        </div>
      </div>
    </USlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const isOpen = ref(false)
const isLocationsOpen = ref(false)
const isCreatingLocation = ref(false)
const loading = ref(false)
const submitting = ref(false)
const locSubmitting = ref(false)
const editMode = ref(false)

const warehouses = ref<any[]>([])
const locations = ref<any[]>([])
const selectedWarehouse = ref<any>(null)

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'address', label: 'Address' },
  { key: 'actions', label: '' }
]

const form = reactive({ id: '', name: '', address: '' })
const locForm = reactive({ name: '', code: '', type: 'Storage' })

// Form validation - button enabled only when required fields are filled
const isFormValid = computed(() => {
    return form.name.trim() !== '' && form.address.trim() !== ''
})

const fetchWarehouses = async () => {
    loading.value = true
    try {
        const res: any = await $fetch('/api/inventory/warehouses')
        warehouses.value = res
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const openCreateModal = () => {
    form.id = ''
    form.name = ''
    form.address = ''
    editMode.value = false
    isOpen.value = true
}

const editWarehouse = (row: any) => {
    form.id = row.id
    form.name = row.name
    form.address = row.address || ''
    editMode.value = true
    isOpen.value = true
}

const createWarehouse = async () => {
    submitting.value = true
    try {
        if (editMode.value) {
            await $fetch(`/api/inventory/warehouses/${form.id}`, {
                method: 'PUT',
                body: { name: form.name, address: form.address }
            })
        } else {
            await $fetch('/api/inventory/warehouses', {
                method: 'POST',
                body: form
            })
        }
        isOpen.value = false
        fetchWarehouses()
    } catch (e) { console.error('Failed:', e) }
    finally { submitting.value = false }
}

const viewLocations = async (warehouse: any) => {
    selectedWarehouse.value = warehouse
    locations.value = warehouse.locations || []
    isLocationsOpen.value = true
    isCreatingLocation.value = false
}

const openCreateLocation = () => {
    locForm.name = ''
    locForm.code = ''
    locForm.type = 'Storage'
    isCreatingLocation.value = true
}

const createLocation = async () => {
    if (!selectedWarehouse.value) return
    locSubmitting.value = true
    try {
        await $fetch('/api/inventory/locations', {
            method: 'POST',
            body: {
                warehouse_id: selectedWarehouse.value.id,
                ...locForm
            }
        })
        await fetchWarehouses()
        const updated = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
        if (updated) locations.value = updated.locations || []
        isCreatingLocation.value = false
    } catch (e) { console.error('Failed:', e) }
    finally { locSubmitting.value = false }
}

onMounted(() => {
    fetchWarehouses()
})
</script>
