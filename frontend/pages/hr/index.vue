<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">HR Dashboard</h2>
        <p class="text-gray-500 text-sm">Employee management, attendance tracking, and office monitoring</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/hr/employees">
          <UButton icon="i-heroicons-user-group" variant="soft">Employees</UButton>
        </NuxtLink>
        <NuxtLink to="/hr/attendance">
          <UButton icon="i-heroicons-clock" variant="soft">Attendance</UButton>
        </NuxtLink>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-primary-600">{{ stats.total_employees }}</p>
          <p class="text-sm text-gray-500">Total Employees</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-green-600">{{ stats.present_today }}</p>
          <p class="text-sm text-gray-500">Present Today</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-orange-600">{{ stats.late_today }}</p>
          <p class="text-sm text-gray-500">Late Today</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-blue-600">{{ stats.on_leave_today }}</p>
          <p class="text-sm text-gray-500">On Leave</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-red-600">{{ stats.absent_today }}</p>
          <p class="text-sm text-gray-500">Absent</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-yellow-600">{{ stats.pending_leave_requests }}</p>
          <p class="text-sm text-gray-500">Pending Leaves</p>
        </div>
      </UCard>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Live Camera Monitoring (2 columns) -->
      <div class="lg:col-span-2">
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <UIcon name="i-heroicons-video-camera" class="w-5 h-5 text-red-600" />
                <h3 class="font-semibold">Live Office Monitoring</h3>
                <UBadge v-if="cameras.length > 0" color="green" size="xs" variant="subtle">
                  {{ cameras.filter(c => c.is_active).length }} Active
                </UBadge>
              </div>
              <div class="flex gap-2">
                <UButton size="xs" variant="soft" icon="i-heroicons-plus" @click="openAddCamera">
                  Add Camera
                </UButton>
                <UButton size="xs" variant="ghost" icon="i-heroicons-arrow-path" @click="fetchCameras" />
              </div>
            </div>
          </template>

          <!-- Camera Grid -->
          <div v-if="cameras.length === 0" class="text-center py-12">
            <UIcon name="i-heroicons-video-camera" class="w-12 h-12 text-gray-400 mx-auto" />
            <p class="text-gray-500 mt-2">No cameras configured</p>
            <UButton size="sm" class="mt-4" @click="openAddCamera">
              Add Your First Camera
            </UButton>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div 
              v-for="camera in cameras" 
              :key="camera.id" 
              class="relative rounded-lg overflow-hidden bg-gray-900 aspect-video"
            >
              <!-- Camera Feed (Webcam or Stream) -->
              <video 
                v-if="camera.camera_type === 'WEBCAM' && activeCameraId === camera.id"
                ref="videoRef"
                autoplay
                playsinline
                muted
                class="w-full h-full object-cover"
              />
              <img 
                v-else-if="camera.stream_url"
                :src="camera.stream_url"
                :alt="camera.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center bg-gray-800">
                <div class="text-center">
                  <UIcon name="i-heroicons-video-camera-slash" class="w-10 h-10 text-gray-500" />
                  <p class="text-gray-400 text-sm mt-2">{{ camera.name }}</p>
                </div>
              </div>

              <!-- Camera Overlay -->
              <div class="absolute top-0 left-0 right-0 p-2 bg-gradient-to-b from-black/70 to-transparent">
                <div class="flex items-center justify-between">
                  <span class="text-white text-sm font-medium">{{ camera.name }}</span>
                  <UBadge :color="camera.is_active ? 'green' : 'gray'" size="xs">
                    {{ camera.is_active ? 'Live' : 'Offline' }}
                  </UBadge>
                </div>
              </div>

              <!-- Camera Controls -->
              <div class="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/70 to-transparent">
                <div class="flex justify-between items-center">
                  <span class="text-white text-xs">{{ camera.location || 'Unknown location' }}</span>
                  <div class="flex gap-1">
                    <UButton 
                      v-if="camera.camera_type === 'WEBCAM'"
                      size="xs" 
                      variant="soft" 
                      color="white"
                      :icon="activeCameraId === camera.id ? 'i-heroicons-stop' : 'i-heroicons-play'"
                      @click="toggleCamera(camera)"
                    />
                    <UButton 
                      size="xs" 
                      variant="soft" 
                      color="white"
                      icon="i-heroicons-pencil-square"
                      @click="editCamera(camera)"
                    />
                    <UButton 
                      size="xs" 
                      variant="soft" 
                      color="red"
                      icon="i-heroicons-trash"
                      @click="confirmDeleteCamera(camera)"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Quick Actions & Recent Activity -->
      <div class="space-y-6">
        <!-- Quick Actions -->
        <UCard>
          <template #header>
            <h3 class="font-semibold">Quick Actions</h3>
          </template>
          <div class="space-y-2">
            <NuxtLink to="/hr/employees" class="block">
              <UButton block variant="soft" icon="i-heroicons-user-plus">Add New Employee</UButton>
            </NuxtLink>
            <NuxtLink to="/hr/attendance" class="block">
              <UButton block variant="soft" icon="i-heroicons-finger-print" color="green">Face Check-In</UButton>
            </NuxtLink>
            <NuxtLink to="/hr/leave" class="block">
              <UButton block variant="soft" icon="i-heroicons-calendar-days" color="blue">Leave Requests</UButton>
            </NuxtLink>
            <NuxtLink to="/hr/payroll" class="block">
              <UButton block variant="soft" icon="i-heroicons-banknotes" color="yellow">Process Payroll</UButton>
            </NuxtLink>
          </div>
        </UCard>

        <!-- Recent Attendance -->
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold">Today's Check-ins</h3>
              <NuxtLink to="/hr/attendance">
                <UButton size="xs" variant="ghost">View All</UButton>
              </NuxtLink>
            </div>
          </template>
          <div v-if="recentAttendance.length === 0" class="text-center py-4 text-gray-500">
            No check-ins yet today
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="att in recentAttendance.slice(0, 5)" 
              :key="att.id" 
              class="flex items-center gap-3"
            >
              <div class="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                <img 
                  v-if="att.check_in_photo_url" 
                  :src="att.check_in_photo_url" 
                  class="w-10 h-10 rounded-full object-cover"
                />
                <UIcon v-else name="i-heroicons-user" class="w-5 h-5 text-primary-600" />
              </div>
              <div class="flex-1">
                <p class="font-medium text-sm">{{ att.employee_name }}</p>
                <p class="text-xs text-gray-500">
                  {{ att.check_in ? formatTime(att.check_in) : 'Not checked in' }}
                </p>
              </div>
              <UBadge 
                :color="att.status === 'PRESENT' ? 'green' : att.status === 'LATE' ? 'orange' : 'gray'" 
                size="xs"
              >
                {{ att.status }}
              </UBadge>
            </div>
          </div>
        </UCard>

        <!-- Alerts -->
        <UCard v-if="stats.contracts_expiring_soon > 0 || stats.pending_leave_requests > 0">
          <template #header>
            <h3 class="font-semibold text-orange-600">Alerts</h3>
          </template>
          <div class="space-y-2">
            <div v-if="stats.contracts_expiring_soon > 0" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-exclamation-triangle" class="w-4 h-4 text-orange-500" />
              <span>{{ stats.contracts_expiring_soon }} contracts expiring in 30 days</span>
            </div>
            <div v-if="stats.pending_leave_requests > 0" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-clock" class="w-4 h-4 text-blue-500" />
              <span>{{ stats.pending_leave_requests }} leave requests pending approval</span>
            </div>
          </div>
        </UCard>
      </div>
    </div>

    <!-- Add/Edit Camera Slideover -->
    <USlideover v-model="showCameraSlideover" :ui="{ width: 'max-w-md' }">
      <UCard class="h-full flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{{ editingCamera ? 'Edit Camera' : 'Add Camera' }}</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showCameraSlideover = false" />
          </div>
        </template>

        <div class="flex-1 overflow-y-auto space-y-4 p-1">
          <UFormGroup label="Camera Name" required :error="!cameraForm.name && formSubmitted ? 'Camera name is required' : ''">
            <UInput v-model="cameraForm.name" placeholder="e.g. Office Lobby" />
          </UFormGroup>
          
          <UFormGroup label="Location" required :error="!cameraForm.location && formSubmitted ? 'Location is required' : ''">
            <USelectMenu
              v-model="cameraForm.location"
              :options="workCenterOptions"
              searchable
              searchable-placeholder="Search work center..."
              placeholder="Select or type location"
              creatable
              @create="handleCreateLocation"
            />
          </UFormGroup>
          
          <UFormGroup label="Camera Type" required :error="!cameraForm.camera_type && formSubmitted ? 'Camera type is required' : ''">
            <USelect 
              v-model="cameraForm.camera_type" 
              :options="[
                { label: 'Webcam', value: 'WEBCAM' },
                { label: 'IP Camera', value: 'IP_CAMERA' },
                { label: 'CCTV', value: 'CCTV' },
                { label: 'USB Camera', value: 'USB_CAMERA' }
              ]"
              option-attribute="label"
              value-attribute="value"
            />
          </UFormGroup>
          
          <UFormGroup v-if="cameraForm.camera_type === 'IP_CAMERA' || cameraForm.camera_type === 'CCTV'" label="Stream URL">
            <UInput v-model="cameraForm.stream_url" placeholder="rtsp://192.168.1.100:554/stream" />
          </UFormGroup>
          
          <UFormGroup label="Enable AI Detection">
            <UToggle v-model="cameraForm.is_ai_enabled" />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showCameraSlideover = false">Cancel</UButton>
            <UButton 
              @click="saveCamera" 
              :loading="savingCamera"
              :disabled="!isFormValid"
            >
              Save
            </UButton>
          </div>
        </template>
      </UCard>
    </USlideover>

    <!-- Delete Confirmation Modal -->
    <UModal v-model="showDeleteModal">
      <UCard>
        <template #header>
          <h3 class="font-semibold text-red-600">Delete Camera</h3>
        </template>
        <p>Are you sure you want to delete camera "{{ cameraToDelete?.name }}"? This action cannot be undone.</p>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDeleteModal = false">Cancel</UButton>
            <UButton color="red" @click="deleteCamera" :loading="deletingCamera">Delete</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()

