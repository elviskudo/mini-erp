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
        
        <!-- Map Location Picker -->
        <UFormGroup label="Location (Click map to set)">
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
        
        <UFormGroup label="Address">
          <UTextarea 
            v-model="form.location" 
            placeholder="Address will be filled when you click on the map" 
            rows="2"
            readonly
          />
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
const mapLoading = ref(true)
let map: any = null
let marker: any = null

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
