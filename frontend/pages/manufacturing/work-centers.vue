<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Work Centers</h2>
        <p class="text-gray-500">Manage manufacturing work centers</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Add Work Center</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable 
        :columns="columns" 
        :rows="workCenters" 
        :loading="loading"
        search-placeholder="Search work centers..."
      >
        <template #primary-data="{ row }">
          <UBadge v-if="isPrimary(row)" color="yellow" variant="soft" class="gap-1">
            <UIcon name="i-heroicons-star-solid" class="w-3 h-3" />
            Primary
          </UBadge>
        </template>
        <template #status-data="{ row }">
          <UButton 
            :color="row.is_active ? 'green' : 'red'" 
            variant="soft"
            size="xs"
            @click="openStatusModal(row)"
          >
            {{ row.is_active ? 'Active' : 'Inactive' }}
          </UButton>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton 
              v-if="canDelete"
              icon="i-heroicons-trash" 
              color="red" 
              variant="ghost" 
              size="xs" 
              @click="deleteWorkCenter(row)" 
            />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Work Center' : 'Add Work Center'"
      :loading="submitting"
      @submit="saveWorkCenter"
    >
      <div class="space-y-4">
        <UFormGroup label="Name" required hint="Display name for this work center" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g. Assembly Line 1" />
        </UFormGroup>
        
        <UFormGroup label="Code" required hint="Unique identifier code for internal reference" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.code" placeholder="e.g. WC-001" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Hourly Rate" hint="Cost per hour for labor" :ui="{ hint: 'text-xs text-gray-400' }">
            <CurrencyInput v-model="form.cost_per_hour" :currency="currencyCode" />
          </UFormGroup>
          <UFormGroup label="Capacity (Hrs/Day)" hint="Max productive hours/day" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.capacity_hours" type="number" step="0.1" />
          </UFormGroup>
        </div>
        
        <!-- Map Location Picker -->
        <UFormGroup label="Location" hint="Click map to set GPS coordinates" :ui="{ hint: 'text-xs text-gray-400' }">
          <ClientOnly>
            <div class="relative rounded-lg overflow-hidden border border-gray-300">
              <div id="workcenter-map" class="h-48 w-full"></div>
              <div v-if="mapLoading" class="absolute inset-0 flex items-center justify-center bg-gray-100">
                <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-gray-500" />
              </div>
            </div>
            <template #fallback>
              <div class="h-48 w-full bg-gray-100 rounded-lg flex items-center justify-center">
                <span class="text-gray-500">Loading map...</span>
              </div>
            </template>
          </ClientOnly>
          <p v-if="form.latitude && form.longitude" class="text-xs text-gray-500 mt-1">
            📍 Lat: {{ form.latitude.toFixed(6) }}, Lng: {{ form.longitude.toFixed(6) }}
          </p>
        </UFormGroup>
        
        <UFormGroup label="Address" hint="Auto-filled from map" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea 
            v-model="form.location" 
            placeholder="Address will be filled when you click on the map" 
            rows="2"
            readonly
          />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Status Change Modal -->
    <UModal v-model="isStatusModalOpen">
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 text-blue-600" />
            <span class="font-semibold">Change Work Center Status</span>
          </div>
        </template>
        <p class="text-gray-600">
          Are you sure you want to change the status of <strong>{{ statusTarget?.name }}</strong> 
          from <UBadge :color="statusTarget?.is_active ? 'green' : 'red'" variant="soft">{{ statusTarget?.is_active ? 'Active' : 'Inactive' }}</UBadge>
          to <UBadge :color="!statusTarget?.is_active ? 'green' : 'red'" variant="soft">{{ !statusTarget?.is_active ? 'Active' : 'Inactive' }}</UBadge>?
        </p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="gray" variant="outline" @click="isStatusModalOpen = false">Cancel</UButton>
            <UButton :color="!statusTarget?.is_active ? 'green' : 'red'" :loading="submitting" @click="toggleStatus">
              {{ !statusTarget?.is_active ? 'Activate' : 'Deactivate' }}
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Delete Confirmation Modal -->
    <UModal v-model="isDeleteModalOpen">
      <UCard>
        <template #header>
          <div class="flex items-center gap-2 text-red-600">
            <UIcon name="i-heroicons-exclamation-triangle" class="w-6 h-6" />
            <span class="font-semibold">Delete Work Center</span>
          </div>
        </template>
        <p class="text-gray-600">
          Are you sure you want to delete <strong>{{ deleteTarget?.name }}</strong>? This action cannot be undone.
        </p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="gray" variant="outline" @click="isDeleteModalOpen = false">Cancel</UButton>
            <UButton color="red" :loading="deleting" @click="confirmDeleteWorkCenter">Delete</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const { currencyCode, formatCurrency } = useCurrency()
const toast = useToast()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const editMode = ref(false)
const workCenters = ref<any[]>([])
const mapLoading = ref(true)
let map: any = null
let marker: any = null

// Delete modal state
const isDeleteModalOpen = ref(false)
const deleteTarget = ref<any>(null)
const deleting = ref(false)

// Status modal state
const isStatusModalOpen = ref(false)
const statusTarget = ref<any>(null)