definePageMeta({ layout: 'default' })

const stats = ref({
  total_employees: 0,
  active_employees: 0,
  present_today: 0,
  late_today: 0,
  on_leave_today: 0,
  absent_today: 0,
  pending_leave_requests: 0,
  contracts_expiring_soon: 0
})

const cameras = ref<any[]>([])
const recentAttendance = ref<any[]>([])
const activeCameraId = ref<string | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
let mediaStream: MediaStream | null = null

// Work centers for location autocomplete
const workCenters = ref<any[]>([])
const workCenterOptions = computed(() => {
  return workCenters.value.map(wc => ({
    label: wc.name,
    value: wc.name
  }))
})

// Camera form
const showCameraSlideover = ref(false)
const editingCamera = ref<any>(null)
const savingCamera = ref(false)
const formSubmitted = ref(false)
const cameraForm = ref({
  name: '',
  location: '',
  camera_type: 'WEBCAM',
  stream_url: '',
  is_ai_enabled: false
})

// Delete camera
const showDeleteModal = ref(false)
const cameraToDelete = ref<any>(null)
const deletingCamera = ref(false)

// Computed for form validation
const isFormValid = computed(() => {
  return cameraForm.value.name && cameraForm.value.location && cameraForm.value.camera_type
})

const fetchStats = async () => {
  try {
    const res = await $api.get('/hr/stats')
    stats.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchCameras = async () => {
  try {
    const res = await $api.get('/hr/cameras')
    cameras.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchWorkCenters = async () => {
  try {
    const res = await $api.get('/manufacturing/work-centers')
    workCenters.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchRecentAttendance = async () => {
  try {
    const today = new Date().toISOString().split('T')[0]
    const res = await $api.get('/hr/attendance', { params: { start_date: today, end_date: today } })
    recentAttendance.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const toggleCamera = async (camera: any) => {
  if (activeCameraId.value === camera.id) {
    // Stop camera
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
      mediaStream = null
    }
    activeCameraId.value = null
  } else {
    // Start camera
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment', width: 640, height: 480 } 
      })
      activeCameraId.value = camera.id
      
      await nextTick()
      if (videoRef.value) {
        videoRef.value.srcObject = mediaStream
      }
    } catch (e) {
      console.error('Camera access denied:', e)
    }
  }
}

const openAddCamera = () => {
  editingCamera.value = null
  formSubmitted.value = false
  cameraForm.value = { name: '', location: '', camera_type: 'WEBCAM', stream_url: '', is_ai_enabled: false }
  showCameraSlideover.value = true
}

const editCamera = (camera: any) => {
  editingCamera.value = camera
  formSubmitted.value = false
  cameraForm.value = {
    name: camera.name,
    location: camera.location || '',
    camera_type: camera.camera_type,
    stream_url: camera.stream_url || '',
    is_ai_enabled: camera.is_ai_enabled
  }
  showCameraSlideover.value = true
}

const handleCreateLocation = (option: string) => {
  cameraForm.value.location = option
}

const saveCamera = async () => {
  formSubmitted.value = true
  if (!isFormValid.value) return
  
  savingCamera.value = true
  try {
    // Extract location value if it's an object
    const locationValue = typeof cameraForm.value.location === 'object' 
      ? cameraForm.value.location?.value || cameraForm.value.location?.label 
      : cameraForm.value.location
    
    const payload = {
      ...cameraForm.value,
      location: locationValue
    }
    
    if (editingCamera.value) {
      await $api.put(`/hr/cameras/${editingCamera.value.id}`, payload)
    } else {
      await $api.post('/hr/cameras', payload)
    }
    showCameraSlideover.value = false
    editingCamera.value = null
    cameraForm.value = { name: '', location: '', camera_type: 'WEBCAM', stream_url: '', is_ai_enabled: false }
    await fetchCameras()
  } catch (e) {
    console.error(e)
  } finally {
    savingCamera.value = false
  }
}

const confirmDeleteCamera = (camera: any) => {
  cameraToDelete.value = camera
  showDeleteModal.value = true
}

const deleteCamera = async () => {
  if (!cameraToDelete.value) return
  deletingCamera.value = true
  try {
    await $api.delete(`/hr/cameras/${cameraToDelete.value.id}`)
    showDeleteModal.value = false
    cameraToDelete.value = null
    await fetchCameras()
  } catch (e) {
    console.error(e)
  } finally {
    deletingCamera.value = false
  }
}

const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchStats()
  fetchCameras()
  fetchWorkCenters()
  fetchRecentAttendance()
})

onUnmounted(() => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
  }
})
</script>
