<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Leave Management</h2>
        <p class="text-gray-500 text-sm">Manage leave requests and track balances</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton variant="soft" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" @click="openRequestForm">
          New Leave Request
        </UButton>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ pendingCount }}</p>
          <p class="text-sm text-gray-500">Pending</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ approvedCount }}</p>
          <p class="text-sm text-gray-500">Approved</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ rejectedCount }}</p>
          <p class="text-sm text-gray-500">Rejected</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ leaveTypes.length }}</p>
          <p class="text-sm text-gray-500">Leave Types</p>
        </div>
      </UCard>
    </div>

    <!-- Tabs -->
    <UTabs :items="tabs" v-model="activeTab">
      <template #default="{ item, selected }">
        <span :class="selected ? 'text-primary-600' : 'text-gray-500'">{{ item.label }}</span>
      </template>
    </UTabs>

    <!-- Leave Requests -->
    <UCard v-if="activeTab === 0">
      <template #header>
        <div class="flex items-center justify-between flex-wrap gap-4">
          <h3 class="font-semibold">Leave Requests</h3>
          <div class="flex gap-2">
            <USelect 
              v-model="filterStatus" 
              :options="['All', 'PENDING', 'APPROVED', 'REJECTED']"
              class="w-32"
            />
            <UButton variant="ghost" icon="i-heroicons-arrow-path" @click="fetchRequests" />
          </div>
        </div>
      </template>

      <UTable :columns="requestColumns" :rows="filteredRequests" :loading="loading">
        <template #employee_name-data="{ row }">
          <span class="font-medium">{{ row.employee_name || 'Unknown' }}</span>
        </template>
        
        <template #leave_type_name-data="{ row }">
          <UBadge variant="subtle">{{ row.leave_type_name }}</UBadge>
        </template>
        
        <template #dates-data="{ row }">
          {{ formatDate(row.start_date) }} - {{ formatDate(row.end_date) }}
          <span class="text-gray-500 text-xs block">{{ row.total_days }} days</span>
        </template>
        
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" size="sm">
            {{ row.status }}
          </UBadge>
        </template>
        
        <template #actions-data="{ row }">
          <div v-if="row.status === 'PENDING'" class="flex gap-1">
            <UButton 
              size="xs" 
              color="green" 
              variant="soft"
              icon="i-heroicons-check"
              @click="approveRequest(row)"
            />
            <UButton 
              size="xs" 
              color="red" 
              variant="soft"
              icon="i-heroicons-x-mark"
              @click="rejectRequest(row)"
            />
          </div>
          <span v-else class="text-gray-400 text-xs">-</span>
        </template>
      </UTable>
    </UCard>

    <!-- Leave Balances -->
    <UCard v-if="activeTab === 1">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Employee Leave Balances</h3>
          <USelect 
            v-model="selectedEmployeeForBalance" 
            :options="employeeOptions"
            placeholder="Select employee"
            class="w-64"
            @update:modelValue="fetchBalance"
          />
        </div>
      </template>

      <div v-if="!selectedEmployeeForBalance" class="text-center py-8 text-gray-500">
        Select an employee to view their leave balance
      </div>
      
      <div v-else-if="balances.length === 0" class="text-center py-8 text-gray-500">
        No leave balance records found
      </div>
      
      <div v-else class="space-y-4">
        <!-- Info Box -->
        <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-sm text-blue-700 dark:text-blue-300">
          <p><strong>How Leave Balance Works:</strong></p>
          <ul class="list-disc list-inside mt-1 space-y-1">
            <li>Each employee has a leave quota per leave type (annual, sick, etc.)</li>
            <li>When a leave request is <strong>approved</strong>, the days are automatically deducted from balance</li>
            <li>Remaining balance = Quota - Used days</li>
          </ul>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <UCard v-for="bal in balances" :key="bal.leave_type_id" :ui="{ body: { padding: 'p-4' } }">
            <h4 class="font-semibold mb-3">{{ bal.leave_type_name }}</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">Annual Quota</span>
                <span class="font-medium">{{ bal.quota }} days</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">Used</span>
                <span class="font-medium text-orange-600">{{ bal.used }} days</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">Remaining</span>
                <span class="font-medium text-green-600">{{ bal.remaining }} days</span>
              </div>
              <UProgress 
                :value="(bal.used / bal.quota) * 100" 
                :color="bal.remaining < 3 ? 'red' : 'green'"
                size="sm"
                class="mt-2"
              />
            </div>
          </UCard>
        </div>
      </div>
    </UCard>

    <!-- Leave Types -->
    <UCard v-if="activeTab === 2">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Leave Types</h3>
          <UButton size="sm" icon="i-heroicons-plus" @click="openLeaveTypeForm">
            Add Type
          </UButton>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <UCard v-for="lt in leaveTypes" :key="lt.id" :ui="{ body: { padding: 'p-4' } }">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div 
                class="w-4 h-4 rounded-full" 
                :style="{ backgroundColor: lt.color }"
              />
              <h4 class="font-semibold">{{ lt.name }}</h4>
            </div>
            <UDropdown :items="[[
              { label: 'Edit', icon: 'i-heroicons-pencil', click: () => editLeaveType(lt) },
              { label: 'Delete', icon: 'i-heroicons-trash', click: () => confirmDeleteLeaveType(lt) }
            ]]">
              <UButton variant="ghost" icon="i-heroicons-ellipsis-vertical" size="xs" />
            </UDropdown>
          </div>
          <div class="space-y-1 text-sm text-gray-500">
            <p>Code: {{ lt.code }}</p>
            <p>Annual Quota: {{ lt.annual_quota }} days</p>
            <div class="flex gap-2 mt-2">
              <UBadge :color="lt.is_paid ? 'green' : 'gray'" size="xs">
                {{ lt.is_paid ? 'Paid' : 'Unpaid' }}
              </UBadge>
              <UBadge v-if="lt.requires_document" color="yellow" size="xs">
                Requires Doc
              </UBadge>
            </div>
          </div>
        </UCard>
      </div>
    </UCard>

    <!-- New Leave Request Slideover -->
    <USlideover v-model="showRequestSlideover" :ui="{ width: 'max-w-md' }">
      <UCard class="h-full flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Submit Leave Request</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showRequestSlideover = false" />
          </div>
        </template>
        
        <div class="flex-1 overflow-y-auto space-y-4 p-1">
          <UFormGroup label="Employee" required>
            <USelectMenu 
              v-model="requestForm.employee_id" 
              :options="employees"
              searchable
              placeholder="Select employee"
              option-attribute="full_name"
              value-attribute="id"
            />
          </UFormGroup>
          
          <UFormGroup label="Leave Type" required>
            <USelect 
              v-model="requestForm.leave_type_id" 
              :options="leaveTypeOptions"
              option-attribute="label"
              value-attribute="value"
            />
          </UFormGroup>
          
          <!-- Show remaining balance -->
          <div v-if="selectedLeaveTypeBalance !== null" class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Remaining Balance</span>
              <span :class="selectedLeaveTypeBalance < 1 ? 'text-red-600 font-semibold' : 'text-green-600 font-semibold'">
                {{ selectedLeaveTypeBalance }} days
              </span>
            </div>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Start Date" required>
              <UInput v-model="requestForm.start_date" type="date" />
            </UFormGroup>
            <UFormGroup label="End Date" required>
              <UInput v-model="requestForm.end_date" type="date" />
            </UFormGroup>
          </div>
          
          <div v-if="calculatedDays > 0" class="text-sm text-gray-500">
            Total: <span class="font-semibold text-primary-600">{{ calculatedDays }} days</span>
          </div>
          
          <UFormGroup label="Reason">
            <UTextarea v-model="requestForm.reason" placeholder="Enter reason for leave..." rows="3" />
          </UFormGroup>
          
          <UFormGroup v-if="selectedLeaveTypeRequiresDoc" label="Supporting Document">
            <UInput type="file" @change="handleDocumentUpload" />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showRequestSlideover = false">Cancel</UButton>
            <UButton 
              @click="submitRequest" 
              :loading="submitting"
              :disabled="!isRequestFormValid"
            >
              Submit
            </UButton>
          </div>
        </template>
      </UCard>
    </USlideover>

    <!-- Rejection Modal -->
    <UModal v-model="showRejectModal">
      <UCard>
        <template #header>
          <h3 class="font-semibold">Reject Leave Request</h3>
        </template>
        <UFormGroup label="Rejection Reason">
          <UTextarea v-model="rejectionReason" placeholder="Enter reason for rejection..." />
        </UFormGroup>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showRejectModal = false">Cancel</UButton>
            <UButton color="red" @click="confirmReject" :loading="submitting">Reject</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Add/Edit Leave Type Slideover -->
    <USlideover v-model="showLeaveTypeSlideover" :ui="{ width: 'max-w-md' }">
      <UCard class="h-full flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{{ editingLeaveType ? 'Edit Leave Type' : 'Add Leave Type' }}</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showLeaveTypeSlideover = false" />
          </div>
        </template>
        
        <div class="flex-1 overflow-y-auto space-y-4 p-1">
          <UFormGroup label="Name" required>
            <UInput v-model="leaveTypeForm.name" placeholder="e.g. Annual Leave" />
          </UFormGroup>
          <UFormGroup label="Code" required>
            <UInput v-model="leaveTypeForm.code" placeholder="e.g. AL" />
          </UFormGroup>
          <UFormGroup label="Annual Quota (days)">
            <UInput v-model="leaveTypeForm.annual_quota" type="number" />
          </UFormGroup>
          <UFormGroup label="Color">
            <div class="flex gap-2">
              <UInput v-model="leaveTypeForm.color" type="color" class="w-16 h-10 p-1" />
              <UInput v-model="leaveTypeForm.color" placeholder="#3B82F6" class="flex-1" />
            </div>
          </UFormGroup>
          <UFormGroup label="Description">
            <UTextarea v-model="leaveTypeForm.description" placeholder="Describe this leave type..." rows="2" />
          </UFormGroup>
          <div class="space-y-3">
            <UCheckbox v-model="leaveTypeForm.is_paid" label="Paid Leave" />
            <UCheckbox v-model="leaveTypeForm.requires_document" label="Requires Supporting Document" />
            <UCheckbox v-model="leaveTypeForm.is_active" label="Active" />
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showLeaveTypeSlideover = false">Cancel</UButton>
            <UButton @click="saveLeaveType" :loading="submitting">Save</UButton>
          </div>
        </template>
      </UCard>
    </USlideover>

    <!-- Delete Leave Type Modal -->
    <UModal v-model="showDeleteLeaveTypeModal">
      <UCard>
        <template #header>
          <h3 class="font-semibold text-red-600">Delete Leave Type</h3>
        </template>
        <p>Are you sure you want to delete "{{ leaveTypeToDelete?.name }}"? This may affect existing leave records.</p>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDeleteLeaveTypeModal = false">Cancel</UButton>
            <UButton color="red" @click="deleteLeaveType" :loading="deletingLeaveType">Delete</UButton>
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

