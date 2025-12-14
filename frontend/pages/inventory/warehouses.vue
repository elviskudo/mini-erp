<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Warehouses</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">Add Warehouse</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="warehouses" :loading="loading">
         <template #actions-data="{ row }">
             <UButton icon="i-heroicons-map-pin" color="gray" variant="ghost" size="xs" @click="viewLocations(row)" />
        </template>
      </UTable>
    </UCard>

    <!-- Create Warehouse Modal -->
    <UModal v-model="isOpen">
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }">
        <template #header>
          <h3 class="text-base font-semibold leading-6 text-gray-900">
            Create Warehouse
          </h3>
        </template>

        <form @submit.prevent="createWarehouse" class="space-y-4">
            <UFormGroup label="Name" name="name" required>
                <UInput v-model="form.name" placeholder="e.g. Central Warehouse" />
            </UFormGroup>
             <UFormGroup label="Address" name="address">
                <UInput v-model="form.address" placeholder="e.g. 123 Industrial Park" />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Save</UButton>
            </div>
        </form>
      </UCard>
    </UModal>

    <!-- View Locations Modal (Simple List for now) -->
    <UModal v-model="isLocationsOpen">
         <UCard>
            <template #header>
                <div class="flex justify-between items-center">
                    <h3 class="font-semibold">Locations in {{ selectedWarehouse?.name }}</h3>
                    <UButton size="xs" icon="i-heroicons-plus" @click="openCreateLocation">Add Location</UButton>
                </div>
            </template>
            
            <div class="space-y-2">
                 <div v-for="loc in locations" :key="loc.id" class="flex justify-between p-2 bg-gray-50 rounded">
                    <span>{{ loc.name }} ({{ loc.code }})</span>
                    <span class="text-xs text-gray-500">{{ loc.type }}</span>
                 </div>
                 <div v-if="locations.length === 0" class="text-sm text-gray-400">No locations found.</div>
            </div>

            <!-- Nested Create Location Form -->
             <div v-if="isCreatingLocation" class="mt-4 p-4 border rounded bg-white">
                <h4 class="text-sm font-medium mb-2">New Location</h4>
                <form @submit.prevent="createLocation" class="space-y-2">
                    <UInput v-model="locForm.name" placeholder="Location Name" size="sm" />
                    <UInput v-model="locForm.code" placeholder="Code (e.g. A-01)" size="sm" />
                    <USelect v-model="locForm.type" :options="['Receiving', 'Storage', 'Picking', 'Production', 'Quarantine']" size="sm" />
                    <div class="flex justify-end gap-2">
                        <UButton size="2xs" color="gray" @click="isCreatingLocation = false">Cancel</UButton>
                        <UButton size="2xs" type="submit" :loading="locSubmitting">Add</UButton>
                    </div>
                </form>
             </div>
         </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const isOpen = ref(false)
const isLocationsOpen = ref(false)
const isCreatingLocation = ref(false)
const loading = ref(false)
const submitting = ref(false)
const locSubmitting = ref(false)

const warehouses = ref([])
const locations = ref([])
const selectedWarehouse = ref(null)

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'address', label: 'Address' },
  { key: 'actions', label: 'Locations' }
]

const form = reactive({ name: '', address: '' })
const locForm = reactive({ name: '', code: '', type: 'Storage' })

const fetchWarehouses = async () => {
    loading.value = true
    try {
        const res = await $api.get('/inventory/warehouses')
        warehouses.value = res.data
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const openCreateModal = () => {
    form.name = ''
    form.address = ''
    isOpen.value = true
}

const createWarehouse = async () => {
    submitting.value = true
    try {
        await $api.post('/inventory/warehouses', form)
        isOpen.value = false
        fetchWarehouses()
    } catch (e) { alert('Failed') }
    finally { submitting.value = false }
}

const viewLocations = async (warehouse: any) => {
    selectedWarehouse.value = warehouse
    // Fetch locations for this warehouse
    // Assuming backend returns locations in warehouse object or separate endpoint?
    // Checking backend/routers/inventory.py... 
    // It has `read_warehouses` (selectinload(locations))... So `warehouse.locations` should exist if fetched correctly.
    // However, the table rows might not have deep objects if we didn't type it well or if nuxt ui flattens it?
    // Let's assume we need to re-fetch or use what we have.
    // Ideally we should have a `GET /inventory/warehouses/{id}/locations` or just use the loaded data.
    // Let's try to use `warehouse.locations` if available, else fetch.
    if (warehouse.locations) {
        locations.value = warehouse.locations
    } else {
        locations.value = [] // Fallback
    }
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
        const payload = {
            warehouse_id: selectedWarehouse.value.id,
            ...locForm
        }
        await $api.post('/inventory/locations', payload)
        // Refresh locations - simplified by just re-fetching all warehouses for now or add to local list
        // Let's re-fetch warehouses to be safe and update current view
        await fetchWarehouses()
        const updated = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
        if (updated) locations.value = updated.locations
        isCreatingLocation.value = false
    } catch (e) { alert('Failed to add location') }
    finally { locSubmitting.value = false }
}

onMounted(() => {
    fetchWarehouses()
})
</script>
