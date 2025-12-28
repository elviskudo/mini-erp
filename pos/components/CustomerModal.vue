<template>
  <UModal v-model="isOpen" :ui="{ width: 'max-w-2xl' }">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold">{{ searchMode ? 'Search Customer' : 'Add Customer' }}</h3>
            <p class="text-sm text-gray-500">{{ searchMode ? 'Find existing customer' : 'Register new customer' }}</p>
          </div>
          <div class="flex gap-2">
            <UButton 
              :color="searchMode ? 'orange' : 'gray'" 
              :variant="searchMode ? 'solid' : 'outline'"
              size="sm"
              @click="searchMode = true"
            >
              Search
            </UButton>
            <UButton 
              :color="!searchMode ? 'orange' : 'gray'" 
              :variant="!searchMode ? 'solid' : 'outline'"
              size="sm"
              @click="searchMode = false"
            >
              New
            </UButton>
          </div>
        </div>
      </template>

      <!-- Search Mode - Autocomplete -->
      <div v-if="searchMode">
        <div class="relative">
          <UInput 
            v-model="searchQuery" 
            placeholder="Type to search by name, email, phone, or Card ID..." 
            icon="i-heroicons-magnifying-glass"
            size="lg"
            @input="debouncedSearch"
          />
          
          <!-- Autocomplete Dropdown -->
          <div v-if="searchResults.length > 0 || searchLoading" class="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
            <div v-if="searchLoading" class="p-4 text-center text-gray-400">
              <UIcon name="i-heroicons-arrow-path" class="w-5 h-5 animate-spin inline mr-2" />
              Searching...
            </div>
            <div 
              v-for="customer in searchResults" 
              :key="customer.id"
              class="p-3 hover:bg-gray-50 cursor-pointer flex items-center gap-3 border-b last:border-0"
              @click="selectCustomer(customer)"
            >
              <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                <UIcon name="i-heroicons-user" class="w-5 h-5 text-orange-600" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-medium truncate">{{ customer.name }}</p>
                <p class="text-sm text-gray-500 truncate">{{ customer.email }} • {{ customer.phone }}</p>
              </div>
              <UBadge color="orange" variant="soft">${{ (customer.current_balance || 0).toFixed(2) }}</UBadge>
            </div>
          </div>
        </div>
        
        <div v-if="searchQuery.length > 2 && searchResults.length === 0 && !searchLoading" class="py-8 text-center text-gray-400">
          No customers found. <UButton variant="link" color="orange" @click="searchMode = false">Create new?</UButton>
        </div>
      </div>

      <!-- New Customer Form -->
      <form v-else @submit.prevent="createCustomer" class="space-y-4">
        <!-- Card ID Capture Section -->
        <div class="border rounded-lg p-4 bg-gray-50">
          <h4 class="font-medium mb-3 flex items-center gap-2">
            <UIcon name="i-heroicons-identification" class="w-5 h-5" />
            Card ID Capture (Optional)
          </h4>

          <!-- Capture Mode Selection -->
          <div class="flex gap-3 mb-4">
            <UButton 
              type="button"
              :color="captureMode === 'upload' ? 'orange' : 'gray'" 
              :variant="captureMode === 'upload' ? 'solid' : 'outline'"
              icon="i-heroicons-arrow-up-tray"
              @click="captureMode = 'upload'; stopCamera()"
            >
              Upload File
            </UButton>
            <UButton 
              type="button"
              :color="captureMode === 'camera' ? 'orange' : 'gray'" 
              :variant="captureMode === 'camera' ? 'solid' : 'outline'"
              icon="i-heroicons-camera"
              @click="startCamera"
            >
              Scan with Camera
            </UButton>
          </div>

          <!-- Upload Mode -->
          <div v-if="captureMode === 'upload' && !cardIdPreview">
            <input 
              ref="fileInput" 
              type="file" 
              accept="image/*" 
              class="hidden"
              @change="handleFileUpload"
            />
            <div 
              class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-orange-400 transition-colors"
              @click="($refs.fileInput as HTMLInputElement)?.click()"
            >
              <UIcon name="i-heroicons-arrow-up-tray" class="w-8 h-8 mx-auto text-gray-400 mb-2" />
              <p class="text-gray-500">Click to upload Card ID image</p>
            </div>
          </div>

          <!-- Camera Mode -->
          <div v-if="captureMode === 'camera' && cameraActive" class="relative">
            <video 
              ref="videoElement" 
              autoplay 
              playsinline
              class="w-full rounded-lg"
            ></video>
            <!-- Card ID Overlay Guide - Ratio 85.6mm x 53.98mm = 1.585:1 -->
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div 
                class="border-4 rounded-lg border-orange-400"
                :style="cardOverlayStyle"
              ></div>
            </div>
            <p class="text-center text-sm mt-2 text-gray-500">
              Align Card ID within the frame (85.6mm × 53.98mm)
            </p>
            <div class="flex justify-center gap-3 mt-3">
              <UButton type="button" color="gray" variant="outline" @click="stopCamera">Cancel</UButton>
              <UButton 
                type="button" 
                color="orange" 
                icon="i-heroicons-camera" 
                @click="captureFromCamera"
                :disabled="!cameraReady"
              >
                Capture
              </UButton>
            </div>
            <canvas ref="canvasElement" class="hidden"></canvas>
          </div>

          <!-- Capture Warning -->
          <UAlert v-if="captureWarning" color="amber" variant="soft" class="mt-3">
            <template #icon>
              <UIcon name="i-heroicons-exclamation-triangle" />
            </template>
            {{ captureWarning }}
          </UAlert>

          <!-- Preview -->
          <div v-if="cardIdPreview" class="space-y-3">
            <div class="relative">
              <img :src="cardIdPreview" alt="Card ID Preview" class="max-h-40 mx-auto rounded-lg" />
              <UButton 
                type="button" 
                size="xs" 
                color="gray" 
                variant="solid"
                icon="i-heroicons-x-mark"
                class="absolute top-1 right-1"
                @click="clearCardId"
              />
            </div>
            <div v-if="ocrLoading" class="text-center text-gray-500">
              <UIcon name="i-heroicons-arrow-path" class="w-4 h-4 animate-spin inline mr-2" />
              Extracting information from Card ID...
            </div>
            <UAlert v-if="ocrSuccess" color="green" variant="soft" class="mt-2">
              <template #icon>
                <UIcon name="i-heroicons-check-circle" />
              </template>
              Successfully extracted {{ extractedCount }} field(s) from Card ID
            </UAlert>
            <!-- Debug: Show raw OCR text -->
            <div v-if="ocrDebugText" class="mt-2 p-2 bg-gray-100 rounded text-xs font-mono max-h-32 overflow-y-auto">
              <p class="font-bold mb-1">OCR Text (Debug):</p>
              {{ ocrDebugText }}
            </div>
          </div>
        </div>

        <!-- Form Fields -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Full Name" required hint="Customer's complete name">
            <UInput v-model="form.name" placeholder="Enter full name" />
          </UFormGroup>
          <UFormGroup label="Card ID Number" hint="16-digit identification number">
            <UInput v-model="form.ktp_number" placeholder="e.g., 3201234567890001" maxlength="16" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Email Address" hint="For receipts and notifications (optional)">
            <UInput v-model="form.email" type="email" placeholder="email@example.com" />
          </UFormGroup>
          <UFormGroup label="Phone Number" required hint="Primary contact number">
            <UInput v-model="form.phone" type="tel" placeholder="+62..." />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Birth Date" hint="Date of birth">
            <UInput v-model="form.birth_date" type="date" />
          </UFormGroup>
          <UFormGroup label="Initial Credit Limit" hint="Starting credit balance">
            <UInput v-model.number="form.credit_limit" type="number" min="0" placeholder="0" />
          </UFormGroup>
        </div>

        <UFormGroup label="Address" hint="Full street address (optional)">
          <UTextarea v-model="form.address" placeholder="Street, City, Postal Code" rows="2" />
        </UFormGroup>

        <UAlert v-if="error" color="red" variant="soft" icon="i-heroicons-exclamation-triangle">
          {{ error }}
        </UAlert>

        <div class="flex gap-3">
          <UButton type="button" color="gray" variant="outline" class="flex-1" @click="isOpen = false">
            Cancel
          </UButton>
          <UButton 
            type="submit" 
            color="orange" 
            class="flex-1" 
            :loading="saving"
            :disabled="!isFormValid"
          >
            <UIcon name="i-heroicons-check" class="mr-1" />
            Create & Link
          </UButton>
        </div>
      </form>
    </UCard>
  </UModal>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved', customer: any): void
}>()