const tabs = [
  { label: 'Leave Requests', key: 'requests' },
  { label: 'Leave Balances', key: 'balances' },
  { label: 'Leave Types', key: 'types' }
]
const activeTab = ref(0)

const requests = ref<any[]>([])
const leaveTypes = ref<any[]>([])
const employees = ref<any[]>([])
const balances = ref<any[]>([])
const loading = ref(false)
const submitting = ref(false)
const filterStatus = ref('All')

const exportItems = [[
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') },
  { label: 'Export as XLS', icon: 'i-heroicons-table-cells', click: () => exportData('xls') },
  { label: 'Export as CSV', icon: 'i-heroicons-document-text', click: () => exportData('csv') }
]]

const exportData = (format: string) => {
  const url = `/api/hr/export/leave?format=${format}`
  window.open(url, '_blank')
}

const showRequestSlideover = ref(false)
const showRejectModal = ref(false)
const showLeaveTypeSlideover = ref(false)
const showDeleteLeaveTypeModal = ref(false)
const selectedRequest = ref<any>(null)
const rejectionReason = ref('')
const selectedEmployeeForBalance = ref<string | null>(null)
const editingLeaveType = ref<any>(null)
const leaveTypeToDelete = ref<any>(null)
const deletingLeaveType = ref(false)

