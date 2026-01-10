<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Employees</h2>
        <p class="text-gray-500">Manage employee records with photos, documents, and biometrics</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/hr">
          <UButton variant="ghost" icon="i-heroicons-arrow-left">Back</UButton>
        </NuxtLink>
        <UDropdown :items="exportItems">
          <UButton variant="soft" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Employee</UButton>
      </div>
    </div>

    <!-- Filters -->
    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex gap-4 flex-wrap">
        <UInput v-model="searchQuery" placeholder="Search name, email..." icon="i-heroicons-magnifying-glass" class="w-64" />
        <USelect v-model="filterDepartment" :options="departmentOptions" placeholder="All Departments" class="w-48" />
        <USelect v-model="filterStatus" :options="['All', 'ACTIVE', 'ON_LEAVE', 'TERMINATED']" class="w-36" />
        <UButton variant="ghost" icon="i-heroicons-arrow-path" @click="fetchEmployees" />
      </div>
    </UCard>

    <!-- Employees Table -->
    <UCard :ui="{ body: { padding: 'p-4' } }">
      <UTable :columns="columns" :rows="filteredEmployees" :loading="loading">
        <template #employee-data="{ row }">
          <div class="flex items-center gap-3">
            <img 
              v-if="row.profile_photo_url" 
              :src="row.profile_photo_url" 
              class="w-10 h-10 rounded-full object-cover"
            />
            <div v-else class="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
              <span class="text-primary-600 dark:text-primary-400 font-medium">
                {{ row.first_name?.[0] }}{{ row.last_name?.[0] }}
              </span>
            </div>
            <div>
              <p class="font-medium">{{ row.first_name }} {{ row.last_name }}</p>
              <p class="text-xs text-gray-500">{{ row.employee_code }}</p>
            </div>
          </div>
        </template>
        
        <template #position-data="{ row }">
          <p>{{ row.position_name || '-' }}</p>
          <p class="text-xs text-gray-500">{{ row.department_name || '-' }}</p>
        </template>
        
        <template #contact-data="{ row }">
          <p class="text-sm">{{ row.email }}</p>
          <p class="text-xs text-gray-500">{{ row.phone || '-' }}</p>
        </template>
        
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        
        <template #hire_date-data="{ row }">
          {{ formatDate(row.hire_date) }}
        </template>
        
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="viewEmployee(row)" />
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton 
              v-if="!row.face_encoding"
              icon="i-heroicons-finger-print" 
              color="green" 
              variant="ghost" 
              size="xs" 
              @click="openFaceRegistration(row)"
            />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Employee Detail Modal -->
    <UModal v-model="showDetailModal" :ui="{ width: 'max-w-4xl' }">
      <UCard v-if="selectedEmployee">
        <template #header>
          <div class="flex items-center gap-4">
            <img 
              v-if="selectedEmployee.profile_photo_url" 
              :src="selectedEmployee.profile_photo_url" 
              class="w-16 h-16 rounded-full object-cover"
            />
            <div v-else class="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
              <span class="text-primary-600 text-xl font-bold">
                {{ selectedEmployee.first_name?.[0] }}{{ selectedEmployee.last_name?.[0] }}
              </span>
            </div>
            <div>
              <h3 class="font-semibold text-lg">{{ selectedEmployee.first_name }} {{ selectedEmployee.last_name }}</h3>
              <p class="text-gray-500">{{ selectedEmployee.employee_code }}</p>
            </div>
          </div>
        </template>
        
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-4">
            <h4 class="font-semibold border-b pb-2">Personal Information</h4>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <span class="text-gray-500">Card ID</span><span>{{ selectedEmployee.card_id_number || '-' }}</span>
              <span class="text-gray-500">Gender</span><span>{{ selectedEmployee.gender || '-' }}</span>
              <span class="text-gray-500">Birth Date</span><span>{{ selectedEmployee.birth_date || '-' }}</span>
              <span class="text-gray-500">Marital Status</span><span>{{ selectedEmployee.marital_status || '-' }}</span>
              <span class="text-gray-500">Address</span><span>{{ selectedEmployee.address || '-' }}</span>
            </div>
          </div>
          <div class="space-y-4">
            <h4 class="font-semibold border-b pb-2">Employment</h4>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <span class="text-gray-500">Department</span><span>{{ selectedEmployee.department_name || '-' }}</span>
              <span class="text-gray-500">Position</span><span>{{ selectedEmployee.position_name || '-' }}</span>
              <span class="text-gray-500">Hire Date</span><span>{{ formatDate(selectedEmployee.hire_date) }}</span>
              <span class="text-gray-500">Contract Type</span><span>{{ selectedEmployee.contract_type || '-' }}</span>
              <span class="text-gray-500">Base Salary</span><span>{{ formatCurrency(selectedEmployee.base_salary) }}</span>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDetailModal = false">Close</UButton>
            <UButton @click="openEdit(selectedEmployee); showDetailModal = false">Edit</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Employee Form Slideover -->
    <FormSlideover
      v-model="isOpen"
      :title="editMode ? 'Edit Employee' : 'Add New Employee'"
      :loading="saving"
      @submit="onSubmit"
    >
      <div class="space-y-6">
        <!-- ID Card Capture Section -->
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <h4 class="font-medium text-sm mb-3 flex items-center gap-2">
            <UIcon name="i-heroicons-identification" class="w-4 h-4" />
            ID Card Capture (KTP)
          </h4>
          <div class="flex items-start gap-4">
            <div class="flex-1">
              <div v-if="!showIdCardCamera" class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                <img 
                  v-if="form.id_card_photo_url" 
                  :src="form.id_card_photo_url" 
                  class="w-full max-w-xs mx-auto rounded object-cover mb-2"
                />
                <div v-else class="w-full aspect-[1.6] max-w-xs mx-auto bg-gray-200 rounded flex items-center justify-center">
                  <UIcon name="i-heroicons-identification" class="w-12 h-12 text-gray-400" />
                </div>
                <UButton size="sm" icon="i-heroicons-camera" class="mt-3" @click="startIdCardCapture">
                  {{ form.id_card_photo_url ? 'Recapture' : 'Capture ID Card' }}
                </UButton>
              </div>
              <div v-else class="space-y-3">
                <div class="bg-gray-900 rounded-lg aspect-video overflow-hidden">
                  <video ref="idCardVideoRef" autoplay playsinline muted class="w-full h-full object-cover" />
                  <canvas ref="idCardCanvasRef" class="hidden" />
                </div>
                <div class="flex justify-center gap-2">
                  <UButton variant="ghost" @click="cancelIdCardCapture">Cancel</UButton>
                  <UButton icon="i-heroicons-camera" @click="captureIdCard" :loading="processingOcr">
                    {{ processingOcr ? 'Processing...' : 'Capture & Process' }}
                  </UButton>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Profile Photo Section -->
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0">
            <div class="relative">
              <div v-if="!showProfileCamera">
                <img 
                  v-if="form.profile_photo_url" 
                  :src="form.profile_photo_url" 
                  class="w-24 h-24 rounded-full object-cover"
                />
                <div v-else class="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center">
                  <UIcon name="i-heroicons-user" class="w-10 h-10 text-gray-400" />
                </div>
                <UButton 
                  size="xs" 
                  icon="i-heroicons-camera" 
                  class="absolute -bottom-1 -right-1"
                  @click="startProfileCapture"
                />
              </div>
              <div v-else class="space-y-2">
                <div class="w-32 h-32 bg-gray-900 rounded-lg overflow-hidden">
                  <video ref="profileVideoRef" autoplay playsinline muted class="w-full h-full object-cover" />
                  <canvas ref="profileCanvasRef" class="hidden" />
                </div>
                <div class="flex gap-1">
                  <UButton size="xs" variant="ghost" @click="cancelProfileCapture">Cancel</UButton>
                  <UButton size="xs" icon="i-heroicons-camera" @click="captureProfilePhoto">Capture</UButton>
                </div>
              </div>
            </div>
          </div>
          <div class="flex-1">
            <p class="font-medium">Profile Photo</p>
            <p class="text-xs text-gray-500">This photo will be used for face recognition attendance</p>
          </div>
        </div>
        
        <!-- Personal Info -->
        <div>
          <h4 class="font-medium text-sm text-gray-700 dark:text-gray-300 mb-3">Personal Information</h4>
          <div class="grid grid-cols-2 gap-3">
            <UFormGroup label="First Name" required :error="formSubmitted && !form.first_name ? 'Required' : ''">
              <UInput v-model="form.first_name" placeholder="e.g. John" />
            </UFormGroup>
            <UFormGroup label="Last Name" required :error="formSubmitted && !form.last_name ? 'Required' : ''">
              <UInput v-model="form.last_name" placeholder="e.g. Smith" />
            </UFormGroup>
            <UFormGroup label="Email" required :error="formSubmitted && !form.email ? 'Required' : ''">
              <UInput v-model="form.email" type="email" placeholder="john@company.com" />
            </UFormGroup>
            <UFormGroup label="Phone" required :error="formSubmitted && !form.phone ? 'Required' : ''">
              <UInput v-model="form.phone" placeholder="+62 812 3456 7890" />
            </UFormGroup>
            <UFormGroup label="Card ID Number (NIK)" required :error="formSubmitted && !form.card_id_number ? 'Required' : ''">
              <UInput v-model="form.card_id_number" placeholder="16 digit number" />
            </UFormGroup>
            <UFormGroup label="NPWP">
              <UInput v-model="form.npwp" placeholder="Tax ID Number" />
            </UFormGroup>
            <UFormGroup label="Birth Place">
              <UInput v-model="form.birth_place" placeholder="e.g. Jakarta" />
            </UFormGroup>
            <UFormGroup label="Birth Date">
              <UInput v-model="form.birth_date" type="date" />
            </UFormGroup>
            <UFormGroup label="Gender" required :error="formSubmitted && !form.gender ? 'Required' : ''">
              <USelect v-model="form.gender" :options="[
                { label: 'Male', value: 'MALE' },
                { label: 'Female', value: 'FEMALE' }
              ]" option-attribute="label" value-attribute="value" />
            </UFormGroup>
            <UFormGroup label="Marital Status">
              <USelect v-model="form.marital_status" :options="['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED']" />
            </UFormGroup>
            <UFormGroup label="Religion">
              <USelect v-model="form.religion" :options="['Islam', 'Kristen', 'Katolik', 'Hindu', 'Buddha', 'Konghucu', 'Other']" />
            </UFormGroup>
            <UFormGroup label="Blood Type">
              <USelect v-model="form.blood_type" :options="['A', 'B', 'AB', 'O', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']" placeholder="Select blood type" />
            </UFormGroup>
          </div>
          <UFormGroup label="Address" class="mt-3">
            <UTextarea v-model="form.address" placeholder="Full address" rows="2" />
          </UFormGroup>
          <div class="grid grid-cols-3 gap-3 mt-3">
            <UFormGroup label="City">
              <UInput v-model="form.city" placeholder="City" />
            </UFormGroup>
            <UFormGroup label="Province">
              <UInput v-model="form.province" placeholder="Province" />
            </UFormGroup>
            <UFormGroup label="Postal Code">
              <UInput v-model="form.postal_code" placeholder="e.g. 12345" />
            </UFormGroup>
          </div>
        </div>
            
        <!-- Employment -->
        <div>
          <h4 class="font-medium text-sm text-gray-700 dark:text-gray-300 mb-3">Employment</h4>
          <div class="grid grid-cols-2 gap-3">
            <UFormGroup label="Department" required :error="formSubmitted && !form.department_id ? 'Required' : ''">
              <USelect v-model="form.department_id" :options="departmentSelectOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
            <UFormGroup label="Position" required :error="formSubmitted && !form.position_id ? 'Required' : ''">
              <USelect v-model="form.position_id" :options="positionSelectOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
            <UFormGroup label="Hire Date" required :error="formSubmitted && !form.hire_date ? 'Required' : ''">
              <UInput v-model="form.hire_date" type="date" />
            </UFormGroup>
            <UFormGroup label="Contract Type" required :error="formSubmitted && !form.contract_type ? 'Required' : ''">
              <USelect v-model="form.contract_type" :options="['PERMANENT', 'CONTRACT', 'PROBATION', 'INTERNSHIP', 'PART_TIME']" />
            </UFormGroup>
            <UFormGroup label="Contract Start" required :error="formSubmitted && !form.contract_start ? 'Required' : ''">
              <UInput v-model="form.contract_start" type="date" />
            </UFormGroup>
            <UFormGroup label="Contract End" required :error="formSubmitted && !form.contract_end ? 'Required' : ''">
              <UInput v-model="form.contract_end" type="date" />
            </UFormGroup>
            <UFormGroup label="Base Salary (IDR)" required :error="formSubmitted && !form.base_salary ? 'Required' : ''">
              <UInput 
                :model-value="formatSalaryInput(form.base_salary)" 
                @update:model-value="form.base_salary = parseSalaryInput($event)"
                placeholder="e.g. 10,000,000"
              >
                <template #leading>
                  <span class="text-gray-500 text-sm">Rp</span>
                </template>
              </UInput>
            </UFormGroup>
            <UFormGroup label="Status" required :error="formSubmitted && !form.status ? 'Required' : ''">
              <USelect v-model="form.status" :options="['ACTIVE', 'INACTIVE', 'ON_LEAVE', 'TERMINATED', 'PROBATION']" />
            </UFormGroup>
          </div>
        </div>
            
        <!-- Bank & BPJS -->
        <div>
          <h4 class="font-medium text-sm text-gray-700 dark:text-gray-300 mb-3">Bank & Benefits</h4>
          <div class="grid grid-cols-2 gap-3">
            <UFormGroup label="Bank Name" required :error="formSubmitted && !form.bank_name ? 'Required' : ''">
              <USelect v-model="form.bank_name" :options="['BCA', 'BNI', 'BRI', 'Mandiri', 'CIMB Niaga', 'Danamon', 'Permata', 'Other']" />
            </UFormGroup>
            <UFormGroup label="Account Number" required :error="formSubmitted && !form.bank_account ? 'Required' : ''">
              <UInput v-model="form.bank_account" placeholder="Account number" />
            </UFormGroup>
            <UFormGroup label="Account Holder Name" required :error="formSubmitted && !form.account_name ? 'Required' : ''">
              <UInput v-model="form.account_name" placeholder="Account holder name" />
            </UFormGroup>
            <UFormGroup label="BPJS Kesehatan">
              <UInput v-model="form.bpjs_kesehatan" placeholder="BPJS Health number" />
            </UFormGroup>
            <UFormGroup label="BPJS Ketenagakerjaan" class="col-span-2 sm:col-span-1">
              <UInput v-model="form.bpjs_ketenagakerjaan" placeholder="BPJS TK number" />
            </UFormGroup>
          </div>
        </div>

        <!-- Emergency Contact -->
        <div>
          <h4 class="font-medium text-sm text-gray-700 dark:text-gray-300 mb-3">Emergency Contact</h4>
          <div class="grid grid-cols-2 gap-3">
            <UFormGroup label="Contact Name">
              <UInput v-model="form.emergency_contact_name" placeholder="e.g. Spouse/Parent name" />
            </UFormGroup>
            <UFormGroup label="Contact Phone">
              <UInput v-model="form.emergency_contact_phone" placeholder="Phone number" />
            </UFormGroup>
            <UFormGroup label="Relation" class="col-span-2 sm:col-span-1">
              <USelect v-model="form.emergency_contact_relation" :options="['Spouse', 'Parent', 'Sibling', 'Child', 'Other']" placeholder="Select relation" />
            </UFormGroup>
          </div>
        </div>
        <!-- Fingerprint Section -->
        <div>
          <h4 class="font-medium text-sm text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <UIcon name="i-heroicons-finger-print" class="w-4 h-4" />
            Fingerprint Registration
          </h4>
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div v-if="form.fingerprint_id" class="flex items-center gap-3">
              <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-green-500" />
              <span class="text-sm">Fingerprint registered</span>
              <UButton size="xs" variant="soft" @click="registerFingerprint">Re-register</UButton>
            </div>
            <div v-else class="text-center">
              <p class="text-sm text-gray-500 mb-3">Register fingerprint for attendance</p>
              <UButton icon="i-heroicons-finger-print" @click="registerFingerprint" :loading="registeringFingerprint">
                Register Fingerprint
              </UButton>
            </div>
          </div>
        </div>
      </div>
    </FormSlideover>


    <!-- Face Registration Modal -->
    <UModal v-model="showFaceModal">
      <UCard>
        <template #header>
          <h3 class="font-semibold">Register Face - {{ faceRegistrationEmployee?.first_name }}</h3>
        </template>
        <div class="space-y-4">
          <p class="text-sm text-gray-500">Position your face in the center of the camera to register for attendance.</p>
          <div class="bg-gray-900 rounded-lg aspect-video overflow-hidden">
            <video ref="faceVideoRef" autoplay playsinline muted class="w-full h-full object-cover" />
            <canvas ref="faceCanvasRef" class="hidden" />
          </div>
          <div v-if="!faceCameraActive" class="text-center">
            <UButton @click="startFaceCamera">Start Camera</UButton>
          </div>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="closeFaceModal">Cancel</UButton>
            <UButton 
              @click="registerFace" 
              :loading="registeringFace"
              :disabled="!faceCameraActive"
              color="green"
              icon="i-heroicons-finger-print"
            >
              Register Face
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const editMode = ref(false)
const employees = ref<any[]>([])
const departments = ref<any[]>([])
const positions = ref<any[]>([])
const formSubmitted = ref(false)