const { $api } = useNuxtApp()

const isOpen = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
})

const searchMode = ref(true)
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const searchLoading = ref(false)

const captureMode = ref<'upload' | 'camera'>('upload')
const cameraActive = ref(false)
const cameraReady = ref(false)
const videoElement = ref<HTMLVideoElement | null>(null)
const canvasElement = ref<HTMLCanvasElement | null>(null)
const mediaStream = ref<MediaStream | null>(null)

const form = reactive({
  name: '',
  email: '',
  phone: '',
  address: '',
  ktp_number: '',
  birth_date: '',
  credit_limit: 0
})

const cardIdFile = ref<File | null>(null)
const cardIdPreview = ref('')
const ocrLoading = ref(false)
const ocrSuccess = ref(false)
const ocrDebugText = ref('')
const extractedCount = ref(0)
const saving = ref(false)
const error = ref('')
const captureWarning = ref('')

// Card overlay style - ratio 85.6mm x 53.98mm = 1.585:1
const cardOverlayStyle = computed(() => ({
  width: '80%',
  aspectRatio: '1.585 / 1'
}))

// Form validation - only name and phone required
const isFormValid = computed(() => {
  return form.name.trim() !== '' && form.phone.trim() !== ''
})

let searchTimeout: any = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  searchTimeout = setTimeout(searchCustomers, 300)
}

