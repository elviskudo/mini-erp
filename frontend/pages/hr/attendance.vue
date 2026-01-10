<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Attendance Management</h2>
        <p class="text-gray-500 text-sm">Track employee attendance with face recognition and fingerprint</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton variant="soft" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton 
          icon="i-heroicons-camera" 
          color="green"
          @click="showCheckInModal = true"
        >
          Face Check-In
        </UButton>
        <UButton 
          icon="i-heroicons-finger-print" 
          color="blue"
          @click="fingerprintCheckIn"
          :loading="fingerprintProcessing"
        >
          Fingerprint
        </UButton>
      </div>
    </div>

    <!-- Tabs -->
    <UTabs :items="tabs" v-model="activeTab">
      <template #default="{ item, selected }">
        <span :class="selected ? 'text-primary-600' : 'text-gray-500'">{{ item.label }}</span>
      </template>
    </UTabs>

    <!-- Check-In Panel -->
    <UCard v-if="activeTab === 0">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Face Recognition Check-in -->
        <div>
          <h3 class="font-semibold mb-4 flex items-center gap-2">
            <UIcon name="i-heroicons-camera" class="w-5 h-5" />
            Face Recognition Check-In/Out
          </h3>
          <div class="bg-gray-900 rounded-lg aspect-video relative overflow-hidden">
            <video 
              ref="videoRef" 
              autoplay 
              playsinline 
              muted
              class="w-full h-full object-cover"
            />
            <canvas ref="canvasRef" class="hidden" />
            
            <!-- Status overlay -->
            <div 
              v-if="checkInStatus" 
              class="absolute inset-0 flex items-center justify-center bg-black/50"
            >
              <div class="text-center">
                <UIcon 
                  :name="checkInStatus === 'success' ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'" 
                  :class="checkInStatus === 'success' ? 'text-green-500' : 'text-red-500'"
                  class="w-16 h-16 mx-auto"
                />
                <p class="text-white text-lg mt-2">{{ checkInMessage }}</p>
                <p v-if="matchedEmployee" class="text-green-400 font-semibold mt-1">
                  {{ matchedEmployee.first_name }} {{ matchedEmployee.last_name }}
                </p>
              </div>
            </div>
          </div>
          
          <div class="flex gap-2 mt-4">
            <UButton 
              v-if="!cameraActive" 
              block 
              @click="startCamera"
              icon="i-heroicons-video-camera"
            >
              Start Camera
            </UButton>
            <template v-else>
              <UButton 
                block 
                color="green" 
                @click="captureAndCheckIn" 
                :loading="processing"
                icon="i-heroicons-arrow-left-on-rectangle"
              >
                Check-In
              </UButton>
              <UButton 
                block 
                color="orange" 
                @click="captureAndCheckOut" 
                :loading="processing"
                icon="i-heroicons-arrow-right-on-rectangle"
              >
                Check-Out
              </UButton>
            </template>
          </div>
        </div>

        <!-- Manual Check-in / Fingerprint -->
        <div class="space-y-6">
          <!-- Fingerprint Check-in -->
          <div>
            <h3 class="font-semibold mb-4 flex items-center gap-2">
              <UIcon name="i-heroicons-finger-print" class="w-5 h-5" />
              Fingerprint Check-In
            </h3>
            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 text-center">
              <p class="text-sm text-gray-500 mb-3">Click to verify fingerprint and check-in/out</p>
              <div class="flex gap-2 justify-center">
                <UButton 
                  color="green" 
                  @click="fingerprintCheckIn" 
                  :loading="fingerprintProcessing"
                  icon="i-heroicons-finger-print"
                >
                  Check-In
                </UButton>
                <UButton 
                  color="orange" 
                  @click="fingerprintCheckOut" 
                  :loading="fingerprintProcessing"
                  icon="i-heroicons-finger-print"
                >
                  Check-Out
                </UButton>
              </div>
            </div>
          </div>

          <!-- Manual Check-in -->
          <div>
            <h3 class="font-semibold mb-4">Manual Check-In</h3>
            <div class="space-y-4">
              <UFormGroup label="Select Employee">
                <USelectMenu 
                  v-model="selectedEmployee" 
                  :options="employees"
                  searchable
                  placeholder="Search employee..."
                  option-attribute="full_name"
                  value-attribute="id"
                >
                  <template #option="{ option }">
                    <div class="flex items-center gap-2">
                      <img 
                        v-if="option.profile_photo_url" 
                        :src="option.profile_photo_url" 
                        class="w-8 h-8 rounded-full object-cover"
                      />
                      <div v-else class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                        <span class="text-primary-600 text-xs font-medium">
                          {{ option.first_name?.[0] }}{{ option.last_name?.[0] }}
                        </span>
                      </div>
                      <div>
                        <p class="font-medium">{{ option.first_name }} {{ option.last_name }}</p>
                        <p class="text-xs text-gray-500">{{ option.employee_code }}</p>
                      </div>
                    </div>
                  </template>
                </USelectMenu>
              </UFormGroup>
              
              <UFormGroup label="Select Shift">
                <USelect 
                  v-model="selectedShift" 
                  :options="shiftOptions"
                  placeholder="Select shift..."
                  option-attribute="label"
                  value-attribute="value"
                />
              </UFormGroup>
              
              <UFormGroup label="Notes (optional)">
                <UTextarea v-model="manualNotes" placeholder="Add notes..." />
              </UFormGroup>
              
              <div class="flex gap-2">
                <UButton 
                  class="flex-1" 
                  color="green" 
                  @click="manualCheckIn" 
                  :loading="processing"
                  :disabled="!selectedEmployee"
                >
                  Manual Check-In
                </UButton>
                <UButton 
                  class="flex-1" 
                  color="orange" 
                  @click="manualCheckOut" 
                  :loading="processing"
                  :disabled="!selectedEmployee"
                >
                  Manual Check-Out
                </UButton>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Shift-Attendance Correlation Info -->
      <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h4 class="font-semibold text-blue-700 dark:text-blue-300 mb-2">How Shift & Attendance Works</h4>
        <ul class="text-sm text-blue-600 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li><strong>Shift</strong> defines expected work hours (start_time, end_time, break times)</li>
          <li>Employees are assigned to shifts via Employee Schedule</li>
          <li><strong>Late</strong> is calculated when check_in &gt; shift.start_time + tolerance</li>
          <li><strong>Overtime</strong> is calculated when check_out &gt; shift.end_time</li>
          <li>Attendance status auto-updates based on check-in time vs shift schedule</li>
        </ul>
      </div>
    </UCard>

    <!-- Attendance List -->
    <UCard v-if="activeTab === 1">
      <template #header>
        <div class="flex items-center justify-between flex-wrap gap-4">
          <h3 class="font-semibold">Attendance Records</h3>
          <div class="flex gap-2 items-center">
            <UInput v-model="filterStartDate" type="date" class="w-40" />
            <span class="text-gray-500">to</span>
            <UInput v-model="filterEndDate" type="date" class="w-40" />
            <UDropdown :items="exportRecordsItems">
              <UButton variant="soft" size="sm" icon="i-heroicons-arrow-down-tray">Export</UButton>
            </UDropdown>
            <UButton variant="ghost" icon="i-heroicons-arrow-path" @click="fetchAttendance" />
          </div>
        </div>
      </template>

      <UTable :columns="columns" :rows="attendanceList" :loading="loading">
        <template #employee_name-data="{ row }">
          <div class="flex items-center gap-2">
            <img 
              v-if="row.check_in_photo_url" 
              :src="row.check_in_photo_url" 
              class="w-8 h-8 rounded-full object-cover"
            />
            <div v-else class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <UIcon name="i-heroicons-user" class="w-4 h-4 text-gray-500" />
            </div>
            <span>{{ row.employee_name || 'Unknown' }}</span>
          </div>
        </template>
        
        <template #check_in-data="{ row }">
          <span v-if="row.check_in">{{ formatTime(row.check_in) }}</span>
          <span v-else class="text-gray-400">-</span>
        </template>
        
        <template #check_out-data="{ row }">
          <span v-if="row.check_out">{{ formatTime(row.check_out) }}</span>
          <span v-else class="text-gray-400">-</span>
        </template>
        
        <template #status-data="{ row }">
          <UBadge 
            :color="getStatusColor(row.status)" 
            size="sm"
          >
            {{ row.status }}
          </UBadge>
        </template>
        
        <template #shift-data="{ row }">
          <span v-if="row.shift_name">{{ row.shift_name }}</span>
          <span v-else class="text-gray-400">No shift</span>
        </template>
        
        <template #work_hours-data="{ row }">
          {{ row.work_hours?.toFixed(1) || '0' }} hrs
        </template>
        
        <template #late_minutes-data="{ row }">
          <span v-if="row.late_minutes > 0" class="text-orange-600">
            {{ row.late_minutes }} min
          </span>
          <span v-else class="text-green-600">On time</span>
        </template>
      </UTable>
    </UCard>

    <!-- Shifts Management -->
    <UCard v-if="activeTab === 2">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Work Shifts</h3>
          <div class="flex gap-2">
            <UDropdown :items="exportShiftsItems">
              <UButton variant="soft" size="sm" icon="i-heroicons-arrow-down-tray">Export</UButton>
            </UDropdown>
            <UButton size="sm" icon="i-heroicons-plus" @click="openShiftForm">Add Shift</UButton>
          </div>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <UCard v-for="shift in shifts" :key="shift.id" :ui="{ body: { padding: 'p-4' } }">
          <div class="flex items-center justify-between mb-3">
            <UBadge :color="shift.is_active ? 'green' : 'gray'">{{ shift.code }}</UBadge>
            <UDropdown :items="[[
              { label: 'Edit', icon: 'i-heroicons-pencil', click: () => editShift(shift) },
              { label: 'Delete', icon: 'i-heroicons-trash', click: () => confirmDeleteShift(shift) }
            ]]">
              <UButton variant="ghost" icon="i-heroicons-ellipsis-vertical" size="xs" />
            </UDropdown>
          </div>
          <h4 class="font-semibold">{{ shift.name }}</h4>
          <div class="mt-2 space-y-1 text-sm text-gray-500">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-clock" class="w-4 h-4" />
              <span>{{ shift.start_time }} - {{ shift.end_time }}</span>
            </div>
            <div v-if="shift.break_start" class="flex items-center gap-2">
              <UIcon name="i-heroicons-pause" class="w-4 h-4" />
              <span>Break: {{ shift.break_start }} - {{ shift.break_end }}</span>
            </div>
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-clock" class="w-4 h-4" />
              <span>Late tolerance: {{ shift.late_tolerance_minutes }} min</span>
            </div>
          </div>
        </UCard>
      </div>
    </UCard>

    <!-- Face Check-In Modal -->
    <UModal v-model="showCheckInModal" :ui="{ width: 'max-w-2xl' }">
      <UCard>
        <template #header>
          <h3 class="font-semibold">Face Recognition Check-In</h3>
        </template>
        
        <div class="space-y-4">
          <div class="bg-gray-900 rounded-lg aspect-video relative overflow-hidden">
            <video 
              ref="modalVideoRef" 
              autoplay 
              playsinline 
              muted
              class="w-full h-full object-cover"
            />
            <canvas ref="modalCanvasRef" class="hidden" />
          </div>
          
          <div v-if="!modalCameraActive" class="text-center">
            <UButton @click="startModalCamera" icon="i-heroicons-video-camera">
              Start Camera
            </UButton>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="closeCheckInModal">Close</UButton>
            <UButton 
              color="green" 
              @click="modalFaceCheckIn" 
              :loading="processing"
              :disabled="!modalCameraActive"
              icon="i-heroicons-finger-print"
            >
              Capture & Check-In
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Add/Edit Shift Slideover -->
    <USlideover v-model="showShiftSlideover" :ui="{ width: 'max-w-md' }">
      <UCard class="h-full flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{{ editingShift ? 'Edit Shift' : 'Add New Shift' }}</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showShiftSlideover = false" />
          </div>
        </template>
        
        <div class="flex-1 overflow-y-auto space-y-4 p-1">
          <UFormGroup label="Shift Name" required>
            <UInput v-model="shiftForm.name" placeholder="e.g. Morning Shift" />
          </UFormGroup>
          <UFormGroup label="Code" required>
            <UInput v-model="shiftForm.code" placeholder="e.g. AM" />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Start Time" required>
              <UInput v-model="shiftForm.start_time" type="time" />
            </UFormGroup>
            <UFormGroup label="End Time" required>
              <UInput v-model="shiftForm.end_time" type="time" />
            </UFormGroup>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Break Start">
              <UInput v-model="shiftForm.break_start" type="time" />
            </UFormGroup>
            <UFormGroup label="Break End">
              <UInput v-model="shiftForm.break_end" type="time" />
            </UFormGroup>
          </div>
          <UFormGroup label="Late Tolerance (minutes)">
            <UInput v-model="shiftForm.late_tolerance_minutes" type="number" />
          </UFormGroup>
          <UFormGroup label="Active">
            <UToggle v-model="shiftForm.is_active" />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showShiftSlideover = false">Cancel</UButton>
            <UButton @click="saveShift" :loading="savingShift">Save</UButton>
          </div>
        </template>
      </UCard>
    </USlideover>

    <!-- Delete Shift Modal -->
    <UModal v-model="showDeleteShiftModal">
      <UCard>
        <template #header>
          <h3 class="font-semibold text-red-600">Delete Shift</h3>
        </template>
        <p>Are you sure you want to delete shift "{{ shiftToDelete?.name }}"? This action cannot be undone.</p>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDeleteShiftModal = false">Cancel</UButton>
            <UButton color="red" @click="deleteShift" :loading="deletingShift">Delete</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const tabs = [
  { label: 'Check-In/Out', key: 'checkin' },
  { label: 'Attendance Records', key: 'records' },
  { label: 'Shifts', key: 'shifts' }
]
const activeTab = ref(0)