const requestForm = ref({
  employee_id: '',
  leave_type_id: '',
  start_date: '',
  end_date: '',
  reason: '',
  document_url: ''
})

const leaveTypeForm = ref({
  name: '',
  code: '',
  annual_quota: 12,
  color: '#3B82F6',
  description: '',
  is_paid: true,
  requires_document: false,
  is_active: true
})

const requestColumns = [
  { key: 'employee_name', label: 'Employee' },
  { key: 'leave_type_name', label: 'Type' },
  { key: 'dates', label: 'Date Range' },
  { key: 'reason', label: 'Reason' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const pendingCount = computed(() => requests.value.filter(r => r.status === 'PENDING').length)
const approvedCount = computed(() => requests.value.filter(r => r.status === 'APPROVED').length)
const rejectedCount = computed(() => requests.value.filter(r => r.status === 'REJECTED').length)

const filteredRequests = computed(() => {
  if (filterStatus.value === 'All') return requests.value
  return requests.value.filter(r => r.status === filterStatus.value)
})

const employeeOptions = computed(() => 
  employees.value.map(e => ({
    label: `${e.first_name} ${e.last_name}`,
    value: e.id
  }))
)

const leaveTypeOptions = computed(() =>
  leaveTypes.value.map(lt => ({
    label: lt.name,
    value: lt.id
  }))
)

const selectedLeaveTypeBalance = computed(() => {
  if (!requestForm.value.employee_id || !requestForm.value.leave_type_id) return null
  const bal = balances.value.find(b => b.leave_type_id === requestForm.value.leave_type_id)
  return bal?.remaining ?? null
})

const selectedLeaveTypeRequiresDoc = computed(() => {
  if (!requestForm.value.leave_type_id) return false
  const lt = leaveTypes.value.find(t => t.id === requestForm.value.leave_type_id)
  return lt?.requires_document ?? false
})

const calculatedDays = computed(() => {
  if (!requestForm.value.start_date || !requestForm.value.end_date) return 0
  const start = new Date(requestForm.value.start_date)
  const end = new Date(requestForm.value.end_date)
  const diff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
  return Math.max(0, Math.floor(diff) + 1)
})

const isRequestFormValid = computed(() => 
  requestForm.value.employee_id &&
  requestForm.value.leave_type_id &&
  requestForm.value.start_date &&
  requestForm.value.end_date &&
  calculatedDays.value > 0
)

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'PENDING': 'yellow',
    'APPROVED': 'green',
    'REJECTED': 'red',
    'CANCELLED': 'gray'
  }
  return colors[status] || 'gray'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}

