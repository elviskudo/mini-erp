<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Initial Setup</h1>
        <p class="text-gray-500">Configure your company settings to get started</p>
      </div>
    </div>

    <!-- Setup Progress -->
    <UCard>
      <div class="flex items-center gap-4 mb-6">
        <div v-for="(step, idx) in steps" :key="idx" class="flex items-center">
          <div 
            class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            :class="[
              currentStep > idx ? 'bg-green-500 text-white' :
              currentStep === idx ? 'bg-primary-500 text-white' :
              'bg-gray-200 text-gray-500'
            ]"
          >
            <UIcon v-if="currentStep > idx" name="i-heroicons-check" class="w-5 h-5" />
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <span class="ml-2 text-sm font-medium" :class="currentStep >= idx ? 'text-gray-900' : 'text-gray-400'">
            {{ step.title }}
          </span>
          <div v-if="idx < steps.length - 1" class="w-12 h-0.5 mx-3 bg-gray-200"></div>
        </div>
      </div>
    </UCard>

    <!-- Step Content -->
    <UCard>
      <!-- Step 1: Company Info -->
      <div v-if="currentStep === 0" class="space-y-4">
        <h2 class="text-lg font-semibold">Company Information</h2>
        
        <UFormGroup label="Company Name" required>
          <UInput v-model="settings.companyName" placeholder="Enter company name" />
        </UFormGroup>
        
        <UFormGroup label="Company Logo">
          <div 
            class="relative border-2 border-dashed rounded-lg p-6 transition-colors"
            :class="[
              isDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
            ]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <!-- Preview -->
            <div v-if="logoPreview" class="flex items-center gap-4">
              <img :src="logoPreview" alt="Logo preview" class="w-20 h-20 object-contain rounded-lg border" />
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-900">{{ logoFile?.name }}</p>
                <p class="text-xs text-gray-500">{{ formatFileSize(logoFile?.size || 0) }}</p>
              </div>
              <UButton icon="i-heroicons-trash" color="red" variant="ghost" @click="removeLogo" />
            </div>
            
            <!-- Dropzone -->
            <div v-else class="text-center">
              <UIcon name="i-heroicons-cloud-arrow-up" class="w-10 h-10 text-gray-400 mx-auto mb-2" />
              <p class="text-sm text-gray-600 mb-1">
                <span class="text-primary-600 font-medium cursor-pointer" @click="triggerFileInput">Click to upload</span>
                or drag and drop
              </p>
              <p class="text-xs text-gray-500">PNG, JPG up to 2MB</p>
            </div>
            
            <input 
              ref="fileInput"
              type="file" 
              accept="image/png,image/jpeg,image/jpg"
              class="hidden"
              @change="handleFileSelect"
            />
          </div>
        </UFormGroup>
        
        <UFormGroup label="Industry">
          <USelect v-model="settings.industry" :options="industries" placeholder="Select industry" />
        </UFormGroup>
      </div>

      <!-- Step 2: Regional Settings -->
      <div v-if="currentStep === 1" class="space-y-4">
        <h2 class="text-lg font-semibold">Regional Settings</h2>
        
        <UFormGroup label="Default Currency" required>
          <USelect v-model="settings.currency" :options="currencies" />
        </UFormGroup>
        
        <UFormGroup label="Timezone" required>
          <USelect v-model="settings.timezone" :options="timezones" />
        </UFormGroup>
        
        <UFormGroup label="Date Format">
          <USelect v-model="settings.dateFormat" :options="dateFormats" />
        </UFormGroup>
      </div>

      <!-- Step 3: Warehouse -->
      <div v-if="currentStep === 2" class="space-y-4">
        <h2 class="text-lg font-semibold">Default Warehouse</h2>
        <p class="text-sm text-gray-500">Set up your primary warehouse location. Click on the map to set location.</p>
        
        <UFormGroup label="Warehouse Name" required>
          <UInput v-model="settings.warehouseName" placeholder="e.g. Main Warehouse" />
        </UFormGroup>
        
        <!-- Map Container - ClientOnly to prevent SSR hydration errors -->
        <UFormGroup label="Location (Click map to set)">
          <ClientOnly>
            <div class="relative rounded-lg overflow-hidden border border-gray-300">
              <div id="warehouse-map" class="h-64 w-full"></div>
              <div v-if="mapLoading" class="absolute inset-0 flex items-center justify-center bg-gray-100">
                <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-gray-500" />
              </div>
            </div>
            <template #fallback>
              <div class="h-64 w-full bg-gray-100 rounded-lg flex items-center justify-center">
                <span class="text-gray-500">Loading map...</span>
              </div>
            </template>
          </ClientOnly>
          <p v-if="settings.warehouseLat && settings.warehouseLng" class="text-xs text-gray-500 mt-1">
            📍 Lat: {{ settings.warehouseLat.toFixed(6) }}, Lng: {{ settings.warehouseLng.toFixed(6) }}
          </p>
        </UFormGroup>
        
        <UFormGroup label="Address">
          <UTextarea 
            v-model="settings.warehouseAddress" 
            placeholder="Address will be filled when you click on the map" 
            rows="3"
            readonly
          />
        </UFormGroup>
      </div>

      <!-- Step 4: Complete -->
      <div v-if="currentStep === 3" class="text-center py-8">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <UIcon name="i-heroicons-check" class="w-8 h-8 text-green-600" />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Setup Complete!</h2>
        <p class="text-gray-500 mb-6">Your company is ready to use Mini ERP</p>
        <UButton @click="navigateTo('/')">Go to Dashboard</UButton>
      </div>

      <!-- Navigation -->
      <div v-if="currentStep < 3" class="flex justify-between mt-8 pt-6 border-t">
        <UButton 
          v-if="currentStep > 0" 
          variant="ghost" 
          @click="currentStep--"
        >
          Back
        </UButton>
        <div v-else></div>
        
        <UButton :loading="saving" @click="nextStep">
          {{ currentStep === 2 ? 'Complete Setup' : 'Next' }}
        </UButton>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const currentStep = ref(0)

