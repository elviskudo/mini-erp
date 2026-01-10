<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold">Vehicle Expenses</h2>
        <p class="text-small text-gray-500">Track operational costs and miscellaneous expenses</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }" :disabled="expenses.length === 0">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" :disabled="expenses.length === 0">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="sm" @click="fetchExpenses">Refresh</UButton>
        <UButton icon="i-heroicons-plus" size="sm" @click="openCreate">Add Expense</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Total Expenses</p>
        <p class="text-xl font-bold">{{ formatCurrency(totalExpenses) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">This Month</p>
        <p class="text-xl font-bold text-blue-500">{{ formatCurrency(thisMonthExpenses) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Toll/Parking</p>
        <p class="text-xl font-bold text-orange-500">{{ formatCurrency(tollParkingExpenses) }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Other Expenses</p>
        <p class="text-xl font-bold text-purple-500">{{ formatCurrency(otherExpenses) }}</p>
      </UCard>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="expenses" :loading="loading" searchable :search-keys="['description']" empty-message="No expenses yet.">
        <template #vehicle_id-data="{ row }">
          <p class="text-xs font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #date-data="{ row }">
          <p class="text-xs">{{ formatDate(row.date) }}</p>
        </template>
        <template #category-data="{ row }">
          <UBadge :color="getCategoryColor(row.category)" variant="subtle" size="xs">{{ row.category }}</UBadge>
        </template>
        <template #description-data="{ row }">
          <p class="text-xs truncate max-w-40">{{ row.description }}</p>
        </template>
        <template #amount-data="{ row }">
          <p class="text-xs font-medium">{{ formatCurrency(row.amount) }}</p>
        </template>
        <template #receipt_url-data="{ row }">
          <UButton v-if="row.receipt_url" icon="i-heroicons-document" size="2xs" variant="ghost" :to="row.receipt_url" target="_blank" />
          <span v-else class="text-[10px] text-gray-400">—</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="2xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="2xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteExpense(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingExpense ? 'Edit Expense' : 'Add Expense'" :loading="saving" @submit="saveExpense" size="lg">
      <div class="space-y-3">
        <UFormGroup label="Vehicle" required :ui="{ hint: 'text-small' }" hint="Vehicle for this expense">
          <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." size="sm" />
        </UFormGroup>

        <UFormGroup label="Date" required :ui="{ hint: 'text-small' }" hint="Expense date">
          <UInput v-model="form.date" type="date" size="sm" />
        </UFormGroup>

        <UFormGroup label="Category" required :ui="{ hint: 'text-small' }" hint="Type of expense">
          <USelect v-model="form.category" :options="categoryOptions" size="sm" />
        </UFormGroup>

        <UFormGroup label="Description" required :ui="{ hint: 'text-small' }" hint="Brief description">
          <UInput v-model="form.description" placeholder="e.g. Toll Jakarta-Bandung" size="sm" />
        </UFormGroup>

        <UFormGroup label="Amount (Rp)" required :ui="{ hint: 'text-small' }" hint="Total amount">
          <UInput v-model.number="form.amount" type="number" placeholder="150000" size="sm" />
        </UFormGroup>

        <UFormGroup label="Linked Booking" :ui="{ hint: 'text-small' }" hint="Link to booking (optional)">
          <USelect v-model="form.booking_id" :options="bookingOptions" placeholder="Select booking..." size="sm" />
        </UFormGroup>

        <UDivider label="Receipt Upload" />

        <UFormGroup label="Receipt/Invoice" required :ui="{ hint: 'text-small' }" hint="Take photo or upload receipt (auto-extracts data)">
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
                <span>Take Receipt Photo</span>
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
                <span class="text-xs">{{ extracting ? 'Extracting data...' : 'Uploading...' }}</span>
              </div>
              <div v-else-if="form.receipt_url && !extractionError" class="space-y-1">
                <UIcon name="i-heroicons-check-circle" class="text-green-500 text-xl" />
                <p class="text-xs text-green-600">Receipt uploaded!</p>
                <img v-if="isImageUrl(form.receipt_url)" :src="form.receipt_url" class="max-h-20 mx-auto rounded" />
              </div>
              <div v-else-if="extractionError" class="space-y-1">
                <UIcon name="i-heroicons-x-circle" class="text-red-500 text-xl" />
                <p class="text-xs text-red-600">{{ extractionError }}</p>
                <p class="text-[10px] text-gray-500">Click to try again</p>
              </div>
              <div v-else class="py-2">
                <UIcon name="i-heroicons-cloud-arrow-up" class="text-2xl text-gray-400" />
                <p class="text-xs text-gray-500 mt-1">Or drag & drop receipt here</p>
              </div>
            </div>
            <UInput v-model="form.receipt_url" placeholder="Or paste URL" size="xs" />
          </div>
        </UFormGroup>

        <!-- Extracted Invoice Data Table -->
        <div v-if="extractedData && Object.keys(extractedData).length > 0" class="border rounded-lg p-3 bg-blue-50">
          <p class="text-xs font-semibold mb-2 text-blue-700">📋 Extracted Receipt Data</p>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div v-if="extractedData.invoice_number">
              <span class="text-gray-500">Receipt #:</span> <span class="font-medium">{{ extractedData.invoice_number }}</span>
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

        <UFormGroup label="Notes" :ui="{ hint: 'text-small' }" hint="Additional notes">
          <UTextarea v-model="form.notes" :rows="2" />
        </UFormGroup>
      </div>
    </FormSlideover>
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
const editingExpense = ref<any>(null)
const expenses = ref<any[]>([])
const vehicles = ref<any[]>([])
const bookings = ref<any[]>([])
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
  { key: 'category', label: 'Category' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' },
  { key: 'receipt_url', label: 'Receipt' },
  { key: 'actions', label: '' }
]

const categoryOptions = [
  { label: 'Fuel', value: 'FUEL' },
  { label: 'Toll', value: 'TOLL' },
  { label: 'Parking', value: 'PARKING' },
  { label: 'Service', value: 'SERVICE' },
  { label: 'Tax', value: 'TAX' },
  { label: 'Insurance', value: 'INSURANCE' },
  { label: 'KIR', value: 'KIR' },
  { label: 'Other', value: 'OTHER' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const bookingOptions = computed(() => [
  { label: 'None', value: '' },
  ...bookings.value.map((b: any) => ({ label: `${b.code} - ${b.destination}`, value: b.id }))
])

const totalExpenses = computed(() => expenses.value.reduce((sum, e) => sum + (e.amount || 0), 0))
const thisMonthExpenses = computed(() => {
  const now = new Date()
  return expenses.value
    .filter(e => { const d = new Date(e.date); return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear() })
    .reduce((sum, e) => sum + (e.amount || 0), 0)
})
const tollParkingExpenses = computed(() => expenses.value.filter(e => ['TOLL', 'PARKING'].includes(e.category)).reduce((sum, e) => sum + (e.amount || 0), 0))
const otherExpenses = computed(() => expenses.value.filter(e => !['FUEL', 'TOLL', 'PARKING'].includes(e.category)).reduce((sum, e) => sum + (e.amount || 0), 0))

const form = reactive({
  vehicle_id: '',
  date: '',
  category: 'OTHER',
  description: '',
  amount: 0,
  booking_id: '',
  receipt_url: '',
  notes: ''
})

// ========== FETCH ==========
const fetchExpenses = async () => {
  loading.value = true
  try { expenses.value = (await $api.get('/fleet/expenses')).data } catch (e) { console.error(e) }
  finally { loading.value = false }
}
const fetchVehicles = async () => { try { vehicles.value = (await $api.get('/fleet/vehicles')).data } catch (e) { console.error(e) } }
const fetchBookings = async () => { try { bookings.value = (await $api.get('/fleet/bookings')).data } catch (e) { console.error(e) } }

// ========== HELPERS ==========
const getVehicleName = (id: string) => vehicles.value.find((v: any) => v.id === id)?.plate_number || '-'
const isImageUrl = (url: string) => /\.(jpg|jpeg|png|gif|webp)$/i.test(url)
const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'

const getCategoryColor = (cat: string) => {
  const colors: Record<string, string> = { FUEL: 'blue', TOLL: 'green', PARKING: 'yellow', SERVICE: 'purple', TAX: 'red', INSURANCE: 'cyan', KIR: 'orange' }
  return colors[cat] || 'gray'
}

// ========== EXPORT ==========
const exportData = (format: string) => {
  const data = expenses.value.map((e: any) => ({
    'Vehicle': getVehicleName(e.vehicle_id),
    'Date': formatDate(e.date),
    'Category': e.category,
    'Description': e.description || '',
    'Amount': e.amount || 0,
    'Notes': e.notes || ''
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `expenses.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Expenses exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Vehicle Expenses</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Vehicle Expenses Report</h1>
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
  editingExpense.value = null
  extractedData.value = null
  extractionError.value = ''
  Object.assign(form, {
    vehicle_id: '', date: new Date().toISOString().slice(0, 10), category: 'OTHER',
    description: '', amount: 0, booking_id: '', receipt_url: '', notes: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (expense: any) => {
  editingExpense.value = expense
  extractedData.value = null
  extractionError.value = ''
  Object.assign(form, {
    vehicle_id: expense.vehicle_id, date: expense.date, category: expense.category,
    description: expense.description, amount: expense.amount, booking_id: expense.booking_id || '',
    receipt_url: expense.receipt_url || '', notes: expense.notes || ''
  })
  isSlideoverOpen.value = true
}

const saveExpense = async () => {
  if (!form.vehicle_id || !form.description || !form.amount) {
    toast.add({ title: 'Please fill all required fields', color: 'red' }); return
  }
  if (!form.receipt_url) {
    toast.add({ title: 'Receipt upload is required', color: 'red' }); return
  }
  
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.booking_id) delete payload.booking_id
    
    if (editingExpense.value) {
      await $api.put(`/fleet/expenses/${editingExpense.value.id}`, payload)
      toast.add({ title: 'Expense updated!' })
    } else {
      await $api.post('/fleet/expenses', payload)
      toast.add({ title: 'Expense added!' })
    }
    isSlideoverOpen.value = false
    fetchExpenses()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally { saving.value = false }
}

const deleteExpense = async (expense: any) => {
  if (!confirm(`Delete "${expense.description}"?`)) return
  try { await $api.delete(`/fleet/expenses/${expense.id}`); toast.add({ title: 'Deleted!' }); fetchExpenses() }
  catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

// ========== CAMERA ==========
const openCamera = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    showCamera.value = true
    await nextTick()
    if (videoRef.value) videoRef.value.srcObject = mediaStream
  } catch (e) {
    console.error('Camera error:', e)
    toast.add({ title: 'Camera access denied', description: 'Please allow camera access or use file upload', color: 'red' })
  }
}

const closeCamera = () => {
  if (mediaStream) { mediaStream.getTracks().forEach(track => track.stop()); mediaStream = null }
  showCamera.value = false
}

const capturePhoto = async () => {
  if (!videoRef.value || !canvasRef.value) return
  const video = videoRef.value, canvas = canvasRef.value
  canvas.width = video.videoWidth; canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(video, 0, 0)
    canvas.toBlob(async (blob) => {
      if (blob) { closeCamera(); await processFile(new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' })) }
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
  extractionError.value = ''; extractedData.value = null
  
  uploading.value = true
  try {
    const formData = new FormData(); formData.append('file', file)
    const res = await $api.post('/upload/media', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    form.receipt_url = res.data.url
    toast.add({ title: 'File uploaded!' })
  } catch (e: any) { extractionError.value = 'Upload failed'; uploading.value = false; return }
  uploading.value = false
  
  extracting.value = true
  try {
    const result = await Tesseract.recognize(file, 'eng+ind', { logger: (m: any) => console.log(m) })
    const text = result.data.text
    const keywords = ['invoice', 'faktur', 'nota', 'receipt', 'kwitansi', 'total', 'subtotal', 'rp', 'idr', 'amount', 'toll', 'parkir', 'tol']
    if (!keywords.some(kw => text.toLowerCase().includes(kw))) {
      extractionError.value = 'Document does not appear to be a receipt/invoice.'
      form.receipt_url = ''; extracting.value = false; return
    }
    extractedData.value = parseReceiptText(text)
    toast.add({ title: 'Receipt data extracted!', color: 'green' })
  } catch (e) { console.error('OCR Error:', e); extractionError.value = 'Failed to extract text' }
  extracting.value = false
}

const parseReceiptText = (text: string) => {
  const data: any = { raw_text: text }
  const invMatch = text.match(/(?:invoice|inv|no|faktur|nota|receipt)[^\d]*(\d+[\w-]*)/i)
  if (invMatch) data.invoice_number = invMatch[1]
  const dateMatch = text.match(/(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i)
  if (dateMatch) data.date = dateMatch[1]
  const amountPatterns = [/total[:\s]*(?:rp\.?|idr)?[\s]*([\d.,]+)/i, /(?:rp\.?|idr)[\s]*([\d.,]+)/gi]
  for (const pattern of amountPatterns) {
    const match = text.match(pattern)
    if (match) { const amount = parseFloat(match[1].replace(/\./g, '').replace(',', '.')); if (!isNaN(amount) && amount > 0) { data.total = amount; break } }
  }
  const lines = text.split('\n').filter(l => l.trim())
  if (lines.length > 0 && lines[0].length > 3 && lines[0].length < 50) data.vendor_name = lines[0].trim()
  return data
}

const applyExtractedData = () => {
  if (extractedData.value) {
    if (extractedData.value.total) form.amount = extractedData.value.total
    if (extractedData.value.vendor_name && !form.description) form.description = extractedData.value.vendor_name
    toast.add({ title: 'Data applied!' })
  }
}

onMounted(() => { fetchExpenses(); fetchVehicles(); fetchBookings() })
</script>