// Check if work center is primary (only one exists or first in list)
const isPrimary = (row: any) => {
  if (workCenters.value.length === 1) return true
  // First active work center is considered primary
  const activeWCs = workCenters.value.filter((wc: any) => wc.is_active)
  return activeWCs.length > 0 && activeWCs[0]?.id === row.id
}

// Can only delete if more than one work center exists
const canDelete = computed(() => workCenters.value.length > 1)

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'primary', label: '' },
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
    location: '',
    latitude: null as number | null,
    longitude: null as number | null
})

const resetForm = () => {
    Object.assign(form, {
        id: '',
        name: '',
        code: '',
        cost_per_hour: 0,
        capacity_hours: 8,
        location: '',
        latitude: null,
        longitude: null
    })
    // Reset map state
    map = null
    marker = null
    mapLoading.value = true
}

const fetchWorkCenters = async () => {
    loading.value = true
    try {
        const res: any = await $fetch('/api/manufacturing/work-centers', {
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
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
    // Wait for slideover to open then init map
    setTimeout(() => initMap(), 300)
}

const openEdit = (row: any) => {
    Object.assign(form, row)
    editMode.value = true
    isOpen.value = true
    // Wait for slideover to open then init map with existing location
    setTimeout(() => initMap(), 300)
}

// ============ Map Logic ============
const initMap = async () => {
  if (typeof window === 'undefined') return
  
  const mapContainer = document.getElementById('workcenter-map')
  if (!mapContainer || map) return
  
  // Load Leaflet dynamically
  const L = await import('leaflet')
  
  // Load Leaflet CSS
  if (!document.querySelector('link[href*="leaflet.css"]')) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
  }
  
  // Default or existing location
  let defaultLat = form.latitude || -6.2088
  let defaultLng = form.longitude || 106.8456
  
  map = L.map('workcenter-map').setView([defaultLat, defaultLng], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map)
  
  mapLoading.value = false
  
  // If editing with existing coordinates, place marker
  if (form.latitude && form.longitude) {
    marker = L.marker([form.latitude, form.longitude]).addTo(map)
    map.setView([form.latitude, form.longitude], 15)
  } else {
    // Try to get user's current location
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords
          map.setView([latitude, longitude], 15)
          
          if (marker) {
            marker.setLatLng([latitude, longitude])
          } else {
            marker = L.marker([latitude, longitude]).addTo(map)
          }
          
          form.latitude = latitude
          form.longitude = longitude
          await reverseGeocode(latitude, longitude)
        },
        () => { /* Keep default location */ },
        { enableHighAccuracy: true, timeout: 10000 }
      )
    }
  }
  
  // Add click handler
  map.on('click', async (e: any) => {
    const { lat, lng } = e.latlng
    
    if (marker) {
      marker.setLatLng([lat, lng])
    } else {
      marker = L.marker([lat, lng]).addTo(map)
    }
    
    form.latitude = lat
    form.longitude = lng
    await reverseGeocode(lat, lng)
  })
}

const reverseGeocode = async (lat: number, lng: number) => {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`,
      { headers: { 'Accept-Language': 'en' } }
    )
    const data = await response.json()
    
    if (data.display_name) {
      form.location = data.display_name
    }
  } catch (e) {
    console.error('Reverse geocode failed:', e)
    form.location = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`
  }
}

const saveWorkCenter = async () => {
    submitting.value = true
    try {
        const headers = { Authorization: `Bearer ${authStore.token}` }
        if (editMode.value) {
            await $fetch(`/api/manufacturing/work-centers/${form.id}`, {
                method: 'PUT',
                body: form,
                headers
            })
            toast.add({ title: 'Updated', description: 'Work center updated.' })
        } else {
            await $fetch('/api/manufacturing/work-centers', {
                method: 'POST',
                body: form,
                headers
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

const deleteWorkCenter = (row: any) => {
    deleteTarget.value = row
    isDeleteModalOpen.value = true
}

const confirmDeleteWorkCenter = async () => {
    if (!deleteTarget.value) return
    deleting.value = true
    try {
        await $fetch(`/api/manufacturing/work-centers/${deleteTarget.value.id}`, { 
            method: 'DELETE',
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        toast.add({ title: 'Deleted', description: 'Work center deleted successfully.', color: 'green' })
        fetchWorkCenters()
        isDeleteModalOpen.value = false
        deleteTarget.value = null
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to delete work center.', color: 'red' })
    } finally {
        deleting.value = false
    }
}

const openStatusModal = (row: any) => {
    statusTarget.value = row
    isStatusModalOpen.value = true
}

const toggleStatus = async () => {
    if (!statusTarget.value) return
    submitting.value = true
    try {
        const headers = { Authorization: `Bearer ${authStore.token}` }
        await $fetch(`/api/manufacturing/work-centers/${statusTarget.value.id}`, {
            method: 'PUT',
            body: { ...statusTarget.value, is_active: !statusTarget.value.is_active },
            headers
        })
        toast.add({ 
            title: 'Updated', 
            description: `Work center ${!statusTarget.value.is_active ? 'activated' : 'deactivated'} successfully.`,
            color: 'green'
        })
        isStatusModalOpen.value = false
        statusTarget.value = null
        fetchWorkCenters()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to update status.', color: 'red' })
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchWorkCenters()
})
</script>