// Camera states
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const modalVideoRef = ref<HTMLVideoElement | null>(null)
const modalCanvasRef = ref<HTMLCanvasElement | null>(null)
let mediaStream: MediaStream | null = null
let modalMediaStream: MediaStream | null = null

const cameraActive = ref(false)
const modalCameraActive = ref(false)
const processing = ref(false)
const fingerprintProcessing = ref(false)
const checkInStatus = ref<'success' | 'error' | null>(null)
const checkInMessage = ref('')
const matchedEmployee = ref<any>(null)

// Data
const employees = ref<any[]>([])
const attendanceList = ref<any[]>([])
const shifts = ref<any[]>([])
const loading = ref(false)
const filterStartDate = ref(new Date().toISOString().split('T')[0])
const filterEndDate = ref(new Date().toISOString().split('T')[0])

// Manual check-in
const selectedEmployee = ref<string | null>(null)
const selectedShift = ref<string | null>(null)
const manualNotes = ref('')

// Computed shift options for select
const shiftOptions = computed(() => 
  shifts.value.map((s: any) => ({ 
    label: `${s.name} (${s.start_time} - ${s.end_time})`, 
    value: s.id 
  }))
)

// Modal states
const showCheckInModal = ref(false)
const showShiftSlideover = ref(false)
const showDeleteShiftModal = ref(false)
const editingShift = ref<any>(null)
const savingShift = ref(false)
const shiftToDelete = ref<any>(null)
const deletingShift = ref(false)

