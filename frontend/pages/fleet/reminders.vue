<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold">Reminders</h2>
        <p class="text-small text-gray-500">Document expiry and service alert management</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }" :disabled="reminders.length === 0">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" :disabled="reminders.length === 0">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="sm" @click="fetchReminders">Refresh</UButton>
        <UButton icon="i-heroicons-plus" size="sm" @click="openCreate">Add Reminder</UButton>
      </div>
    </div>

    <!-- Alert Summary -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <UCard :ui="{ body: { padding: 'p-3', background: overdueCount > 0 ? 'bg-red-50 dark:bg-red-900/20' : '' } }">
        <p class="text-xs text-gray-500">Overdue</p>
        <p class="text-xl font-bold text-red-500">{{ overdueCount }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3', background: dueSoonCount > 0 ? 'bg-yellow-50 dark:bg-yellow-900/20' : '' } }">
        <p class="text-xs text-gray-500">Due in 7 Days</p>
        <p class="text-xl font-bold text-yellow-500">{{ dueSoonCount }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Upcoming</p>
        <p class="text-xl font-bold text-blue-500">{{ upcomingCount }}</p>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <p class="text-xs text-gray-500">Completed</p>
        <p class="text-xl font-bold text-green-500">{{ completedCount }}</p>
      </UCard>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="reminders" :loading="loading" searchable :search-keys="['title', 'description']" empty-message="No reminders yet.">
        <template #vehicle_id-data="{ row }">
          <p class="text-xs font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #type-data="{ row }">
          <UBadge :color="getTypeColor(row.reminder_type)" variant="subtle" size="xs">{{ row.reminder_type }}</UBadge>
        </template>
        <template #title-data="{ row }">
          <div>
            <p class="text-xs font-medium">{{ row.title }}</p>
            <p class="text-[10px] text-gray-400 truncate max-w-40">{{ row.description }}</p>
          </div>
        </template>
        <template #due_date-data="{ row }">
          <div>
            <UBadge :color="getDueDateColor(row.due_date)" size="xs">{{ formatDate(row.due_date) }}</UBadge>
            <p class="text-[10px] text-gray-400 mt-0.5">{{ getDaysRemaining(row.due_date) }}</p>
          </div>
        </template>
        <template #reference_number-data="{ row }">
          <p class="text-xs font-mono">{{ row.reference_number || '—' }}</p>
        </template>
        <template #is_completed-data="{ row }">
          <UToggle v-model="row.is_completed" size="xs" @update:model-value="toggleComplete(row)" />
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="2xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="2xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteReminder(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingReminder ? 'Edit Reminder' : 'Add Reminder'" :loading="saving" @submit="saveReminder" size="lg">
      <div class="space-y-3">
        <UFormGroup label="Vehicle" required :ui="{ hint: 'text-small' }" hint="Vehicle for this reminder">
          <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." size="sm" />
        </UFormGroup>

        <UFormGroup label="Type" required :ui="{ hint: 'text-small' }" hint="Category of reminder">
          <USelect v-model="form.type" :options="typeOptions" size="sm" />
        </UFormGroup>

        <UFormGroup label="Title" required :ui="{ hint: 'text-small' }" hint="Short title">
          <UInput v-model="form.title" placeholder="e.g. STNK Renewal" size="sm" />
        </UFormGroup>

        <UFormGroup label="Description" :ui="{ hint: 'text-small' }" hint="Detailed notes">
          <UTextarea v-model="form.description" :rows="2" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Due Date" required :ui="{ hint: 'text-small' }" hint="When due">
            <UInput v-model="form.due_date" type="date" size="sm" />
          </UFormGroup>
          <UFormGroup label="Remind Days Before" :ui="{ hint: 'text-small' }" hint="Days before">
            <UInput v-model.number="form.reminder_days" type="number" size="sm" />
          </UFormGroup>
        </div>

        <UFormGroup label="Estimated Cost (Rp)" :ui="{ hint: 'text-small' }" hint="Estimated renewal cost">
          <UInput v-model.number="form.estimated_cost" type="number" placeholder="500000" size="sm" />
        </UFormGroup>

        <!-- STNK/License Upload Section (shows for STNK/LICENSE types) -->
        <div v-if="['STNK', 'DRIVER_LICENSE', 'KIR', 'INSURANCE'].includes(form.type)">
          <UDivider :label="getDocumentLabel(form.type) + ' Upload'" />
          
          <UFormGroup :label="getDocumentLabel(form.type)" required :ui="{ hint: 'text-small' }" :hint="'Take photo or upload ' + getDocumentLabel(form.type) + ' (auto-extracts number)'">
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
              <input ref="fileInput" type="file" class="hidden" accept="image/*" @change="handleFileSelect" />
              
              <!-- Camera Modal -->
              <div v-if="showCamera" class="fixed inset-0 bg-black z-50 flex flex-col">
                <div class="flex justify-between items-center p-4 text-white">
                  <span>Take {{ getDocumentLabel(form.type) }} Photo</span>
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
                  'border-green-500 bg-green-50': form.document_url && !extractionError,
                  'border-red-500 bg-red-50': extractionError
                }"
                @click="triggerFileUpload"
                @drop.prevent="handleFileDrop"
                @dragover.prevent
              >
                <div v-if="uploading || extracting" class="flex items-center justify-center gap-2 py-2">
                  <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
                  <span class="text-xs">{{ extracting ? 'Extracting document number...' : 'Uploading...' }}</span>
                </div>
                <div v-else-if="form.document_url && !extractionError" class="space-y-1">
                  <UIcon name="i-heroicons-check-circle" class="text-green-500 text-xl" />
                  <p class="text-xs text-green-600">Document uploaded!</p>
                  <img :src="form.document_url" class="max-h-20 mx-auto rounded" />
                </div>
                <div v-else-if="extractionError" class="space-y-1">
                  <UIcon name="i-heroicons-x-circle" class="text-red-500 text-xl" />
                  <p class="text-xs text-red-600">{{ extractionError }}</p>
                  <p class="text-[10px] text-gray-500">Click to try again</p>
                </div>
                <div v-else class="py-2">
                  <UIcon name="i-heroicons-cloud-arrow-up" class="text-2xl text-gray-400" />
                  <p class="text-xs text-gray-500 mt-1">Or drag & drop document here</p>
                </div>
              </div>
              <UInput v-model="form.document_url" placeholder="Or paste URL" size="xs" />
            </div>
          </UFormGroup>

          <!-- Extracted Document Data -->
          <div v-if="extractedData && extractedData.document_number" class="border rounded-lg p-3 bg-green-50 mt-2">
            <p class="text-xs font-semibold text-green-700">📋 Extracted {{ getDocumentLabel(form.type) }} Number</p>
            <p class="text-lg font-mono font-bold text-green-800 mt-1">{{ extractedData.document_number }}</p>
            <div v-if="extractedData.expiry_date" class="text-xs text-gray-600 mt-1">
              Expiry: <span class="font-medium">{{ extractedData.expiry_date }}</span>
            </div>
            <div v-if="extractedData.holder_name" class="text-xs text-gray-600">
              Name: <span class="font-medium">{{ extractedData.holder_name }}</span>
            </div>
            <UButton size="xs" variant="soft" color="green" class="mt-2" @click="applyExtractedData">
              Apply to Form
            </UButton>
          </div>
        </div>

        <UFormGroup label="Reference Number" :ui="{ hint: 'text-small' }" :hint="'Document/reference number (auto-filled if uploaded)'">
          <UInput v-model="form.reference_number" placeholder="e.g. STNK number, Police number" size="sm" />
        </UFormGroup>

        <UFormGroup label="Notes" :ui="{ hint: 'text-small' }" hint="Additional notes">
          <UTextarea v-model="form.notes" :rows="2" />
        </UFormGroup>

        <UFormGroup v-if="editingReminder" label="Status">
          <UCheckbox v-model="form.is_completed" label="Mark as completed" />
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
const editingReminder = ref<any>(null)
const reminders = ref<any[]>([])
const vehicles = ref<any[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const extractedData = ref<any>(null)

// Camera refs
const showCamera = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let mediaStream: MediaStream | null = null

const columns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'type', label: 'Type' },
  { key: 'title', label: 'Title' },
  { key: 'due_date', label: 'Due Date' },
  { key: 'reference_number', label: 'Ref #' },
  { key: 'is_completed', label: 'Done' },
  { key: 'actions', label: '' }
]

const typeOptions = [
  { label: 'Tax (Pajak)', value: 'TAX' },
  { label: 'Service', value: 'SERVICE' },
  { label: 'Insurance', value: 'INSURANCE' },
  { label: 'KIR', value: 'KIR' },
  { label: 'STNK', value: 'STNK' },
  { label: 'Driver License', value: 'DRIVER_LICENSE' },
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

const overdueCount = computed(() => reminders.value.filter(r => !r.is_completed && new Date(r.due_date) < new Date()).length)
const dueSoonCount = computed(() => {
  const now = new Date(); const week = new Date(Date.now() + 7*24*60*60*1000)
  return reminders.value.filter(r => !r.is_completed && new Date(r.due_date) >= now && new Date(r.due_date) <= week).length
})
const upcomingCount = computed(() => {
  const week = new Date(Date.now() + 7*24*60*60*1000)
  return reminders.value.filter(r => !r.is_completed && new Date(r.due_date) > week).length
})
const completedCount = computed(() => reminders.value.filter(r => r.is_completed).length)

const form = reactive({
  vehicle_id: '',
  type: 'OTHER',
  title: '',
  description: '',
  due_date: '',
  reminder_days: 7,
  estimated_cost: null as number | null,
  reference_number: '',
  document_url: '',
  notes: '',
  is_completed: false
})

// ========== FETCH ==========
const fetchReminders = async () => {
  loading.value = true
  try { reminders.value = (await $api.get('/fleet/reminders')).data } catch (e) { console.error(e) }
  finally { loading.value = false }
}
const fetchVehicles = async () => { try { vehicles.value = (await $api.get('/fleet/vehicles')).data } catch (e) { console.error(e) } }

// ========== HELPERS ==========
const getVehicleName = (id: string) => vehicles.value.find((v: any) => v.id === id)?.plate_number || '-'
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'
const getDocumentLabel = (type: string) => {
  const labels: Record<string, string> = { STNK: 'STNK', DRIVER_LICENSE: 'Driver License', KIR: 'KIR Certificate', INSURANCE: 'Insurance Policy' }
  return labels[type] || 'Document'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = { TAX: 'red', SERVICE: 'blue', INSURANCE: 'green', KIR: 'yellow', STNK: 'purple', DRIVER_LICENSE: 'cyan' }
  return colors[type] || 'gray'
}

const getDueDateColor = (dueDate: string) => {
  const d = new Date(dueDate); const now = new Date(); const week = new Date(Date.now() + 7*24*60*60*1000)
  if (d < now) return 'red'; if (d <= week) return 'yellow'; return 'gray'
}

const getDaysRemaining = (dueDate: string) => {
  const d = new Date(dueDate); const now = new Date()
  const diff = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return `${Math.abs(diff)}d overdue`
  if (diff === 0) return 'Due today'
  return `${diff}d remaining`
}

// ========== EXPORT ==========
const exportData = (format: string) => {
  const data = reminders.value.map((r: any) => ({
    'Vehicle': getVehicleName(r.vehicle_id),
    'Type': r.reminder_type,
    'Title': r.title,
    'Due Date': formatDate(r.due_date),
    'Reference': r.reference_number || '',
    'Status': r.is_completed ? 'Completed' : 'Pending',
    'Description': r.description || ''
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `reminders.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Reminders exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Reminders</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Vehicle Reminders Report</h1>
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
  editingReminder.value = null
  extractedData.value = null
  extractionError.value = ''
  const nextMonth = new Date(Date.now() + 30*24*60*60*1000).toISOString().slice(0, 10)
  Object.assign(form, {
    vehicle_id: '', type: 'OTHER', title: '', description: '', due_date: nextMonth,
    reminder_days: 7, estimated_cost: null, reference_number: '', document_url: '', notes: '', is_completed: false
  })
  isSlideoverOpen.value = true
}

const openEdit = (reminder: any) => {
  editingReminder.value = reminder
  extractedData.value = null
  extractionError.value = ''
  Object.assign(form, {
    vehicle_id: reminder.vehicle_id, type: reminder.reminder_type, title: reminder.title,
    description: reminder.description || '', due_date: reminder.due_date, reminder_days: reminder.remind_days_before || 7,
    estimated_cost: reminder.estimated_cost, reference_number: reminder.reference_number || '',
    document_url: reminder.document_url || '', notes: reminder.notes || '', is_completed: reminder.is_completed
  })
  isSlideoverOpen.value = true
}

const saveReminder = async () => {
  if (!form.vehicle_id || !form.title || !form.due_date) {
    toast.add({ title: 'Please fill all required fields', color: 'red' }); return
  }
  if (['STNK', 'DRIVER_LICENSE', 'KIR', 'INSURANCE'].includes(form.type) && !form.document_url) {
    toast.add({ title: `${getDocumentLabel(form.type)} upload is required`, color: 'red' }); return
  }
  
  saving.value = true
  try {
    const payload: any = { 
      vehicle_id: form.vehicle_id, 
      reminder_type: form.type, 
      title: form.title,
      description: form.description,
      due_date: form.due_date, 
      remind_days_before: form.reminder_days,
      estimated_cost: form.estimated_cost,
      reference_number: form.reference_number,
      document_url: form.document_url,
      notes: form.notes,
      is_completed: form.is_completed
    }
    if (!payload.estimated_cost) delete payload.estimated_cost
    if (!payload.document_url) delete payload.document_url
    
    if (editingReminder.value) {
      await $api.put(`/fleet/reminders/${editingReminder.value.id}`, payload)
      toast.add({ title: 'Reminder updated!' })
    } else {
      await $api.post('/fleet/reminders', payload)
      toast.add({ title: 'Reminder created!' })
    }
    isSlideoverOpen.value = false
    fetchReminders()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally { saving.value = false }
}

const toggleComplete = async (reminder: any) => {
  try {
    await $api.put(`/fleet/reminders/${reminder.id}`, { is_completed: reminder.is_completed })
    toast.add({ title: reminder.is_completed ? 'Completed!' : 'Marked incomplete' })
    fetchReminders()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

const deleteReminder = async (reminder: any) => {
  if (!confirm(`Delete "${reminder.title}"?`)) return
  try { await $api.delete(`/fleet/reminders/${reminder.id}`); toast.add({ title: 'Deleted!' }); fetchReminders() }
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
    form.document_url = res.data.url
    toast.add({ title: 'File uploaded!' })
  } catch (e: any) { extractionError.value = 'Upload failed'; uploading.value = false; return }
  uploading.value = false
  
  extracting.value = true
  try {
    const result = await Tesseract.recognize(file, 'eng+ind', { logger: (m: any) => console.log(m) })
    extractedData.value = parseDocumentText(result.data.text, form.type)
    if (extractedData.value.document_number) toast.add({ title: 'Document number extracted!', color: 'green' })
    else toast.add({ title: 'Could not extract number, please enter manually', color: 'yellow' })
  } catch (e) { console.error('OCR Error:', e); toast.add({ title: 'OCR failed, please enter number manually', color: 'yellow' }) }
  extracting.value = false
}

const parseDocumentText = (text: string, docType: string) => {
  const data: any = { raw_text: text }
  if (docType === 'STNK') {
    const stnkPatterns = [/no\.?\s*(?:registrasi|reg|polisi)[:\s]*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})/i, /([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})/i]
    for (const pattern of stnkPatterns) { const match = text.match(pattern); if (match) { data.document_number = match[1].replace(/\s+/g, ' ').trim(); break } }
    const dateMatch = text.match(/berlaku[^:]*[:\s]*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})/i); if (dateMatch) data.expiry_date = dateMatch[1]
    const nameMatch = text.match(/nama[:\s]*([A-Za-z\s]+)/i); if (nameMatch) data.holder_name = nameMatch[1].trim()
  } else if (docType === 'DRIVER_LICENSE') {
    const simPatterns = [/no\.?\s*(?:sim|license)[:\s]*(\d+)/i, /(\d{10,16})/]
    for (const pattern of simPatterns) { const match = text.match(pattern); if (match) { data.document_number = match[1]; break } }
    const nameMatch = text.match(/nama[:\s]*([A-Za-z\s]+)/i); if (nameMatch) data.holder_name = nameMatch[1].trim()
  } else if (docType === 'KIR') {
    const kirMatch = text.match(/no\.?\s*(?:kir|uji)[:\s]*([A-Z0-9\-\/]+)/i); if (kirMatch) data.document_number = kirMatch[1]
  } else if (docType === 'INSURANCE') {
    const insMatch = text.match(/(?:polis|policy)[:\s]*(?:no\.?)?[:\s]*([A-Z0-9\-\/]+)/i); if (insMatch) data.document_number = insMatch[1]
  }
  return data
}

const applyExtractedData = () => {
  if (extractedData.value) {
    if (extractedData.value.document_number) form.reference_number = extractedData.value.document_number
    if (extractedData.value.expiry_date && !form.due_date) {
      const parts = extractedData.value.expiry_date.split(/[\/\-]/)
      if (parts.length === 3) { const year = parts[2].length === 2 ? '20' + parts[2] : parts[2]; form.due_date = `${year}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}` }
    }
    toast.add({ title: 'Data applied!' })
  }
}

onMounted(() => { fetchReminders(); fetchVehicles() })
</script>