const searchQuery = ref('')
const filterDepartment = ref('')
const filterStatus = ref('All')

const showDetailModal = ref(false)
const selectedEmployee = ref<any>(null)

// Profile photo capture (inline)
const showProfileCamera = ref(false)
const profileVideoRef = ref<HTMLVideoElement | null>(null)
const profileCanvasRef = ref<HTMLCanvasElement | null>(null)
let profileStream: MediaStream | null = null

// ID Card capture (inline with OCR)
const showIdCardCamera = ref(false)
const idCardVideoRef = ref<HTMLVideoElement | null>(null)
const idCardCanvasRef = ref<HTMLCanvasElement | null>(null)
let idCardStream: MediaStream | null = null
const processingOcr = ref(false)

// Face registration
const showFaceModal = ref(false)
const faceVideoRef = ref<HTMLVideoElement | null>(null)
const faceCanvasRef = ref<HTMLCanvasElement | null>(null)
let faceStream: MediaStream | null = null
const faceCameraActive = ref(false)
const registeringFace = ref(false)
const faceRegistrationEmployee = ref<any>(null)

// Fingerprint
const registeringFingerprint = ref(false)

// Export items
const exportItems = [
  [{
    label: 'Export as PDF',
    icon: 'i-heroicons-document',
    click: () => exportData('pdf')
  }],
  [{
    label: 'Export as Excel',
    icon: 'i-heroicons-table-cells',
    click: () => exportData('xlsx')
  }],
  [{
    label: 'Export as CSV',
    icon: 'i-heroicons-document-text',
    click: () => exportData('csv')
  }]
]