const steps = [
  { title: 'Company Info' },
  { title: 'Regional' },
  { title: 'Warehouse' },
  { title: 'Complete' }
]

const settings = reactive({
  companyName: '',
  industry: '',
  currency: 'IDR',
  timezone: 'Asia/Jakarta',
  dateFormat: 'DD/MM/YYYY',
  warehouseName: '',
  warehouseAddress: '',
  warehouseLat: null as number | null,
  warehouseLng: null as number | null
})

const industries = [
  'Manufacturing',
  'Retail',
  'Wholesale',
  'Services',
  'Technology',
  'Food & Beverage',
  'Other'
]

const currencies = [
  { label: 'IDR - Indonesian Rupiah', value: 'IDR' },
  { label: 'USD - US Dollar', value: 'USD' },
  { label: 'EUR - Euro', value: 'EUR' },
  { label: 'SGD - Singapore Dollar', value: 'SGD' }
]

const timezones = [
  { label: 'Asia/Jakarta (WIB)', value: 'Asia/Jakarta' },
  { label: 'Asia/Makassar (WITA)', value: 'Asia/Makassar' },
  { label: 'Asia/Jayapura (WIT)', value: 'Asia/Jayapura' },
  { label: 'Asia/Singapore', value: 'Asia/Singapore' }
]

const dateFormats = [
  { label: 'DD/MM/YYYY', value: 'DD/MM/YYYY' },
  { label: 'MM/DD/YYYY', value: 'MM/DD/YYYY' },
  { label: 'YYYY-MM-DD', value: 'YYYY-MM-DD' }
]

const toast = useToast()
const saving = ref(false)