const shiftForm = ref({
  name: '',
  code: '',
  start_time: '08:00',
  end_time: '17:00',
  break_start: '12:00',
  break_end: '13:00',
  late_tolerance_minutes: 15,
  is_active: true
})

const columns = [
  { key: 'employee_name', label: 'Employee' },
  { key: 'date', label: 'Date' },
  { key: 'shift', label: 'Shift' },
  { key: 'check_in', label: 'Check In' },
  { key: 'check_out', label: 'Check Out' },
  { key: 'status', label: 'Status' },
  { key: 'work_hours', label: 'Work Hours' },
  { key: 'late_minutes', label: 'Late' }
]

// Export items
const exportItems = [
  [{ label: 'Export Attendance (PDF)', icon: 'i-heroicons-document', click: () => exportAttendance('pdf') }],
  [{ label: 'Export Attendance (Excel)', icon: 'i-heroicons-table-cells', click: () => exportAttendance('xlsx') }],
  [{ label: 'Export Attendance (CSV)', icon: 'i-heroicons-document-text', click: () => exportAttendance('csv') }]
]

const exportRecordsItems = [
  [{ label: 'PDF', click: () => exportAttendance('pdf') }],
  [{ label: 'Excel', click: () => exportAttendance('xlsx') }],
  [{ label: 'CSV', click: () => exportAttendance('csv') }]
]