const form = reactive({
  id: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  card_id_number: '',
  npwp: '',
  birth_date: '',
  birth_place: '',
  gender: '',
  marital_status: '',
  religion: '',
  blood_type: '',
  address: '',
  city: '',
  province: '',
  postal_code: '',
  department_id: '',
  position_id: '',
  hire_date: new Date().toISOString().split('T')[0],
  contract_type: 'PERMANENT',
  contract_start: '',
  contract_end: '',
  base_salary: 5000000,
  status: 'ACTIVE',
  bank_name: '',
  bank_account: '',
  account_name: '',
  bpjs_kesehatan: '',
  bpjs_ketenagakerjaan: '',
  profile_photo_url: '',
  id_card_photo_url: '',
  fingerprint_id: '',
  emergency_contact_name: '',
  emergency_contact_phone: '',
  emergency_contact_relation: ''
})

const columns = [
  { key: 'employee', label: 'Employee' },
  { key: 'position', label: 'Position' },
  { key: 'contact', label: 'Contact' },
  { key: 'hire_date', label: 'Hire Date' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const isFormValid = computed(() => 
  form.first_name.trim() !== '' && 
  form.last_name.trim() !== '' && 
  form.email.trim() !== '' &&
  form.phone.trim() !== '' &&
  form.card_id_number.trim() !== '' &&
  form.gender !== '' &&
  form.department_id !== '' &&
  form.position_id !== '' &&
  form.hire_date !== '' &&
  form.contract_type !== '' &&
  form.contract_start !== '' &&
  form.contract_end !== '' &&
  form.status !== '' &&
  form.bank_name !== '' &&
  form.bank_account.trim() !== '' &&
  form.account_name.trim() !== ''
)

const filteredEmployees = computed(() => {
  let result = employees.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e => 
      e.first_name?.toLowerCase().includes(q) ||
      e.last_name?.toLowerCase().includes(q) ||
      e.email?.toLowerCase().includes(q) ||
      e.employee_code?.toLowerCase().includes(q)
    )
  }
  if (filterDepartment.value) {
    result = result.filter(e => e.department_id === filterDepartment.value)
  }
  if (filterStatus.value !== 'All') {
    result = result.filter(e => e.status === filterStatus.value)
  }
  return result
})