const searchCustomers = async () => {
  searchLoading.value = true
  try {
    const res = await $api.get(`/pos/customers/search?q=${encodeURIComponent(searchQuery.value)}`)
    searchResults.value = res.data || []
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    searchLoading.value = false
  }
}

const selectCustomer = (customer: any) => {
  emit('saved', customer)
  isOpen.value = false
  resetForm()
}

// File Upload
const handleFileUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    cardIdFile.value = file
    cardIdPreview.value = URL.createObjectURL(file)
    await processOCR(file)
  }
}

// Camera Functions
const startCamera = async () => {
  captureMode.value = 'camera'
  cameraActive.value = true
  cameraReady.value = false
  captureWarning.value = ''
  
  await nextTick()
  
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: 'environment', 
        width: { ideal: 1920 }, 
        height: { ideal: 1080 }
      }
    })
    mediaStream.value = stream
    if (videoElement.value) {
      videoElement.value.srcObject = stream
      videoElement.value.onloadedmetadata = () => {
        cameraReady.value = true
      }
    }
  } catch (err) {
    console.error('Camera error:', err)
    error.value = 'Could not access camera. Please check permissions.'
    cameraActive.value = false
    captureMode.value = 'upload'
  }
}

const stopCamera = () => {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach((track: MediaStreamTrack) => track.stop())
    mediaStream.value = null
  }
  cameraActive.value = false
  cameraReady.value = false
}

const captureFromCamera = async () => {
  if (!videoElement.value || !canvasElement.value) return
  
  captureWarning.value = ''
  
  const video = videoElement.value
  const canvas = canvasElement.value
  
  // Crop to card area (center 80% with 1.585:1 ratio)
  const cardWidth = video.videoWidth * 0.8
  const cardHeight = cardWidth / 1.585
  const cardX = (video.videoWidth - cardWidth) / 2
  const cardY = (video.videoHeight - cardHeight) / 2
  
  // Set canvas to cropped size
  canvas.width = cardWidth
  canvas.height = cardHeight
  
  const ctx = canvas.getContext('2d')
  if (ctx) {
    // Draw cropped area
    ctx.drawImage(
      video, 
      cardX, cardY, cardWidth, cardHeight,
      0, 0, cardWidth, cardHeight
    )
    
    const dataUrl = canvas.toDataURL('image/jpeg', 0.95)
    cardIdPreview.value = dataUrl
    
    // Convert to blob for upload
    const blob = await fetch(dataUrl).then(r => r.blob())
    cardIdFile.value = new File([blob], 'card_id.jpg', { type: 'image/jpeg' })
    
    stopCamera()
    await processOCR(cardIdFile.value)
  }
}

const clearCardId = () => {
  cardIdFile.value = null
  cardIdPreview.value = ''
  ocrSuccess.value = false
  ocrDebugText.value = ''
  extractedCount.value = 0
  captureWarning.value = ''
}

// OCR Processing
const processOCR = async (file: File) => {
  ocrLoading.value = true
  ocrSuccess.value = false
  ocrDebugText.value = ''
  extractedCount.value = 0
  
  try {
    // Dynamic import Tesseract.js
    const { createWorker } = await import('tesseract.js')
    
    // Create worker with Indonesian + English
    const worker = await createWorker('ind+eng')
    
    const { data: { text } } = await worker.recognize(file)
    await worker.terminate()
    
    console.log('OCR Raw Text:', text) // Debug
    ocrDebugText.value = text // Show in UI for debugging
    
    // Parse OCR results
    const count = parseCardIdText(text)
    extractedCount.value = count
    ocrSuccess.value = count > 0
    
    if (count === 0) {
      captureWarning.value = 'Could not extract data. Try capturing with better lighting or enter details manually.'
    }
  } catch (err) {
    console.error('OCR error:', err)
    captureWarning.value = 'OCR processing failed. Please enter details manually.'
  } finally {
    ocrLoading.value = false
  }
}