const exportShiftsItems = [
  [{ label: 'PDF', click: () => exportShifts('pdf') }],
  [{ label: 'Excel', click: () => exportShifts('xlsx') }],
  [{ label: 'CSV', click: () => exportShifts('csv') }]
]

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'PRESENT': 'green',
    'LATE': 'orange',
    'ABSENT': 'red',
    'ON_LEAVE': 'blue',
    'HALF_DAY': 'yellow'
  }
  return colors[status] || 'gray'
}

const formatTime = (dateStr: string) => {
  const auth = useAuthStore()
  const timezone = auth.tenant?.timezone || 'UTC'
  
  // Ensure timestamp is treated as UTC by appending Z if no timezone indicator
  let utcDateStr = dateStr
  if (dateStr && !dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
    utcDateStr = dateStr.replace(' ', 'T') + 'Z'
  }
  
  return new Date(utcDateStr).toLocaleTimeString('id-ID', { 
    hour: '2-digit', 
    minute: '2-digit',
    timeZone: timezone
  })
}

// Export functions
const exportAttendance = async (format: string) => {
  try {
    const res = await $api.get('/export/attendance', {
      params: { format, start_date: filterStartDate.value, end_date: filterEndDate.value },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `attendance_${filterStartDate.value}_${filterEndDate.value}.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast.add({ title: 'Success', description: `Exported as ${format.toUpperCase()}` })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Export failed', color: 'red' })
  }
}

const exportShifts = async (format: string) => {
  try {
    const res = await $api.get('/export/shifts', {
      params: { format },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `shifts.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast.add({ title: 'Success', description: `Exported as ${format.toUpperCase()}` })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Export failed', color: 'red' })
  }
}

// Fingerprint check-in using FingerprintJS
const fingerprintCheckIn = async () => {
  fingerprintProcessing.value = true
  try {
    const FingerprintJS = await import('@fingerprintjs/fingerprintjs')
    const fp = await FingerprintJS.load()
    const result = await fp.get()
    
    // Send fingerprint to backend (using FormData as backend expects Form(...))
    const formData = new FormData()
    formData.append('fingerprint_id', result.visitorId)
    const res = await $api.post('/hr/attendance/fingerprint-check-in', formData)
    
    if (res.data.success) {
      matchedEmployee.value = res.data.employee
      checkInStatus.value = 'success'
      checkInMessage.value = res.data.message || 'Check-in successful'
      toast.add({ title: 'Success', description: `${res.data.employee?.first_name} checked in` })
      await fetchAttendance()
    } else {
      checkInStatus.value = 'error'
      checkInMessage.value = res.data.message || 'Fingerprint not recognized'
      toast.add({ title: 'Error', description: 'Fingerprint not recognized', color: 'red' })
    }
    
    setTimeout(() => {
      checkInStatus.value = null
      matchedEmployee.value = null
    }, 3000)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Fingerprint check-in failed', color: 'red' })
  } finally {
    fingerprintProcessing.value = false
  }
}

const fingerprintCheckOut = async () => {
  fingerprintProcessing.value = true
  try {
    const FingerprintJS = await import('@fingerprintjs/fingerprintjs')
    const fp = await FingerprintJS.load()
    const result = await fp.get()
    
    const formData = new FormData()
    formData.append('fingerprint_id', result.visitorId)
    const res = await $api.post('/hr/attendance/fingerprint-check-out', formData)
    
    if (res.data.success) {
      toast.add({ title: 'Success', description: `${res.data.employee?.first_name} checked out` })
      await fetchAttendance()
    } else {
      toast.add({ title: 'Error', description: 'Fingerprint not recognized', color: 'red' })
    }
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Check-out failed', color: 'red' })
  } finally {
    fingerprintProcessing.value = false
  }
}

// Camera functions
const startCamera = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 480 }
    })
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
    }
    cameraActive.value = true
  } catch (e) {
    console.error('Camera access denied:', e)
    toast.add({ title: 'Error', description: 'Camera access denied', color: 'red' })
  }
}