const departmentOptions = computed(() => [
  { label: 'All Departments', value: '' },
  ...departments.value.map(d => ({ label: d.name, value: d.id }))
])

const departmentSelectOptions = computed(() => 
  departments.value.map(d => ({ label: d.name, value: d.id }))
)

const positionSelectOptions = computed(() =>
  positions.value.map(p => ({ label: p.name, value: p.id }))
)

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'ACTIVE': 'green',
    'INACTIVE': 'gray',
    'ON_LEAVE': 'blue',
    'TERMINATED': 'red',
    'PROBATION': 'yellow'
  }
  return colors[status] || 'gray'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(amount || 0)
}

const formatSalaryInput = (value: number) => {
  if (!value) return ''
  return new Intl.NumberFormat('id-ID').format(value)
}

const parseSalaryInput = (value: string) => {
  const num = parseInt(value.replace(/\D/g, ''), 10)
  return isNaN(num) ? 0 : num
}

const fetchEmployees = async () => {
  loading.value = true
  try {
    const res = await $api.get('/hr/employees')
    employees.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchDepartments = async () => {
  try {
    const res = await $api.get('/hr/departments')
    departments.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchPositions = async () => {
  try {
    const res = await $api.get('/hr/positions')
    positions.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const exportData = async (format: string) => {
  try {
    const res = await $api.get(`/export/employees`, {
      params: { format },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `employees.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast.add({ title: 'Success', description: `Exported as ${format.toUpperCase()}` })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Export failed', color: 'red' })
  }
}

const resetForm = () => {
  formSubmitted.value = false
  Object.assign(form, {
    id: '', first_name: '', last_name: '', email: '', phone: '',
    card_id_number: '', npwp: '', birth_date: '', birth_place: '',
    gender: '', marital_status: '', religion: '', blood_type: '',
    address: '', city: '', province: '', postal_code: '',
    department_id: '', position_id: '',
    hire_date: new Date().toISOString().split('T')[0],
    contract_type: 'PERMANENT', contract_start: '', contract_end: '',
    base_salary: 5000000, status: 'ACTIVE', bank_name: '', bank_account: '',
    account_name: '', bpjs_kesehatan: '', bpjs_ketenagakerjaan: '',
    profile_photo_url: '', id_card_photo_url: '', fingerprint_id: '',
    emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relation: ''
  })
}

const openCreate = () => {
  resetForm()
  editMode.value = false
  isOpen.value = true
}

const openEdit = async (row: any) => {
  formSubmitted.value = false
  loading.value = true
  try {
    // Fetch full employee details from API
    const res = await $api.get(`/hr/employees/${row.id}`)
    const emp = res.data
    
    Object.assign(form, {
      id: emp.id,
      first_name: emp.first_name || '',
      last_name: emp.last_name || '',
      email: emp.email || '',
      phone: emp.phone || '',
      card_id_number: emp.nik || '',
      npwp: emp.npwp || '',
      birth_date: emp.birth_date || '',
      birth_place: emp.birth_place || '',
      gender: emp.gender || '',
      marital_status: emp.marital_status || '',
      religion: emp.religion || '',
      blood_type: emp.blood_type || '',
      address: emp.address || '',
      city: emp.city || '',
      province: emp.province || '',
      postal_code: emp.postal_code || '',
      department_id: emp.department_id || '',
      position_id: emp.position_id || '',
      hire_date: emp.hire_date || '',
      contract_type: emp.contract_type || 'PERMANENT',
      contract_start: emp.contract_start || '',
      contract_end: emp.contract_end || '',
      base_salary: emp.base_salary || 0,
      status: emp.status || 'ACTIVE',
      bank_name: emp.bank_name || '',
      bank_account: emp.bank_account || '',
      account_name: emp.bank_account_name || '',
      bpjs_kesehatan: emp.bpjs_kesehatan || '',
      bpjs_ketenagakerjaan: emp.bpjs_ketenagakerjaan || '',
      profile_photo_url: emp.profile_photo_url || '',
      id_card_photo_url: emp.id_card_photo_url || '',
      fingerprint_id: emp.fingerprint_id || '',
      emergency_contact_name: emp.emergency_contact_name || '',
      emergency_contact_phone: emp.emergency_contact_phone || '',
      emergency_contact_relation: emp.emergency_contact_relation || ''
    })
    editMode.value = true
    isOpen.value = true
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Error', description: 'Failed to load employee details', color: 'red' })
  } finally {
    loading.value = false
  }
}

const viewEmployee = (row: any) => {
  selectedEmployee.value = row
  showDetailModal.value = true
}

const onSubmit = async () => {
  formSubmitted.value = true
  if (!isFormValid.value) {
    toast.add({ title: 'Error', description: 'Please fill all required fields', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    // Map frontend fields to backend schema
    const payload = {
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
      phone: form.phone || null,
      nik: form.card_id_number || null,
      npwp: form.npwp || null,
      birth_date: form.birth_date || null,
      birth_place: form.birth_place || null,
      gender: form.gender || null,
      marital_status: form.marital_status || null,
      religion: form.religion || null,
      blood_type: form.blood_type || null,
      address: form.address || null,
      city: form.city || null,
      province: form.province || null,
      postal_code: form.postal_code || null,
      department_id: form.department_id || null,
      position_id: form.position_id || null,
      hire_date: form.hire_date,
      contract_type: form.contract_type,
      contract_start: form.contract_start || null,
      contract_end: form.contract_end || null,
      base_salary: form.base_salary || 0,
      status: form.status || 'ACTIVE',
      bank_name: form.bank_name || null,
      bank_account: form.bank_account || null,
      bank_account_name: form.account_name || null,
      bpjs_kesehatan: form.bpjs_kesehatan || null,
      bpjs_ketenagakerjaan: form.bpjs_ketenagakerjaan || null,
      emergency_contact_name: form.emergency_contact_name || null,
      emergency_contact_phone: form.emergency_contact_phone || null,
      emergency_contact_relation: form.emergency_contact_relation || null
    }
    
    if (editMode.value) {
      await $api.put(`/hr/employees/${form.id}`, payload)
      toast.add({ title: 'Success', description: 'Employee updated successfully', color: 'green' })
    } else {
      const res = await $api.post('/hr/employees', payload)
      const newEmployeeId = res.data.id
      
      // Upload ID card photo if captured (data URL starts with 'data:')
      if (form.id_card_photo_url && form.id_card_photo_url.startsWith('data:')) {
        try {
          const imageBase64 = form.id_card_photo_url.split(',')[1]
          const formData = new FormData()
          formData.append('photo_type', 'id_card')
          formData.append('image_base64', imageBase64)
          await $api.post(`/hr/employees/${newEmployeeId}/upload-photo`, formData)
        } catch (e) {
          console.error('ID card upload error:', e)
        }
      }
      
      // Upload profile photo if captured
      if (form.profile_photo_url && form.profile_photo_url.startsWith('data:')) {
        try {
          const imageBase64 = form.profile_photo_url.split(',')[1]
          const formData = new FormData()
          formData.append('photo_type', 'profile')
          formData.append('image_base64', imageBase64)
          await $api.post(`/hr/employees/${newEmployeeId}/upload-photo`, formData)
        } catch (e) {
          console.error('Profile photo upload error:', e)
        }
      }
      
      toast.add({ title: 'Success', description: 'Employee created successfully', color: 'green' })
    }
    isOpen.value = false
    fetchEmployees()
    resetForm()
  } catch (e: any) {
    console.error('Save error:', e)
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save employee', color: 'red' })
  } finally {
    saving.value = false
  }
}

// Profile photo inline capture
const startProfileCapture = async () => {
  showProfileCamera.value = true
  await nextTick()
  try {
    profileStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
    if (profileVideoRef.value) {
      profileVideoRef.value.srcObject = profileStream
    }
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Error', description: 'Camera access denied', color: 'red' })
    showProfileCamera.value = false
  }
}

const captureProfilePhoto = async () => {
  if (!profileVideoRef.value || !profileCanvasRef.value) return
  
  const canvas = profileCanvasRef.value
  const video = profileVideoRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0)
  
  const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
  form.profile_photo_url = dataUrl
  
  // If editing, upload to server
  if (editMode.value && form.id) {
    try {
      const base64 = dataUrl.split(',')[1]
      const formData = new FormData()
      formData.append('photo_type', 'profile')
      formData.append('image_base64', base64)
      const res = await $api.post(`/hr/employees/${form.id}/upload-photo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      form.profile_photo_url = res.data.url
    } catch (e) {
      console.error(e)
    }
  }
  
  cancelProfileCapture()
}

const cancelProfileCapture = () => {
  if (profileStream) {
    profileStream.getTracks().forEach(t => t.stop())
    profileStream = null
  }
  showProfileCamera.value = false
}

// ID Card capture with OCR
const startIdCardCapture = async () => {
  showIdCardCamera.value = true
  await nextTick()
  try {
    idCardStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: 1280, height: 720 } })
    if (idCardVideoRef.value) {
      idCardVideoRef.value.srcObject = idCardStream
    }
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Error', description: 'Camera access denied', color: 'red' })
    showIdCardCamera.value = false
  }
}

const captureIdCard = async () => {
  if (!idCardVideoRef.value || !idCardCanvasRef.value) return
  
  const canvas = idCardCanvasRef.value
  const video = idCardVideoRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0)
  
  const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
  const imageBase64 = dataUrl.split(',')[1]
  
  // Set the captured image immediately for preview
  form.id_card_photo_url = dataUrl
  
  // If editing existing employee, upload to server immediately
  if (editMode.value && form.id) {
    processingOcr.value = true
    try {
      const formData = new FormData()
      formData.append('photo_type', 'id_card')
      formData.append('image_base64', imageBase64)
      
      const res = await $api.post(`/hr/employees/${form.id}/upload-photo`, formData)
      if (res.data.url) {
        form.id_card_photo_url = res.data.url
      }
      toast.add({ title: 'Success', description: 'ID Card captured and saved', color: 'green' })
    } catch (e) {
      console.error('Upload error:', e)
      toast.add({ title: 'Info', description: 'ID Card captured. Will be saved when you save the form.', color: 'yellow' })
    } finally {
      processingOcr.value = false
    }
  } else {
    toast.add({ title: 'Success', description: 'ID Card captured. Will be saved when you save the employee.', color: 'green' })
  }
  
  cancelIdCardCapture()
}

const cancelIdCardCapture = () => {
  if (idCardStream) {
    idCardStream.getTracks().forEach(t => t.stop())
    idCardStream = null
  }
  showIdCardCamera.value = false
}

// Fingerprint registration using FingerprintJS
const registerFingerprint = async () => {
  registeringFingerprint.value = true
  try {
    // Dynamic import FingerprintJS
    const FingerprintJS = await import('@fingerprintjs/fingerprintjs')
    const fp = await FingerprintJS.load()
    const result = await fp.get()
    
    form.fingerprint_id = result.visitorId
    toast.add({ title: 'Success', description: 'Fingerprint registered successfully' })
  } catch (e) {
    console.error('Fingerprint error:', e)
    toast.add({ title: 'Error', description: 'Failed to register fingerprint', color: 'red' })
  } finally {
    registeringFingerprint.value = false
  }
}

// Face registration
const openFaceRegistration = (employee: any) => {
  faceRegistrationEmployee.value = employee
  showFaceModal.value = true
}

const startFaceCamera = async () => {
  try {
    faceStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
    if (faceVideoRef.value) {
      faceVideoRef.value.srcObject = faceStream
    }
    faceCameraActive.value = true
  } catch (e) {
    console.error(e)
  }
}

const registerFace = async () => {
  if (!faceVideoRef.value || !faceCanvasRef.value || !faceRegistrationEmployee.value) return
  
  const canvas = faceCanvasRef.value
  const video = faceVideoRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0)
  
  const base64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1]
  
  registeringFace.value = true
  try {
    await $api.post(`/hr/employees/${faceRegistrationEmployee.value.id}/register-face`, {
      face_image_base64: base64
    })
    toast.add({ title: 'Success', description: 'Face registered successfully!' })
    closeFaceModal()
    fetchEmployees()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to register face', color: 'red' })
  } finally {
    registeringFace.value = false
  }
}

const closeFaceModal = () => {
  if (faceStream) {
    faceStream.getTracks().forEach(t => t.stop())
    faceStream = null
  }
  faceCameraActive.value = false
  showFaceModal.value = false
  faceRegistrationEmployee.value = null
}

onMounted(() => {
  fetchEmployees()
  fetchDepartments()
  fetchPositions()
})

onUnmounted(() => {
  if (profileStream) profileStream.getTracks().forEach(t => t.stop())
  if (idCardStream) idCardStream.getTracks().forEach(t => t.stop())
  if (faceStream) faceStream.getTracks().forEach(t => t.stop())
})
</script>
