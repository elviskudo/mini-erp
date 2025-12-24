<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Vendors</h2>
        <p class="text-gray-500">Manage supplier and vendor records</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton color="gray" variant="outline" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Vendor</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable :columns="columns" :rows="vendors" :loading="loading" search-placeholder="Search vendors...">
        <template #rating-data="{ row }">
          <UBadge :color="getRatingColor(row.rating)" variant="soft">{{ row.rating || 'B' }}</UBadge>
        </template>
        <template #category-data="{ row }">
          <span class="text-sm">{{ row.category || 'Raw Material' }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
        </template>
      </DataTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Vendor' : 'Add Vendor'"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="saveVendor"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Vendor Code" required hint="Unique identifier for this vendor" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="e.g. V-001" />
          </UFormGroup>
          <UFormGroup label="Vendor Name" required hint="Official company or business name" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.name" placeholder="e.g. PT Supplier Abadi" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Rating" required hint="Vendor performance rating" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.rating" :options="ratingOptions" />
          </UFormGroup>
          <UFormGroup label="Category" required hint="Type of products/services" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.category" :options="categoryOptions" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Payment Term" required hint="Default payment terms" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.payment_term" :options="paymentTermOptions" />
          </UFormGroup>
          <UFormGroup label="Credit Limit" required hint="Maximum credit allowed" :ui="{ hint: 'text-xs text-gray-400' }">
            <CurrencyInput v-model="form.credit_limit" :currency="'IDR'" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Email" required hint="Primary contact email" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.email" type="email" placeholder="e.g. contact@vendor.com" />
          </UFormGroup>
          <UFormGroup label="Phone" required hint="Primary contact number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.phone" placeholder="e.g. +62 21 1234567" />
          </UFormGroup>
        </div>
        
        <!-- Map Location Picker -->
        <UFormGroup label="Location" hint="Click map to set vendor location" :ui="{ hint: 'text-xs text-gray-400' }">
          <ClientOnly>
            <div class="relative rounded-lg overflow-hidden border border-gray-300">
              <div id="vendor-map" class="h-48 w-full"></div>
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
        
        <UFormGroup label="Address" required hint="Complete business address (auto-filled from map)" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.address" rows="3" placeholder="Click on map or enter address manually" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const toast = useToast()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const editMode = ref(false)
const vendors = ref<any[]>([])
const mapLoading = ref(true)

// Map variables
let map: any = null
let marker: any = null

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'rating', label: 'Rating' },
  { key: 'category', label: 'Category' },
  { key: 'payment_term', label: 'Payment Term' },
  { key: 'credit_limit', label: 'Credit Limit' },
  { key: 'phone', label: 'Phone' },
  { key: 'actions', label: '' }
]

const ratingOptions = [
  { label: 'A - Excellent', value: 'A' },
  { label: 'B - Good', value: 'B' },
  { label: 'C - Fair', value: 'C' }
]

const categoryOptions = [
  { label: 'Raw Material', value: 'Raw Material' },
  { label: 'Finished Goods', value: 'Finished Goods' },
  { label: 'Both', value: 'Both' }
]

const paymentTermOptions = [
  { label: 'Cash (Lunas)', value: 'Cash' },
  { label: 'Net 7 Hari', value: 'Net 7' },
  { label: 'Net 15 Hari', value: 'Net 15' },
  { label: 'Net 30 Hari', value: 'Net 30' },
  { label: 'Net 60 Hari', value: 'Net 60' },
  { label: '3 Termin', value: '3 Termin' },
  { label: '6 Termin', value: '6 Termin' },
  { label: '12 Termin', value: '12 Termin' }
]

const exportItems = [
  [{
    label: 'Export as Excel',
    icon: 'i-heroicons-table-cells',
    click: () => exportData('xlsx')
  }, {
    label: 'Export as CSV',
    icon: 'i-heroicons-document-text',
    click: () => exportData('csv')
  }, {
    label: 'Export as PDF',
    icon: 'i-heroicons-document',
    click: () => exportData('pdf')
  }]
]

const form = reactive({
    id: '',
    name: '',
    code: '',
    email: '',
    phone: '',
    address: '',
    rating: 'B',
    category: 'Raw Material',
    payment_term: 'Net 30',
    credit_limit: 0,
    latitude: null as number | null,
    longitude: null as number | null
})

// Form validation - button enabled only when all required fields are filled
const isFormValid = computed(() => {
    return form.code.trim() !== '' && 
           form.name.trim() !== '' && 
           form.email.trim() !== '' && 
           form.phone.trim() !== '' && 
           form.address.trim() !== '' &&
           form.rating !== '' &&
           form.category !== '' &&
           form.payment_term !== ''
})

const resetForm = () => {
    Object.assign(form, {
        id: '',
        name: '',
        code: '',
        email: '',
        phone: '',
        address: '',
        rating: 'B',
        category: 'Raw Material',
        payment_term: 'Net 30',
        credit_limit: 0,
        latitude: null,
        longitude: null
    })
    // Reset map state
    map = null
    marker = null
    mapLoading.value = true
}

const exportData = async (format: string) => {
    try {
        const res = await $fetch(`/api/export/vendors?format=${format}`, { responseType: 'blob' })
        const blob = new Blob([res as BlobPart])
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `vendors.${format}`
        a.click()
        URL.revokeObjectURL(url)
    } catch (e) {
        toast.add({ title: 'Error', description: 'Export failed', color: 'red' })
    }
}

const getRatingColor = (rating: string) => {
    switch (rating) {
        case 'A': return 'green'
        case 'B': return 'yellow'
        case 'C': return 'red'
        default: return 'gray'
    }
}

const fetchVendors = async () => {
    loading.value = true
    try {
        const headers = { Authorization: `Bearer ${authStore.token}` }
        const res: any = await $fetch('/api/procurement/vendors', { headers })
        vendors.value = res
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
  
  const mapContainer = document.getElementById('vendor-map')
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
  
  // Default or existing location (Jakarta)
  let defaultLat = form.latitude || -6.2088
  let defaultLng = form.longitude || 106.8456
  
  map = L.map('vendor-map').setView([defaultLat, defaultLng], 13)
  
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
      form.address = data.display_name
    }
  } catch (e) {
    console.error('Reverse geocode failed:', e)
    form.address = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`
  }
}

const saveVendor = async () => {
    submitting.value = true
    try {
        const headers = { Authorization: `Bearer ${authStore.token}` }
        if (editMode.value) {
            await $fetch(`/api/procurement/vendors/${form.id}`, {
                method: 'PUT',
                headers,
                body: form
            })
            toast.add({ title: 'Updated', description: 'Vendor updated.', color: 'green' })
        } else {
            await $fetch('/api/procurement/vendors', {
                method: 'POST',
                headers,
                body: form
            })
            toast.add({ title: 'Created', description: 'Vendor created.', color: 'green' })
        }
        isOpen.value = false
        fetchVendors()
        resetForm()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to save vendor.', color: 'red' })
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchVendors()
})
</script>