const startModalCamera = async () => {
  try {
    modalMediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 480 }
    })
    if (modalVideoRef.value) {
      modalVideoRef.value.srcObject = modalMediaStream
    }
    modalCameraActive.value = true
  } catch (e) {
    console.error('Camera access denied:', e)
  }
}

const captureImage = (video: HTMLVideoElement | null, canvas: HTMLCanvasElement | null): string | null => {
  if (!video || !canvas) return null
  
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return null
  
  ctx.drawImage(video, 0, 0)
  return canvas.toDataURL('image/jpeg', 0.8).split(',')[1]
}

const captureAndCheckIn = async () => {
  const imageBase64 = captureImage(videoRef.value, canvasRef.value)
  if (!imageBase64) return
  
  processing.value = true
  try {
    // Try server-side face recognition first
    const res = await $api.post('/hr/attendance/face-check-in', {
      face_image_base64: imageBase64
    })
    
    if (res.data.success) {
      matchedEmployee.value = res.data.employee
      checkInStatus.value = 'success'
      checkInMessage.value = res.data.message
      await fetchAttendance()
    } else {
      checkInStatus.value = 'error'
      checkInMessage.value = res.data.message || 'Face not recognized'
    }
    
    setTimeout(() => {
      checkInStatus.value = null
      checkInMessage.value = ''
      matchedEmployee.value = null
    }, 3000)
  } catch (e: any) {
    // If face recognition library not available, check if there's an employee with profile photo that user can select
    if (e.response?.status === 501) {
      // Server doesn't have face recognition - prompt user to use manual check-in
      checkInStatus.value = 'error'
      checkInMessage.value = 'Face recognition not available. Please use manual check-in.'
    } else {
      checkInStatus.value = 'error'
      checkInMessage.value = e.response?.data?.detail || 'Check-in failed'
    }
    setTimeout(() => { checkInStatus.value = null }, 3000)
  } finally {
    processing.value = false
  }
}