const fetchRequests = async () => {
  loading.value = true
  try {
    const res = await $api.get('/hr/leave/requests')
    requests.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchLeaveTypes = async () => {
  try {
    const res = await $api.get('/hr/leave-types')
    leaveTypes.value = res.data
  } catch (e) {
    console.error(e)
  }
}

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

const fetchBalance = async () => {
  if (!selectedEmployeeForBalance.value) return
  try {
    const res = await $api.get(`/hr/leave/balance/${selectedEmployeeForBalance.value}`)
    balances.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchBalanceForRequest = async () => {
  if (!requestForm.value.employee_id) return
  try {
    const res = await $api.get(`/hr/leave/balance/${requestForm.value.employee_id}`)
    balances.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const openRequestForm = () => {
  requestForm.value = { employee_id: '', leave_type_id: '', start_date: '', end_date: '', reason: '', document_url: '' }
  showRequestSlideover.value = true
}

const handleDocumentUpload = (event: any) => {
  // TODO: Implement document upload
  console.log('Document:', event.target.files[0])
}

const submitRequest = async () => {
  submitting.value = true
  try {
    await $api.post('/hr/leave/request', {
      leave_type_id: requestForm.value.leave_type_id,
      start_date: requestForm.value.start_date,
      end_date: requestForm.value.end_date,
      reason: requestForm.value.reason
    }, { params: { employee_id: requestForm.value.employee_id } })
    toast.add({ title: 'Success', description: 'Leave request submitted' })
    showRequestSlideover.value = false
    await fetchRequests()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to submit', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const approveRequest = async (request: any) => {
  submitting.value = true
  try {
    await $api.put(`/hr/leave/${request.id}/approve`, { approved: true })
    toast.add({ title: 'Success', description: 'Leave request approved. Balance deducted automatically.' })
    await fetchRequests()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to approve', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const rejectRequest = (request: any) => {
  selectedRequest.value = request
  rejectionReason.value = ''
  showRejectModal.value = true
}

const confirmReject = async () => {
  if (!selectedRequest.value) return
  submitting.value = true
  try {
    await $api.put(`/hr/leave/${selectedRequest.value.id}/approve`, {
      approved: false,
      rejection_reason: rejectionReason.value
    })
    toast.add({ title: 'Success', description: 'Leave request rejected' })
    showRejectModal.value = false
    await fetchRequests()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to reject', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const openLeaveTypeForm = () => {
  editingLeaveType.value = null
  leaveTypeForm.value = { name: '', code: '', annual_quota: 12, color: '#3B82F6', description: '', is_paid: true, requires_document: false, is_active: true }
  showLeaveTypeSlideover.value = true
}

const editLeaveType = (lt: any) => {
  editingLeaveType.value = lt
  leaveTypeForm.value = { ...lt }
  showLeaveTypeSlideover.value = true
}

const saveLeaveType = async () => {
  submitting.value = true
  try {
    if (editingLeaveType.value) {
      await $api.put(`/hr/leave-types/${editingLeaveType.value.id}`, leaveTypeForm.value)
      toast.add({ title: 'Success', description: 'Leave type updated' })
    } else {
      await $api.post('/hr/leave-types', leaveTypeForm.value)
      toast.add({ title: 'Success', description: 'Leave type created' })
    }
    showLeaveTypeSlideover.value = false
    await fetchLeaveTypes()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const confirmDeleteLeaveType = (lt: any) => {
  leaveTypeToDelete.value = lt
  showDeleteLeaveTypeModal.value = true
}

const deleteLeaveType = async () => {
  if (!leaveTypeToDelete.value) return
  deletingLeaveType.value = true
  try {
    await $api.delete(`/hr/leave-types/${leaveTypeToDelete.value.id}`)
    toast.add({ title: 'Success', description: 'Leave type deleted' })
    showDeleteLeaveTypeModal.value = false
    await fetchLeaveTypes()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to delete', color: 'red' })
  } finally {
    deletingLeaveType.value = false
  }
}

// Watch for employee change in request form to fetch balance
watch(() => requestForm.value.employee_id, fetchBalanceForRequest)

onMounted(() => {
  fetchRequests()
  fetchLeaveTypes()
  fetchEmployees()
})
</script>