const nextStep = async () => {
  // On step 2 (warehouse), save the warehouse before proceeding
  if (currentStep.value === 2) {
    if (!settings.warehouseName) {
      toast.add({ title: 'Error', description: 'Warehouse name is required', color: 'red' })
      return
    }
    
    saving.value = true
    try {
      const token = useCookie('auth_token')
      const authHeader = token.value ? { Authorization: `Bearer ${token.value}` } : {}
      
      // Generate warehouse code from name (e.g. "Main Warehouse" -> "MAIN-WH")
      const warehouseCode = settings.warehouseName
        .toUpperCase()
        .replace(/[^A-Z0-9]/g, '-')
        .substring(0, 10) + '-WH'
      
      // Save warehouse to backend
      await $fetch('/api/inventory/warehouses', {
        method: 'POST',
        headers: authHeader,
        body: {
          code: warehouseCode,
          name: settings.warehouseName,
          address: settings.warehouseAddress || '-'
        }
      })
      
      // Mark tenant setup as complete
      await $fetch('/api/tenants/complete-setup', {
        method: 'POST',
        headers: authHeader
      })
      
      toast.add({ title: 'Success', description: 'Setup completed successfully!' })
      currentStep.value++
      
      // Refresh page to update menus
      setTimeout(() => {
        window.location.reload()
      }, 1500)
    } catch (e: any) {
      toast.add({ title: 'Error', description: e.data?.detail || 'Failed to complete setup', color: 'red' })
    } finally {
      saving.value = false
    }
    return
  }
  
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

// Dropzone state
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const logoFile = ref<File | null>(null)
const logoPreview = ref<string | null>(null)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    processFile(file)
  }
}

const processFile = (file: File) => {
  // Validate file type
  if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
    alert('Please upload a PNG or JPG image')
    return
  }
  
  // Validate file size (2MB max)
  if (file.size > 2 * 1024 * 1024) {
    alert('File size must be less than 2MB')
    return
  }
  
  logoFile.value = file
  
  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    logoPreview.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

const removeLogo = () => {
  logoFile.value = null
  logoPreview.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// ============ Map Logic ============
const mapLoading = ref(true)
let map: any = null
let marker: any = null

// Initialize map when warehouse step is shown
watch(currentStep, async (newStep) => {
  if (newStep === 2) {
    // Wait for DOM to render
    await nextTick()
    setTimeout(() => initMap(), 100)
  }
})

const initMap = async () => {
  if (typeof window === 'undefined') return
  
  const mapContainer = document.getElementById('warehouse-map')
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
  
  // Default center (Jakarta, Indonesia) - will be overridden by geolocation
  let defaultLat = -6.2088
  let defaultLng = 106.8456
  
  // Create map first with default location
  map = L.map('warehouse-map').setView([defaultLat, defaultLng], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map)
  
  mapLoading.value = false
  
  // Try to get user's current location
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        
        // Center map on user's location
        map.setView([latitude, longitude], 15)
        
        // Place marker and set initial location
        if (marker) {
          marker.setLatLng([latitude, longitude])
        } else {
          marker = L.marker([latitude, longitude]).addTo(map)
        }
        
        settings.warehouseLat = latitude
        settings.warehouseLng = longitude
        
        // Get address for current location
        await reverseGeocode(latitude, longitude)
      },
      (error) => {
        console.log('Geolocation error:', error.message)
        // Keep default location
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }
  
  // Add click handler
  map.on('click', async (e: any) => {
    const { lat, lng } = e.latlng
    
    // Update marker
    if (marker) {
      marker.setLatLng([lat, lng])
    } else {
      marker = L.marker([lat, lng]).addTo(map)
    }
    
    settings.warehouseLat = lat
    settings.warehouseLng = lng
    
    // Reverse geocode to get address
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
      settings.warehouseAddress = data.display_name
    }
  } catch (e) {
    console.error('Reverse geocode failed:', e)
    settings.warehouseAddress = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`
  }
}
</script>