const captureAndCheckOut = async () => {
  const imageBase64 = captureImage(videoRef.value, canvasRef.value)
  if (!imageBase64) return
  
  processing.value = true
  try {
    // Try server-side face recognition first
    const res = await $api.post('/hr/attendance/face-check-out', {
      face_image_base64: imageBase64
    })
    
    if (res.data.success) {
      matchedEmployee.value = res.data.employee
      checkInStatus.value = 'success'
      checkInMessage.value = res.data.message || 'Check-out successful'
      await fetchAttendance()
    } else {
      checkInStatus.value = 'error'
      checkInMessage.value = res.data.message || 'Face not recognized'
    }
    
    setTimeout(() => {
      checkInStatus.value = null
      matchedEmployee.value = null
    }, 3000)
  } catch (e: any) {
    if (e.response?.status === 501) {
      checkInStatus.value = 'error'
      checkInMessage.value = 'Face recognition not available. Please use manual check-out.'
    } else {
      checkInStatus.value = 'error'
      checkInMessage.value = e.response?.data?.detail || 'Check-out failed'
    }
    setTimeout(() => { checkInStatus.value = null }, 3000)
  } finally {
    processing.value = false
  }
}

const manualCheckIn = async () => {
  if (!selectedEmployee.value) return
  processing.value = true
  try {
    // Simple POST with employee_id as query param - no body needed for manual check-in
    await $api.post(`/hr/attendance/simple-face-check-in?employee_id=${selectedEmployee.value}`)
    toast.add({ title: 'Success', description: 'Manual check-in recorded' })
    await fetchAttendance()
    selectedEmployee.value = null
    selectedShift.value = null
    manualNotes.value = ''
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || e.response?.data?.message || 'Check-in failed', color: 'red' })
  } finally {
    processing.value = false
  }
}

