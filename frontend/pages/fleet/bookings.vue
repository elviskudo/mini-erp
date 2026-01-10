<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Vehicle Bookings</h2>
        <p class="text-gray-500 text-small">Schedule and manage vehicle usage</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }" :disabled="bookings.length === 0">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" :disabled="bookings.length === 0">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchBookings">Refresh</UButton>
        <UButton icon="i-heroicons-building-office-2" variant="outline" @click="showDepartmentModal = true">Departments</UButton>
        <UButton icon="i-heroicons-user-group" variant="outline" @click="showDriverModal = true">Drivers</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Booking</UButton>
      </div>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="bookings" :loading="loading" searchable :search-keys="['code', 'destination']" empty-message="No bookings yet.">
        <template #code-data="{ row }">
          <p class="font-medium font-mono">{{ row.code }}</p>
        </template>
        <template #vehicle_id-data="{ row }">
          <p class="font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #purpose-data="{ row }">
          <div>
            <UBadge :color="getPurposeColor(row.purpose)" variant="subtle" size="sm">{{ formatPurpose(row.purpose) }}</UBadge>
            <p class="text-xs text-gray-400 mt-1">{{ row.destination }}</p>
          </div>
        </template>
        <template #department_id-data="{ row }">
          <p class="text-sm">{{ getDepartmentName(row.department_id) }}</p>
        </template>
        <template #driver_id-data="{ row }">
          <p class="text-sm">{{ getDriverName(row.driver_id) }}</p>
        </template>
        <template #start_datetime-data="{ row }">
          <div class="text-sm">
            <p>{{ formatDate(row.start_datetime) }}</p>
            <p class="text-gray-400">to {{ formatDate(row.end_datetime) }}</p>
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton v-if="row.status === 'PENDING'" size="xs" icon="i-heroicons-check" variant="ghost" color="green" @click="approveBooking(row)" title="Approve" />
            <UButton v-if="row.status === 'PENDING'" size="xs" icon="i-heroicons-x-mark" variant="ghost" color="red" @click="openRejectModal(row)" title="Reject" />
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteBooking(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Booking Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingBooking ? 'Edit Booking' : 'New Booking'" :loading="saving" @submit="saveBooking" size="lg">
      <UFormGroup label="Vehicle" required>
        <p class="text-small text-gray-500 mb-1">Select the vehicle to book</p>
        <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." />
      </UFormGroup>

      <UFormGroup label="Purpose" required>
        <p class="text-small text-gray-500 mb-1">Reason for booking</p>
        <USelect v-model="form.purpose" :options="purposeOptions" />
      </UFormGroup>

      <UFormGroup label="Department" required hint="Department making the request">
        <USelect v-model="form.department_id" :options="departmentOptions" placeholder="Select department..." />
      </UFormGroup>

      <UFormGroup label="Driver" required hint="Assigned driver for this trip">
        <USelect v-model="form.driver_id" :options="driverOptions" placeholder="Select driver..." />
      </UFormGroup>

      <UDivider label="Destination" />
      
      <UFormGroup label="Destination Address" required hint="Enter the full destination address">
        <UInput v-model="form.destination" placeholder="Jl. Example No. 123, Jakarta" />
      </UFormGroup>

      <UDivider label="Schedule" />

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Start Date/Time" required hint="When the trip starts">
          <UInput v-model="form.start_datetime" type="datetime-local" />
        </UFormGroup>
        <UFormGroup label="End Date/Time" required hint="Expected return time">
          <UInput v-model="form.end_datetime" type="datetime-local" />
        </UFormGroup>
      </div>

      <UFormGroup label="Notes" hint="Additional trip notes or instructions">
        <UTextarea v-model="form.notes" :rows="2" placeholder="Special instructions, pickup notes, etc." />
      </UFormGroup>

      <template v-if="editingBooking">
        <UDivider label="Trip Details" />
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Start Odometer" hint="Odometer reading at trip start (km)">
            <UInput v-model.number="form.start_odometer" type="number" placeholder="e.g. 45000" />
          </UFormGroup>
          <UFormGroup label="End Odometer" hint="Odometer reading at trip end (km)">
            <UInput v-model.number="form.end_odometer" type="number" placeholder="e.g. 45250" />
          </UFormGroup>
        </div>
        <UFormGroup label="Status" hint="Current booking status">
          <USelect v-model="form.status" :options="statusOptions" />
        </UFormGroup>
      </template>
    </FormSlideover>

    <!-- Department Management Modal -->
    <UModal v-model="showDepartmentModal" :ui="{ width: 'sm:max-w-lg' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Department Management</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showDepartmentModal = false" />
          </div>
        </template>
        <div class="space-y-4">
          <div class="flex gap-2">
            <UInput v-model="deptForm.code" placeholder="Code *" class="w-24" />
            <UInput v-model="deptForm.name" placeholder="Department Name *" class="flex-1" />
            <UButton v-if="editingDept" icon="i-heroicons-check" color="green" @click="updateDepartment" />
            <UButton v-if="editingDept" icon="i-heroicons-x-mark" variant="ghost" @click="cancelEditDept" />
            <UButton v-else icon="i-heroicons-plus" @click="addDepartment" />
          </div>
          <div class="divide-y max-h-64 overflow-y-auto">
            <div v-for="dept in departments" :key="dept.id" class="py-2 flex items-center justify-between">
              <div>
                <span class="font-mono text-sm text-gray-500">{{ dept.code }}</span>
                <span class="ml-2">{{ dept.name }}</span>
              </div>
              <div class="flex gap-1">
                <UButton icon="i-heroicons-pencil" size="xs" variant="ghost" @click="editDept(dept)" />
                <UButton icon="i-heroicons-trash" size="xs" variant="ghost" color="red" @click="deleteDepartment(dept)" />
              </div>
            </div>
          </div>
        </div>
      </UCard>
    </UModal>

    <!-- Driver Management Modal - Full Form -->
    <UModal v-model="showDriverModal" :ui="{ width: 'sm:max-w-2xl' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{{ editingDriver ? 'Edit Driver' : 'Add Driver' }}</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="closeDriverModal" />
          </div>
        </template>
        <div class="space-y-4 max-h-[70vh] overflow-y-auto">
          <!-- Driver Form -->
          <UFormGroup label="Name" required hint="Driver's full legal name">
            <UInput v-model="driverForm.name" placeholder="e.g. Budi Santoso" />
          </UFormGroup>

          <UFormGroup label="Phone Number" required hint="Active phone number for contact">
            <UInput v-model="driverForm.phone" placeholder="e.g. 081234567890" />
          </UFormGroup>

          <UFormGroup label="Card ID Number (KTP)" required hint="16-digit KTP number">
            <UInput v-model="driverForm.card_id_number" placeholder="e.g. 3175012345678901" />
          </UFormGroup>

          <UFormGroup label="Card ID Upload" hint="Upload KTP image via Cloudinary">
            <div class="space-y-2">
              <div 
                class="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer hover:border-primary-500 transition-colors"
                :class="{ 'border-green-500 bg-green-50': driverForm.card_id_url }"
                @click="triggerFileUpload"
                @drop.prevent="handleFileDrop"
                @dragover.prevent
              >
                <input ref="fileInput" type="file" class="hidden" accept="image/*" @change="handleFileSelect" />
                <div v-if="uploading" class="flex items-center justify-center gap-2">
                  <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
                  <span>Uploading...</span>
                </div>
                <div v-else-if="driverForm.card_id_url" class="space-y-2">
                  <UIcon name="i-heroicons-check-circle" class="text-green-500 text-2xl" />
                  <p class="text-sm text-green-600">Image uploaded!</p>
                  <img :src="driverForm.card_id_url" class="max-h-24 mx-auto rounded" />
                </div>
                <div v-else>
                  <UIcon name="i-heroicons-cloud-arrow-up" class="text-3xl text-gray-400" />
                  <p class="text-sm text-gray-500 mt-2">Click or drag to upload KTP image</p>
                </div>
              </div>
              <UInput v-model="driverForm.card_id_url" placeholder="Or paste image URL directly" size="sm" />
            </div>
          </UFormGroup>

          <UFormGroup label="Employment Status" required hint="Type of employment relationship">
            <USelect v-model="driverForm.employment_status" :options="employmentOptions" placeholder="Select status..." />
          </UFormGroup>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="License Number (SIM)" required hint="SIM number">
              <UInput v-model="driverForm.license_number" placeholder="e.g. 123456789012" />
            </UFormGroup>
            <UFormGroup label="License Type" required hint="Type of driving license">
              <USelect v-model="driverForm.license_type" :options="licenseOptions" placeholder="Select type..." />
            </UFormGroup>
          </div>

          <UFormGroup label="Email" hint="Optional email address">
            <UInput v-model="driverForm.email" type="email" placeholder="driver@example.com" />
          </UFormGroup>

          <UFormGroup label="Address" hint="Current residential address">
            <UTextarea v-model="driverForm.address" :rows="2" placeholder="Full address..." />
          </UFormGroup>

          <UFormGroup label="Notes" hint="Additional notes about the driver">
            <UTextarea v-model="driverForm.notes" :rows="2" placeholder="e.g. Preferred routes, availability, etc." />
          </UFormGroup>

          <div class="flex justify-end gap-2 pt-4 border-t">
            <UButton v-if="editingDriver" variant="outline" @click="cancelEditDriver">Cancel</UButton>
            <UButton @click="saveDriver" :loading="savingDriver">
              {{ editingDriver ? 'Update Driver' : 'Add Driver' }}
            </UButton>
          </div>
          
          <UDivider label="Existing Drivers" />
          
          <div class="divide-y max-h-48 overflow-y-auto">
            <div v-for="driver in drivers" :key="driver.id" class="py-3 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <img v-if="driver.qr_code" :src="driver.qr_code" class="w-12 h-12 border rounded" />
                <div>
                  <p class="font-medium">{{ driver.code }} - {{ driver.name }}</p>
                  <p class="text-xs text-gray-400">
                    <UBadge size="xs" :color="getEmploymentColor(driver.employment_status)" variant="subtle">
                      {{ driver.employment_status || 'Unknown' }}
                    </UBadge>
                    <span class="ml-2">📞 {{ driver.phone || 'No phone' }}</span>
                  </p>
                </div>
              </div>
              <div class="flex gap-1">
                <UButton icon="i-heroicons-pencil" size="xs" variant="ghost" @click="editDriver(driver)" />
                <UButton icon="i-heroicons-trash" size="xs" variant="ghost" color="red" @click="deleteDriver(driver)" />
              </div>
            </div>
            <p v-if="drivers.length === 0" class="py-4 text-center text-gray-400">No drivers yet</p>
          </div>
        </div>
      </UCard>
    </UModal>

    <!-- Reject Booking Modal -->
    <UModal v-model="showRejectModal">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-red-600">Reject Booking</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showRejectModal = false" />
          </div>
        </template>
        <div class="space-y-4">
          <p class="text-small text-gray-600">Are you sure you want to reject booking <strong>{{ rejectingBooking?.code }}</strong>?</p>
          <UFormGroup label="Rejection Reason" required>
            <p class="text-small text-gray-500 mb-1">Provide a reason for rejecting this booking</p>
            <UTextarea v-model="rejectReason" :rows="3" placeholder="e.g. Vehicle not available, conflicting schedule, etc." />
          </UFormGroup>
          <div class="flex justify-end gap-2">
            <UButton variant="outline" @click="showRejectModal = false">Cancel</UButton>
            <UButton color="red" @click="rejectBooking" :loading="rejecting">Reject Booking</UButton>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const savingDriver = ref(false)
const uploading = ref(false)
const isSlideoverOpen = ref(false)
const editingBooking = ref<any>(null)
const bookings = ref<any[]>([])
const vehicles = ref<any[]>([])
const departments = ref<any[]>([])
const drivers = ref<any[]>([])
const showDepartmentModal = ref(false)
const showDriverModal = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// Rejection
const showRejectModal = ref(false)
const rejectingBooking = ref<any>(null)
const rejectReason = ref('')
const rejecting = ref(false)

// Department form
const editingDept = ref<any>(null)
const deptForm = reactive({ code: '', name: '' })

// Driver form
const editingDriver = ref<any>(null)
const driverForm = reactive({
  name: '', phone: '', email: '', card_id_number: '', card_id_url: '',
  employment_status: '', license_number: '', license_type: '', address: '', notes: ''
})

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'purpose', label: 'Purpose' },
  { key: 'department_id', label: 'Department' },
  { key: 'driver_id', label: 'Driver' },
  { key: 'start_datetime', label: 'Schedule' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const purposeOptions = [
  { label: 'Business Trip', value: 'BUSINESS_TRIP' },
  { label: 'Delivery', value: 'DELIVERY' },
  { label: 'Client Visit', value: 'CLIENT_VISIT' },
  { label: 'Site Inspection', value: 'SITE_INSPECTION' },
  { label: 'Pickup', value: 'PICKUP' },
  { label: 'Event', value: 'EVENT' },
  { label: 'Training', value: 'TRAINING' },
  { label: 'Other', value: 'OTHER' }
]

const statusOptions = [
  { label: 'Pending', value: 'PENDING' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Rejected', value: 'REJECTED' },
  { label: 'In Use', value: 'IN_USE' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Cancelled', value: 'CANCELLED' }
]

const employmentOptions = [
  { label: 'Permanent', value: 'PERMANENT' },
  { label: 'Contract', value: 'CONTRACT' },
  { label: 'Freelance', value: 'FREELANCE' }
]

const licenseOptions = [
  { label: 'SIM A - Personal Car', value: 'A' },
  { label: 'SIM B1 - Truck/Bus', value: 'B1' },
  { label: 'SIM B2 - Trailer/Tank', value: 'B2' },
  { label: 'SIM C - Motorcycle', value: 'C' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const departmentOptions = computed(() => 
  departments.value.map((d: any) => ({ label: `${d.code} - ${d.name}`, value: d.id }))
)

const driverOptions = computed(() => 
  drivers.value.map((d: any) => ({ label: `${d.code} - ${d.name}`, value: d.id }))
)

const form = reactive({
  vehicle_id: '',
  purpose: 'BUSINESS_TRIP',
  department_id: '',
  driver_id: '',
  destination: '',
  destination_lat: null as number | null,
  destination_lng: null as number | null,
  start_datetime: '',
  end_datetime: '',
  notes: '',
  start_odometer: null as number | null,
  end_odometer: null as number | null,
  status: 'PENDING'
})

const fetchBookings = async () => {
  loading.value = true
  try {
    const res = await $api.get('/fleet/bookings')
    bookings.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchVehicles = async () => {
  try { vehicles.value = (await $api.get('/fleet/vehicles')).data } catch (e) { console.error(e) }
}

const fetchDepartments = async () => {
  try { departments.value = (await $api.get('/fleet/departments')).data } catch (e) { console.error(e) }
}

const fetchDrivers = async () => {
  try { drivers.value = (await $api.get('/fleet/drivers')).data } catch (e) { console.error(e) }
}

const getVehicleName = (id: string) => vehicles.value.find((v: any) => v.id === id)?.plate_number || '-'
const getDepartmentName = (id: string) => departments.value.find((d: any) => d.id === id)?.name || '-'
const getDriverName = (id: string) => drivers.value.find((d: any) => d.id === id)?.name || '-'
const getEmploymentColor = (status: string) => ({ PERMANENT: 'green', CONTRACT: 'blue', FREELANCE: 'yellow' })[status] || 'gray'

const openCreate = () => {
  editingBooking.value = null
  Object.assign(form, {
    vehicle_id: '', purpose: 'BUSINESS_TRIP', department_id: '', driver_id: '',
    destination: '', destination_lat: null, destination_lng: null,
    start_datetime: '', end_datetime: '', notes: '',
    start_odometer: null, end_odometer: null, status: 'PENDING'
  })
  isSlideoverOpen.value = true
}

const openEdit = (booking: any) => {
  editingBooking.value = booking
  Object.assign(form, {
    vehicle_id: booking.vehicle_id,
    purpose: booking.purpose || 'BUSINESS_TRIP',
    department_id: booking.department_id || '',
    driver_id: booking.driver_id || '',
    destination: booking.destination || '',
    destination_lat: booking.destination_lat,
    destination_lng: booking.destination_lng,
    start_datetime: booking.start_datetime?.slice(0, 16) || '',
    end_datetime: booking.end_datetime?.slice(0, 16) || '',
    notes: booking.notes || '',
    start_odometer: booking.start_odometer,
    end_odometer: booking.end_odometer,
    status: booking.status
  })
  isSlideoverOpen.value = true
}

const saveBooking = async () => {
  if (!form.vehicle_id) return toast.add({ title: 'Vehicle is required', color: 'red' })
  if (!form.destination) return toast.add({ title: 'Destination is required', color: 'red' })
  if (!form.department_id) return toast.add({ title: 'Department is required', color: 'red' })
  if (!form.driver_id) return toast.add({ title: 'Driver is required', color: 'red' })
  if (!form.start_datetime || !form.end_datetime) return toast.add({ title: 'Schedule is required', color: 'red' })
  
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.start_odometer) delete payload.start_odometer
    if (!payload.end_odometer) delete payload.end_odometer
    if (!payload.destination_lat) delete payload.destination_lat
    if (!payload.destination_lng) delete payload.destination_lng
    
    if (editingBooking.value) {
      await $api.put(`/fleet/bookings/${editingBooking.value.id}`, payload)
      toast.add({ title: 'Booking updated!' })
    } else {
      await $api.post('/fleet/bookings', payload)
      toast.add({ title: 'Booking created!' })
    }
    isSlideoverOpen.value = false
    fetchBookings()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const approveBooking = async (booking: any) => {
  try {
    await $api.put(`/fleet/bookings/${booking.id}`, { status: 'APPROVED' })
    toast.add({ title: 'Booking approved!' })
    fetchBookings()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

const openRejectModal = (booking: any) => {
  rejectingBooking.value = booking
  rejectReason.value = ''
  showRejectModal.value = true
}

const rejectBooking = async () => {
  if (!rejectReason.value.trim()) return toast.add({ title: 'Rejection reason is required', color: 'red' })
  
  rejecting.value = true
  try {
    await $api.put(`/fleet/bookings/${rejectingBooking.value.id}`, { 
      status: 'REJECTED',
      reject_reason: rejectReason.value
    })
    toast.add({ title: 'Booking rejected', color: 'orange' })
    showRejectModal.value = false
    fetchBookings()
  } catch (e: any) { 
    toast.add({ title: 'Error', description: e.response?.data?.detail, color: 'red' }) 
  } finally {
    rejecting.value = false
  }
}

const deleteBooking = async (booking: any) => {
  if (!confirm(`Delete booking "${booking.code}"?`)) return
  try {
    await $api.delete(`/fleet/bookings/${booking.id}`)
    toast.add({ title: 'Booking deleted!' })
    fetchBookings()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

// ========== DEPARTMENT CRUD ==========
const addDepartment = async () => {
  if (!deptForm.code || !deptForm.name) return toast.add({ title: 'Code and Name required', color: 'red' })
  try {
    await $api.post('/fleet/departments', deptForm)
    toast.add({ title: 'Department added!' })
    deptForm.code = ''
    deptForm.name = ''
    fetchDepartments()
  } catch (e: any) { toast.add({ title: 'Error', description: e.response?.data?.detail, color: 'red' }) }
}

const editDept = (dept: any) => {
  editingDept.value = dept
  deptForm.code = dept.code
  deptForm.name = dept.name
}

const updateDepartment = async () => {
  if (!deptForm.code || !deptForm.name) return toast.add({ title: 'Code and Name required', color: 'red' })
  try {
    await $api.put(`/fleet/departments/${editingDept.value.id}`, deptForm)
    toast.add({ title: 'Department updated!' })
    cancelEditDept()
    fetchDepartments()
  } catch (e: any) { toast.add({ title: 'Error', description: e.response?.data?.detail, color: 'red' }) }
}

const cancelEditDept = () => {
  editingDept.value = null
  deptForm.code = ''
  deptForm.name = ''
}

const deleteDepartment = async (dept: any) => {
  if (!confirm(`Delete "${dept.name}"?`)) return
  try {
    await $api.delete(`/fleet/departments/${dept.id}`)
    toast.add({ title: 'Department deleted!' })
    fetchDepartments()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

// ========== DRIVER CRUD ==========
const resetDriverForm = () => {
  Object.assign(driverForm, {
    name: '', phone: '', email: '', card_id_number: '', card_id_url: '',
    employment_status: '', license_number: '', license_type: '', address: '', notes: ''
  })
}

const closeDriverModal = () => {
  showDriverModal.value = false
  cancelEditDriver()
}

const editDriver = (driver: any) => {
  editingDriver.value = driver
  Object.assign(driverForm, {
    name: driver.name || '',
    phone: driver.phone || '',
    email: driver.email || '',
    card_id_number: driver.card_id_number || '',
    card_id_url: driver.card_id_url || '',
    employment_status: driver.employment_status || '',
    license_number: driver.license_number || '',
    license_type: driver.license_type || '',
    address: driver.address || '',
    notes: driver.notes || ''
  })
}

const cancelEditDriver = () => {
  editingDriver.value = null
  resetDriverForm()
}

const validateDriverForm = () => {
  if (!driverForm.name) { toast.add({ title: 'Name is required', color: 'red' }); return false }
  if (!driverForm.phone) { toast.add({ title: 'Phone is required', color: 'red' }); return false }
  if (!driverForm.card_id_number) { toast.add({ title: 'Card ID Number is required', color: 'red' }); return false }
  if (!driverForm.employment_status) { toast.add({ title: 'Employment Status is required', color: 'red' }); return false }
  if (!driverForm.license_number) { toast.add({ title: 'License Number is required', color: 'red' }); return false }
  if (!driverForm.license_type) { toast.add({ title: 'License Type is required', color: 'red' }); return false }
  return true
}

const saveDriver = async () => {
  if (!validateDriverForm()) return
  
  savingDriver.value = true
  try {
    if (editingDriver.value) {
      await $api.put(`/fleet/drivers/${editingDriver.value.id}`, driverForm)
      toast.add({ title: 'Driver updated!' })
    } else {
      await $api.post('/fleet/drivers', driverForm)
      toast.add({ title: 'Driver added!' })
    }
    cancelEditDriver()
    fetchDrivers()
  } catch (e: any) { 
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save driver', color: 'red' }) 
  } finally {
    savingDriver.value = false
  }
}

const deleteDriver = async (driver: any) => {
  if (!confirm(`Delete driver "${driver.name}"?`)) return
  try {
    await $api.delete(`/fleet/drivers/${driver.id}`)
    toast.add({ title: 'Driver deleted!' })
    fetchDrivers()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

// ========== FILE UPLOAD ==========
const triggerFileUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) {
    await uploadFile(target.files[0])
  }
}

const handleFileDrop = async (event: DragEvent) => {
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    await uploadFile(file)
  }
}

const uploadFile = async (file: File) => {
  if (!file.type.startsWith('image/')) {
    toast.add({ title: 'Please upload an image file', color: 'red' })
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await $api.post('/upload/media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    driverForm.card_id_url = res.data.url
    toast.add({ title: 'Image uploaded successfully!' })
  } catch (e: any) {
    toast.add({ title: 'Upload failed', description: e.response?.data?.detail || 'Could not upload image', color: 'red' })
  } finally {
    uploading.value = false
  }
}

const getStatusColor = (s: string) => ({ PENDING: 'yellow', APPROVED: 'blue', REJECTED: 'red', IN_USE: 'green', COMPLETED: 'gray', CANCELLED: 'gray' })[s] || 'gray'
const getPurposeColor = (p: string) => ({ BUSINESS_TRIP: 'blue', DELIVERY: 'orange', CLIENT_VISIT: 'green', SITE_INSPECTION: 'purple' })[p] || 'gray'
const formatPurpose = (p: string) => ({ BUSINESS_TRIP: 'Business Trip', DELIVERY: 'Delivery', CLIENT_VISIT: 'Client Visit', SITE_INSPECTION: 'Site Inspection', PICKUP: 'Pickup', EVENT: 'Event', TRAINING: 'Training', OTHER: 'Other' })[p] || p
const formatDate = (dt: string) => dt ? new Date(dt).toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' }) : '-'

const exportData = (format: string) => {
  const data = bookings.value.map((b: any) => ({
    'Code': b.code || '',
    'Vehicle': getVehicleName(b.vehicle_id),
    'Purpose': formatPurpose(b.purpose),
    'Department': getDepartmentName(b.department_id),
    'Driver': getDriverName(b.driver_id),
    'Destination': b.destination || '',
    'Start': formatDate(b.start_datetime),
    'End': formatDate(b.end_datetime),
    'Status': b.status
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `bookings.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Bookings exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Bookings</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Vehicle Bookings Report</h1>
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

onMounted(() => {
  fetchBookings()
  fetchVehicles()
  fetchDepartments()
  fetchDrivers()
})
</script>
