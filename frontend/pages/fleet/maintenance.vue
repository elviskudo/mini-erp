<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold">Vehicle Maintenance</h2>
        <p class="text-small text-gray-500">Track service and repair history</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }" :disabled="logs.length === 0">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" :disabled="logs.length === 0">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="sm" @click="fetchLogs">Refresh</UButton>
        <UButton icon="i-heroicons-building-storefront" variant="outline" size="sm" @click="showVendorModal = true">Vendors</UButton>
        <UButton icon="i-heroicons-plus" size="sm" @click="openCreate">Add Maintenance</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Total Records</p>
        <p class="text-xl font-bold">{{ logs.length }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Total Cost</p>
        <p class="text-xl font-bold text-primary-500">{{ formatCurrency(totalCost) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">This Month</p>
        <p class="text-xl font-bold text-blue-500">{{ formatCurrency(thisMonthCost) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Overdue Services</p>
        <p class="text-xl font-bold" :class="overdueCount > 0 ? 'text-red-500' : 'text-green-500'">{{ overdueCount }}</p>
      </UCard>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="logs" :loading="loading" searchable :search-keys="['description', 'service_type']" empty-message="No maintenance records yet.">
        <template #vehicle_id-data="{ row }">
          <p class="text-xs font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #date-data="{ row }">
          <div>
            <p class="text-xs">{{ formatDate(row.date) }}</p>
            <p class="text-[10px] text-gray-400">{{ row.odometer?.toLocaleString() }} km</p>
          </div>
        </template>
        <template #service_type-data="{ row }">
          <div>
            <UBadge :color="getServiceColor(row.service_type)" variant="subtle" size="xs">{{ row.service_type }}</UBadge>
            <p class="text-[10px] text-gray-400 mt-0.5 truncate max-w-40">{{ row.description }}</p>
          </div>
        </template>
        <template #vendor_id-data="{ row }">
          <p class="text-xs">{{ getVendorName(row.vendor_id) }}</p>
        </template>
        <template #total_cost-data="{ row }">
          <p class="text-xs font-medium">{{ formatCurrency(row.total_cost) }}</p>
        </template>
        <template #next_service_date-data="{ row }">
          <UBadge v-if="row.next_service_date" :color="isOverdue(row.next_service_date) ? 'red' : 'gray'" size="xs">
            {{ formatDate(row.next_service_date) }}
          </UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="2xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="2xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteLog(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingLog ? 'Edit Maintenance' : 'Add Maintenance'" :loading="saving" @submit="saveLog" size="lg">
      <div class="space-y-3">
        <UFormGroup label="Vehicle" required :ui="{ hint: 'text-small' }" hint="Select vehicle being serviced">
          <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." size="sm" />
        </UFormGroup>

        <UFormGroup label="Vendor/Workshop" required :ui="{ hint: 'text-small' }" hint="Service provider">
          <USelect v-model="form.vendor_id" :options="vendorOptions" placeholder="Select vendor..." size="sm" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Date" required :ui="{ hint: 'text-small' }" hint="Service date">
            <UInput v-model="form.date" type="date" size="sm" />
          </UFormGroup>
          <UFormGroup label="Odometer (km)" required :ui="{ hint: 'text-small' }" hint="Current km">
            <UInput v-model.number="form.odometer" type="number" placeholder="45000" size="sm" />
          </UFormGroup>
        </div>

        <UFormGroup label="Service Type" required :ui="{ hint: 'text-small' }" hint="Type of work">
          <USelect v-model="form.service_type" :options="serviceTypeOptions" size="sm" />
        </UFormGroup>

        <UFormGroup label="Description" required :ui="{ hint: 'text-small' }" hint="What was done">
          <UTextarea v-model="form.description" :rows="2" placeholder="Describe work..." />
        </UFormGroup>

        <UDivider label="Invoice Upload" />

        <UFormGroup label="Invoice/Receipt" required :ui="{ hint: 'text-small' }" hint="Take photo or upload invoice (auto-extracts data)">
          <div class="space-y-2">
            <!-- Camera & Upload Buttons -->
            <div class="flex gap-2">
              <UButton icon="i-heroicons-camera" color="primary" class="flex-1" @click="openCamera">
                📷 Take Photo
              </UButton>
              <UButton icon="i-heroicons-folder-open" variant="outline" class="flex-1" @click="triggerFileUpload">
                📁 Browse File
              </UButton>
            </div>
            <input ref="fileInput" type="file" class="hidden" accept="image/*,.pdf" @change="handleFileSelect" />
            
            <!-- Camera Modal -->
            <div v-if="showCamera" class="fixed inset-0 bg-black z-50 flex flex-col">
              <div class="flex justify-between items-center p-4 text-white">
                <span>Take Invoice Photo</span>
                <UButton icon="i-heroicons-x-mark" color="white" variant="ghost" @click="closeCamera" />
              </div>
              <video ref="videoRef" autoplay playsinline class="flex-1 object-cover"></video>
              <div class="p-4 flex justify-center">
                <UButton icon="i-heroicons-camera" size="xl" class="rounded-full w-16 h-16" @click="capturePhoto" />
              </div>
            </div>
            <canvas ref="canvasRef" class="hidden"></canvas>
            
            <!-- Dropzone -->
            <div 
              class="border-2 border-dashed rounded-lg p-3 text-center cursor-pointer hover:border-primary-500 transition-colors"
              :class="{ 
                'border-green-500 bg-green-50': form.receipt_url && !extractionError,
                'border-red-500 bg-red-50': extractionError
              }"
              @click="triggerFileUpload"
              @drop.prevent="handleFileDrop"
              @dragover.prevent
            >
              <div v-if="uploading || extracting" class="flex items-center justify-center gap-2 py-2">
                <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
                <span class="text-xs">{{ extracting ? 'Extracting invoice data...' : 'Uploading...' }}</span>
              </div>
              <div v-else-if="form.receipt_url && !extractionError" class="space-y-1">
                <UIcon name="i-heroicons-check-circle" class="text-green-500 text-xl" />
                <p class="text-xs text-green-600">Invoice uploaded!</p>
                <img v-if="isImageUrl(form.receipt_url)" :src="form.receipt_url" class="max-h-20 mx-auto rounded" />
              </div>
              <div v-else-if="extractionError" class="space-y-1">
                <UIcon name="i-heroicons-x-circle" class="text-red-500 text-xl" />
                <p class="text-xs text-red-600">{{ extractionError }}</p>
                <p class="text-[10px] text-gray-500">Click to try again</p>
              </div>
              <div v-else class="py-2">
                <UIcon name="i-heroicons-cloud-arrow-up" class="text-2xl text-gray-400" />
                <p class="text-xs text-gray-500 mt-1">Or drag & drop invoice here</p>
              </div>
            </div>
            <UInput v-model="form.receipt_url" placeholder="Or paste URL" size="xs" />
          </div>
        </UFormGroup>

        <!-- Extracted Invoice Data Table -->
        <div v-if="extractedData && Object.keys(extractedData).length > 0" class="border rounded-lg p-3 bg-blue-50">
          <p class="text-xs font-semibold mb-2 text-blue-700">📋 Extracted Invoice Data</p>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div v-if="extractedData.invoice_number">
              <span class="text-gray-500">Invoice #:</span> <span class="font-medium">{{ extractedData.invoice_number }}</span>
            </div>
            <div v-if="extractedData.vendor_name">
              <span class="text-gray-500">Vendor:</span> <span class="font-medium">{{ extractedData.vendor_name }}</span>
            </div>
            <div v-if="extractedData.date">
              <span class="text-gray-500">Date:</span> <span class="font-medium">{{ extractedData.date }}</span>
            </div>
            <div v-if="extractedData.total">
              <span class="text-gray-500">Total:</span> <span class="font-medium text-green-600">{{ formatCurrency(extractedData.total) }}</span>
            </div>
          </div>
          <UButton size="xs" variant="soft" color="blue" class="mt-2" @click="applyExtractedData">
            Apply to Form
          </UButton>
        </div>

        <UDivider label="Costs" />

        <div class="grid grid-cols-3 gap-3">
          <UFormGroup label="Parts (Rp)" :ui="{ hint: 'text-small' }" hint="Parts cost">
            <UInput v-model.number="form.parts_cost" type="number" placeholder="0" size="sm" />
          </UFormGroup>
          <UFormGroup label="Labor (Rp)" :ui="{ hint: 'text-small' }" hint="Labor cost">
            <UInput v-model.number="form.labor_cost" type="number" placeholder="0" size="sm" />
          </UFormGroup>
          <UFormGroup label="Total (Rp)" :ui="{ hint: 'text-small' }" hint="Auto-calc">
            <UInput :model-value="(form.parts_cost || 0) + (form.labor_cost || 0)" disabled size="sm" class="bg-gray-50" />
          </UFormGroup>
        </div>

        <UDivider label="Next Service" />

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Next Service Date" required :ui="{ hint: 'text-small' }" hint="Recommended date">
            <UInput v-model="form.next_service_date" type="date" size="sm" />
          </UFormGroup>
          <UFormGroup label="Next Service km" :ui="{ hint: 'text-small' }" hint="Recommended km">
            <UInput v-model.number="form.next_service_odometer" type="number" placeholder="50000" size="sm" />
          </UFormGroup>
        </div>

        <UFormGroup label="Performed By" :ui="{ hint: 'text-small' }" hint="Mechanic name">
          <UInput v-model="form.performed_by" placeholder="Mechanic" size="sm" />
        </UFormGroup>

        <UFormGroup label="Invoice Number" :ui="{ hint: 'text-small' }" hint="Invoice/work order #">
          <UInput v-model="form.invoice_number" placeholder="INV-123456" size="sm" />
        </UFormGroup>

        <UFormGroup label="Notes" :ui="{ hint: 'text-small' }" hint="Additional notes">
          <UTextarea v-model="form.notes" :rows="2" />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Vendor Modal -->
    <UModal v-model="showVendorModal" :ui="{ width: 'sm:max-w-xl' }">
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold">Vendor Management</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" size="xs" @click="showVendorModal = false" />
          </div>
        </template>
        <div class="space-y-3">
          <div class="grid grid-cols-5 gap-2">
            <UInput v-model="newVendor.name" placeholder="Vendor Name *" size="xs" class="col-span-2" />
            <UInput v-model="newVendor.phone" placeholder="Phone" size="xs" />
            <UInput v-model="newVendor.city" placeholder="City" size="xs" />
            <UButton icon="i-heroicons-plus" size="xs" @click="addVendor" />
          </div>
          <div class="divide-y max-h-48 overflow-y-auto">
            <div v-for="vendor in vendors" :key="vendor.id" class="py-2 flex items-center justify-between">
              <div>
                <p class="text-xs font-medium">{{ vendor.code }} - {{ vendor.name }}</p>
                <p class="text-[10px] text-gray-400">{{ vendor.city || '—' }} | {{ vendor.phone || '—' }}</p>
              </div>
              <UButton icon="i-heroicons-trash" size="2xs" variant="ghost" color="red" @click="deleteVendor(vendor)" />
            </div>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import Tesseract from 'tesseract.js'

const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const uploading = ref(false)
const extracting = ref(false)
const extractionError = ref('')
const isSlideoverOpen = ref(false)
const editingLog = ref<any>(null)
const logs = ref<any[]>([])
const vehicles = ref<any[]>([])
const vendors = ref<any[]>([])
const showVendorModal = ref(false)
const newVendor = reactive({ name: '', phone: '', city: '' })
const fileInput = ref<HTMLInputElement | null>(null)
const extractedData = ref<any>(null)

// Camera refs
const showCamera = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let mediaStream: MediaStream | null = null

const columns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'date', label: 'Date' },
  { key: 'service_type', label: 'Service' },
  { key: 'vendor_id', label: 'Vendor' },
  { key: 'total_cost', label: 'Cost' },
  { key: 'next_service_date', label: 'Next Service' },
  { key: 'actions', label: '' }
]

const serviceTypeOptions = [
  { label: 'Routine Service', value: 'Routine' },
  { label: 'Oil Change', value: 'Oil Change' },
  { label: 'Tire Change', value: 'Tire' },
  { label: 'Brake Service', value: 'Brake' },
  { label: 'Engine Repair', value: 'Engine' },
  { label: 'Body Repair', value: 'Body' },
  { label: 'Electrical', value: 'Electrical' },
  { label: 'AC Service', value: 'AC' },
  { label: 'Inspection', value: 'Inspection' },
  { label: 'Other', value: 'Other' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const vendorOptions = computed(() => 
  vendors.value.map((v: any) => ({ label: `${v.code} - ${v.name}`, value: v.id }))
)

const totalCost = computed(() => logs.value.reduce((sum, l) => sum + (l.total_cost || 0), 0))
const thisMonthCost = computed(() => {
  const now = new Date()
  return logs.value
    .filter(l => { const d = new Date(l.date); return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear() })
    .reduce((sum, l) => sum + (l.total_cost || 0), 0)
})
const overdueCount = computed(() => logs.value.filter(l => l.next_service_date && new Date(l.next_service_date) < new Date()).length)

const form = reactive({
  vehicle_id: '',
  vendor_id: '',
  date: '',
  odometer: 0,
  service_type: 'Routine',
  description: '',
  lat: null as number | null,
  lng: null as number | null,
  parts_cost: 0,
  labor_cost: 0,
  next_service_date: '',
  next_service_odometer: null as number | null,
  performed_by: '',
  invoice_number: '',
  receipt_url: '',
  notes: ''
})

// ========== FETCH ==========
const fetchLogs = async () => {
  loading.value = true
  try { logs.value = (await $api.get('/fleet/maintenance')).data } catch (e) { console.error(e) }
  finally { loading.value = false }
}
const fetchVehicles = async () => { try { vehicles.value = (await $api.get('/fleet/vehicles')).data } catch (e) { console.error(e) } }
const fetchVendors = async () => { try { vendors.value = (await $api.get('/fleet/vendors')).data } catch (e) { console.error(e) } }

// ========== HELPERS ==========
const getVehicleName = (id: string) => vehicles.value.find((v: any) => v.id === id)?.plate_number || '-'
const getVendorName = (id: string) => vendors.value.find((v: any) => v.id === id)?.name || '-'
const isImageUrl = (url: string) => /\.(jpg|jpeg|png|gif|webp)$/i.test(url)
const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'
const isOverdue = (d: string) => new Date(d) < new Date()

const getServiceColor = (type: string) => {
  const colors: Record<string, string> = { Routine: 'blue', 'Oil Change': 'yellow', Tire: 'gray', Brake: 'red', Engine: 'orange', Body: 'purple', Electrical: 'cyan', AC: 'teal' }
  return colors[type] || 'gray'
}

// ========== EXPORT ==========
const exportData = (format: string) => {
  const data = logs.value.map((l: any) => ({
    'Vehicle': getVehicleName(l.vehicle_id),
    'Date': formatDate(l.date),
    'Odometer': l.odometer || '',
    'Service Type': l.service_type,
    'Vendor': getVendorName(l.vendor_id),
    'Parts Cost': l.parts_cost || 0,
    'Labor Cost': l.labor_cost || 0,
    'Total Cost': l.total_cost || 0,
    'Next Service': formatDate(l.next_service_date),
    'Description': l.description || ''
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `maintenance_logs.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Maintenance logs exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Maintenance Logs</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Vehicle Maintenance Report</h1>
        <p>Exported: ${new Date().toLocaleDateString()}</p>
        <table><tr>${Object.keys(data[0] || {}).map(h => `<th>${h}</th>`).join('')}</tr>
        ${data.map((row: any) => `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}
        </table></body></html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }
}

// ========== CRUD ==========
const openCreate = () => {
  editingLog.value = null
  extractedData.value = null
  extractionError.value = ''
  const today = new Date().toISOString().slice(0, 10)
  const nextMonth = new Date(Date.now() + 30*24*60*60*1000).toISOString().slice(0, 10)
  Object.assign(form, {
    vehicle_id: '', vendor_id: '', date: today, odometer: 0, service_type: 'Routine', description: '',
    lat: null, lng: null, parts_cost: 0, labor_cost: 0, next_service_date: nextMonth, next_service_odometer: null,
    performed_by: '', invoice_number: '', receipt_url: '', notes: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (log: any) => {
  editingLog.value = log
  extractedData.value = null
  extractionError.value = ''
  Object.assign(form, {
    vehicle_id: log.vehicle_id, vendor_id: log.vendor_id, date: log.date, odometer: log.odometer,
    service_type: log.service_type, description: log.description, lat: log.lat, lng: log.lng,
    parts_cost: log.parts_cost, labor_cost: log.labor_cost, next_service_date: log.next_service_date,
    next_service_odometer: log.next_service_odometer, performed_by: log.performed_by || '',
    invoice_number: log.invoice_number || '', receipt_url: log.receipt_url || '', notes: log.notes || ''
  })
  isSlideoverOpen.value = true
}

const saveLog = async () => {
  if (!form.vehicle_id || !form.vendor_id || !form.odometer || !form.description || !form.next_service_date) {
    toast.add({ title: 'Please fill all required fields', color: 'red' }); return
  }
  if (!form.receipt_url) {
    toast.add({ title: 'Invoice upload is required', color: 'red' }); return
  }
  
  saving.value = true
  try {
    const payload = { ...form, total_cost: (form.parts_cost || 0) + (form.labor_cost || 0) }
    if (editingLog.value) {
      await $api.put(`/fleet/maintenance/${editingLog.value.id}`, payload)
      toast.add({ title: 'Maintenance record updated!' })
    } else {
      await $api.post('/fleet/maintenance', payload)
      toast.add({ title: 'Maintenance record added!' })
    }
    isSlideoverOpen.value = false
    fetchLogs()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally { saving.value = false }
}

const deleteLog = async (log: any) => {
  if (!confirm('Delete this maintenance record?')) return
  try { await $api.delete(`/fleet/maintenance/${log.id}`); toast.add({ title: 'Deleted!' }); fetchLogs() }
  catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

// ========== CAMERA ==========
const openCamera = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ 
      video: { facingMode: 'environment' } 
    })
    showCamera.value = true
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
    }
  } catch (e) {
    console.error('Camera error:', e)
    toast.add({ title: 'Camera access denied', description: 'Please allow camera access or use file upload', color: 'red' })
  }
}

const closeCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  showCamera.value = false
}

const capturePhoto = async () => {
  if (!videoRef.value || !canvasRef.value) return
  
  const video = videoRef.value
  const canvas = canvasRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(video, 0, 0)
    canvas.toBlob(async (blob) => {
      if (blob) {
        closeCamera()
        const file = new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' })
        await processFile(file)
      }
    }, 'image/jpeg', 0.9)
  }
}

// ========== FILE UPLOAD & OCR ==========
const triggerFileUpload = () => fileInput.value?.click()

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) await processFile(target.files[0])
}

const handleFileDrop = async (event: DragEvent) => {
  const file = event.dataTransfer?.files?.[0]
  if (file) await processFile(file)
}

const processFile = async (file: File) => {
  extractionError.value = ''
  extractedData.value = null
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await $api.post('/upload/media', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    form.receipt_url = res.data.url
    toast.add({ title: 'File uploaded!' })
  } catch (e: any) {
    extractionError.value = 'Upload failed'
    uploading.value = false
    return
  }
  uploading.value = false
  
  extracting.value = true
  try {
    const result = await Tesseract.recognize(file, 'eng+ind', { logger: (m: any) => console.log(m) })
    const text = result.data.text
    
    const invoiceKeywords = ['invoice', 'faktur', 'nota', 'receipt', 'kwitansi', 'total', 'subtotal', 'rp', 'idr', 'amount']
    const hasInvoiceKeywords = invoiceKeywords.some(kw => text.toLowerCase().includes(kw))
    
    if (!hasInvoiceKeywords) {
      extractionError.value = 'Document does not appear to be an invoice.'
      form.receipt_url = ''
      extracting.value = false
      return
    }
    
    extractedData.value = parseInvoiceText(text)
    toast.add({ title: 'Invoice data extracted!', color: 'green' })
  } catch (e) {
    console.error('OCR Error:', e)
    extractionError.value = 'Failed to extract text'
  }
  extracting.value = false
}

const parseInvoiceText = (text: string) => {
  const data: any = { raw_text: text }
  const invMatch = text.match(/(?:invoice|inv|no|faktur|nota)[^\d]*(\d+[\w-]*)/i)
  if (invMatch) data.invoice_number = invMatch[1]
  const dateMatch = text.match(/(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i)
  if (dateMatch) data.date = dateMatch[1]
  const amountPatterns = [/total[:\s]*(?:rp\.?|idr)?[\s]*([\d.,]+)/i, /(?:rp\.?|idr)[\s]*([\d.,]+)/gi]
  for (const pattern of amountPatterns) {
    const match = text.match(pattern)
    if (match) {
      const amount = parseFloat(match[1].replace(/\./g, '').replace(',', '.'))
      if (!isNaN(amount) && amount > 0) { data.total = amount; break }
    }
  }
  const lines = text.split('\n').filter(l => l.trim())
  if (lines.length > 0 && lines[0].trim().length > 3 && lines[0].trim().length < 50) data.vendor_name = lines[0].trim()
  return data
}

const applyExtractedData = () => {
  if (extractedData.value) {
    if (extractedData.value.invoice_number) form.invoice_number = extractedData.value.invoice_number
    if (extractedData.value.total) { form.parts_cost = extractedData.value.total; form.labor_cost = 0 }
    toast.add({ title: 'Data applied to form!' })
  }
}

// ========== VENDOR CRUD ==========
const addVendor = async () => {
  if (!newVendor.name) { toast.add({ title: 'Vendor name required', color: 'red' }); return }
  try {
    await $api.post('/fleet/vendors', newVendor)
    toast.add({ title: 'Vendor added!' })
    Object.assign(newVendor, { name: '', phone: '', city: '' })
    fetchVendors()
  } catch (e: any) { toast.add({ title: 'Error', description: e.response?.data?.detail, color: 'red' }) }
}

const deleteVendor = async (vendor: any) => {
  if (!confirm(`Delete "${vendor.name}"?`)) return
  try { await $api.delete(`/fleet/vendors/${vendor.id}`); toast.add({ title: 'Deleted!' }); fetchVendors() }
  catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

onMounted(() => { fetchLogs(); fetchVehicles(); fetchVendors() })
</script>