const parseCardIdText = (text: string): number => {
  let count = 0
  
  // Clean up text - remove extra whitespace
  const cleanText = text.replace(/\s+/g, ' ').trim()
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0)
  
  console.log('OCR Lines:', lines)
  
  // === NIK (16-digit ID number) ===
  // Look for sequences of 16 digits
  const nikPatterns = [
    /NIK\s*[:\s]*(\d[\d\s]{15,20})/i,
    /(\d{16})/,
    /(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})/
  ]
  
  for (const pattern of nikPatterns) {
    const match = cleanText.match(pattern)
    if (match) {
      const nik = match[1].replace(/\s/g, '')
      if (nik.length === 16 && /^\d+$/.test(nik)) {
        form.ktp_number = nik
        count++
        console.log('Found NIK:', nik)
        break
      }
    }
  }
  
  // === NAME ===
  // Look for "Nama" label followed by name
  const namaPatterns = [
    /[Nn][Aa][Mm][Aa]\s*[:\s]+([A-Z][A-Z\s'.,-]+)/,
    /^([A-Z][A-Z\s'.,-]{4,40})$/m
  ]
  
  for (const pattern of namaPatterns) {
    const match = text.match(pattern)
    if (match && !form.name) {
      let name = match[1].trim()
      // Clean up - remove trailing/leading garbage
      name = name.replace(/[^A-Z\s'.,-]/gi, '').trim()
      // Filter out non-name text
      const excludeWords = ['NIK', 'PROVINSI', 'KABUPATEN', 'KOTA', 'KECAMATAN', 'KELURAHAN', 'DESA', 'WARGA', 'STATUS', 'AGAMA', 'PEKERJAAN']
      const isExcluded = excludeWords.some(w => name.toUpperCase().includes(w))
      
      if (name.length >= 3 && name.length <= 50 && !isExcluded) {
        form.name = name
        count++
        console.log('Found Name:', name)
        break
      }
    }
  }
  
  // === BIRTH DATE ===
  // Indonesian KTP format: DD-MM-YYYY or Tempat/Tgl Lahir: City, DD-MM-YYYY
  const datePatterns = [
    /[Ll]ahir\s*[:\s]*[A-Za-z,\s]*(\d{2})[-\/\.](\d{2})[-\/\.](\d{4})/,
    /(\d{2})[-\/\.](\d{2})[-\/\.](\d{4})/,
    /(\d{2})\s*[-\/\.]\s*(\d{2})\s*[-\/\.]\s*(\d{4})/
  ]
  
  for (const pattern of datePatterns) {
    const match = text.match(pattern)
    if (match && !form.birth_date) {
      const [, day, month, year] = match
      const d = parseInt(day)
      const m = parseInt(month)
      const y = parseInt(year)
      
      // Validate date
      if (d >= 1 && d <= 31 && m >= 1 && m <= 12 && y >= 1920 && y <= 2010) {
        form.birth_date = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
        count++
        console.log('Found Birth Date:', form.birth_date)
        break
      }
    }
  }
  
  return count
}

const createCustomer = async () => {
  error.value = ''
  
  if (!isFormValid.value) {
    error.value = 'Name and Phone are required'
    return
  }

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('name', form.name)
    formData.append('email', form.email || '')
    formData.append('phone', form.phone)
    if (form.address) formData.append('address', form.address)
    if (form.ktp_number) formData.append('ktp_number', form.ktp_number)
    if (form.birth_date) formData.append('birth_date', form.birth_date)
    formData.append('credit_limit', form.credit_limit.toString())
    if (cardIdFile.value) formData.append('ktp_image', cardIdFile.value)

    const res = await $api.post('/pos/customer', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    emit('saved', res.data)
    isOpen.value = false
    resetForm()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to create customer'
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  form.name = ''
  form.email = ''
  form.phone = ''
  form.address = ''
  form.ktp_number = ''
  form.birth_date = ''
  form.credit_limit = 0
  cardIdFile.value = null
  cardIdPreview.value = ''
  searchQuery.value = ''
  searchResults.value = []
  captureMode.value = 'upload'
  ocrSuccess.value = false
  ocrDebugText.value = ''
  extractedCount.value = 0
  captureWarning.value = ''
  stopCamera()
}

// Cleanup on unmount
onUnmounted(() => {
  stopCamera()
})
</script>