const manualCheckOut = async () => {
  if (!selectedEmployee.value) return
  processing.value = true
  try {
    // Simple POST with employee_id as query param - no body needed for manual check-out
    await $api.post(`/hr/attendance/simple-face-check-out?employee_id=${selectedEmployee.value}`)
    toast.add({ title: 'Success', description: 'Manual check-out recorded' })
    await fetchAttendance()
    selectedEmployee.value = null
    selectedShift.value = null
    manualNotes.value = ''
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || e.response?.data?.message || 'Check-out failed', color: 'red' })
  } finally {
    processing.value = false
  }
}

const modalFaceCheckIn = async () => {
  const imageBase64 = captureImage(modalVideoRef.value, modalCanvasRef.value)
  if (!imageBase64) return
  
  processing.value = true
  try {
    const res = await $api.post('/hr/attendance/face-check-in', {
      face_image_base64: imageBase64
    })
    
    if (res.data.success) {
      toast.add({ title: 'Success', description: res.data.message })
      closeCheckInModal()
      await fetchAttendance()
    } else {
      toast.add({ title: 'Error', description: res.data.message || 'Face not recognized', color: 'red' })
    }
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Check-in failed', color: 'red' })
  } finally {
    processing.value = false
  }
}

const closeCheckInModal = () => {
  if (modalMediaStream) {
    modalMediaStream.getTracks().forEach(track => track.stop())
    modalMediaStream = null
  }
  modalCameraActive.value = false
  showCheckInModal.value = false
}

// Data fetching
const fetchEmployees = async () => {
  try {
    const res = await $api.get('/hr/employees')
    employees.value = res.data.map((e: any) => ({
      ...e,
      full_name: `${e.first_name} ${e.last_name}`
    }))
  } catch (e) {
    console.error(e)
  }
}

const fetchAttendance = async () => {
  loading.value = true
  try {
    const res = await $api.get('/hr/attendance', {
      params: { start_date: filterStartDate.value, end_date: filterEndDate.value }
    })
    attendanceList.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchShifts = async () => {
  try {
    const res = await $api.get('/hr/shifts')
    shifts.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const openShiftForm = () => {
  editingShift.value = null
  shiftForm.value = {
    name: '', code: '', start_time: '08:00', end_time: '17:00',
    break_start: '12:00', break_end: '13:00', late_tolerance_minutes: 15, is_active: true
  }
  showShiftSlideover.value = true
}

const editShift = (shift: any) => {
  editingShift.value = shift
  shiftForm.value = { ...shift }
  showShiftSlideover.value = true
}

const saveShift = async () => {
  savingShift.value = true
  try {
    if (editingShift.value) {
      await $api.put(`/hr/shifts/${editingShift.value.id}`, shiftForm.value)
      toast.add({ title: 'Success', description: 'Shift updated' })
    } else {
      await $api.post('/hr/shifts', shiftForm.value)
      toast.add({ title: 'Success', description: 'Shift created' })
    }
    showShiftSlideover.value = false
    await fetchShifts()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save shift', color: 'red' })
  } finally {
    savingShift.value = false
  }
}

const confirmDeleteShift = (shift: any) => {
  shiftToDelete.value = shift
  showDeleteShiftModal.value = true
}

const deleteShift = async () => {
  if (!shiftToDelete.value) return
  deletingShift.value = true
  try {
    await $api.delete(`/hr/shifts/${shiftToDelete.value.id}`)
    toast.add({ title: 'Success', description: 'Shift deleted' })
    showDeleteShiftModal.value = false
    await fetchShifts()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to delete shift', color: 'red' })
  } finally {
    deletingShift.value = false
  }
}

watch([filterStartDate, filterEndDate], () => fetchAttendance())

onMounted(() => {
  fetchEmployees()
  fetchAttendance()
  fetchShifts()
})

onUnmounted(() => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
  }
  if (modalMediaStream) {
    modalMediaStream.getTracks().forEach(track => track.stop())
  }
})
</script>
