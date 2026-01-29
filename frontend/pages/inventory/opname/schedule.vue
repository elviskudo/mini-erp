<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/inventory/opname" />
        <div>
          <h2 class="text-xl font-bold">Opname Schedule</h2>
          <p class="text-gray-500">Plan and schedule stock opname events</p>
        </div>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreateModal">New Schedule</UButton>
      </div>
    </div>

    <!-- Schedule List -->
    <UCard>
      <DataTable
        :columns="columns"
        :rows="schedules"
        :loading="loading"
        searchable
        :search-keys="['name', 'warehouse.name']"
        empty-message="No schedules found"
      >
        <template #scheduled_date-data="{ row }">
          {{ formatDate(row.scheduled_date) }}
        </template>
        <template #warehouse-data="{ row }">
          {{ row.warehouse?.name || '-' }}
        </template>
        <template #frequency-data="{ row }">
          <UBadge variant="subtle" color="blue">{{ row.frequency }}</UBadge>
        </template>
        <template #team-data="{ row }">
          <div class="flex -space-x-2">
            <div v-for="a in (row.assignments || []).slice(0, 3)" :key="a.id" 
                 class="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center text-xs font-bold text-primary-700 border-2 border-white"
                 :title="a.user?.username">
              {{ a.user?.username?.charAt(0)?.toUpperCase() || '?' }}
            </div>
            <span v-if="(row.assignments?.length || 0) > 3" class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs border-2 border-white">
              +{{ row.assignments.length - 3 }}
            </span>
            <span v-if="!row.assignments?.length" class="text-xs text-gray-400">No team</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewSchedule(row)" title="View Details" />
            <UButton 
              icon="i-heroicons-play" 
              size="xs" 
              color="green" 
              variant="ghost" 
              :disabled="!row.assignments?.length"
              @click="openStartOpnameModal(row)" 
              :title="row.assignments?.length ? 'Start Opname' : 'Assign team first'" 
            />
            <UButton icon="i-heroicons-printer" size="xs" color="gray" variant="ghost" @click="printSheet(row)" title="Print Count Sheet" />
            <UButton icon="i-heroicons-user-plus" size="xs" color="blue" variant="ghost" @click="assignTeam(row)" title="Assign Team" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="openDeleteModal(row)" title="Delete" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- View Schedule Modal -->
    <UModal v-model="showViewModal" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedSchedule">
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">{{ selectedSchedule.name }}</h3>
            <UBadge variant="subtle" color="blue">{{ selectedSchedule.frequency }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500">Warehouse</p>
              <p class="font-medium">{{ selectedSchedule.warehouse?.name || '-' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Scheduled Date</p>
              <p class="font-medium">{{ formatDate(selectedSchedule.scheduled_date) }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Duration</p>
              <p class="font-medium">{{ selectedSchedule.estimated_duration_hours }} hours</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Status</p>
              <UBadge :color="selectedSchedule.is_active ? 'green' : 'gray'">
                {{ selectedSchedule.is_active ? 'Active' : 'Inactive' }}
              </UBadge>
            </div>
          </div>
          
          <div v-if="selectedSchedule.description">
            <p class="text-sm text-gray-500">Description</p>
            <p>{{ selectedSchedule.description }}</p>
          </div>
          
          <div>
            <p class="text-sm text-gray-500 mb-2">Assigned Team ({{ selectedSchedule.assignments?.length || 0 }})</p>
            <div v-if="selectedSchedule.assignments?.length" class="space-y-2">
              <div v-for="a in selectedSchedule.assignments" :key="a.id" class="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-sm font-bold text-primary-700">
                    {{ a.user?.username?.charAt(0)?.toUpperCase() || '?' }}
                  </div>
                  <span>{{ a.user?.username || 'Unknown' }}</span>
                </div>
                <UBadge variant="soft" :color="a.role === 'Supervisor' ? 'orange' : a.role === 'Approver' ? 'purple' : 'blue'">
                  {{ a.role }}
                </UBadge>
              </div>
            </div>
            <p v-else class="text-gray-400">No team assigned yet</p>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showViewModal = false">Close</UButton>
            <UButton color="blue" @click="assignTeam(selectedSchedule)">Assign Team</UButton>
            <UButton 
              color="green" 
              :disabled="!selectedSchedule.assignments?.length"
              @click="openStartOpnameModal(selectedSchedule)"
            >
              Start Opname
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Create Schedule Form Slideover -->
    <FormSlideover 
      v-model="showCreateModal" 
      title="Create Opname Schedule"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="createSchedule"
    >
      <div class="space-y-4">
        <UFormGroup label="Name" required hint="A descriptive name for this schedule" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g., Monthly Full Count" />
        </UFormGroup>
        
        <UFormGroup label="Warehouse" required hint="Select warehouse to count" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.warehouse_id" :options="warehouses" option-attribute="name" value-attribute="id" placeholder="Select warehouse" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Frequency" hint="How often this count repeats" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.frequency" :options="frequencyOptions" />
          </UFormGroup>
          <UFormGroup label="Scheduled Date" required hint="Target date and time" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.scheduled_date" type="datetime-local" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Description" hint="Additional notes or instructions" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" placeholder="Optional notes..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Start Opname Modal (SweetAlert style) -->
    <UModal v-model="showStartModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <UIcon name="i-heroicons-play" class="text-green-600 w-5 h-5" />
            </div>
            <div>
              <h3 class="text-lg font-semibold">Start Opname</h3>
              <p class="text-sm text-gray-500">{{ scheduleToStart?.name }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="p-3 bg-blue-50 rounded-lg text-sm">
            <p class="font-medium text-blue-800">📋 This will:</p>
            <ul class="mt-1 ml-4 list-disc text-blue-700">
              <li>Create a snapshot of current stock</li>
              <li>Notify {{ scheduleToStart?.assignments?.length || 0 }} team member(s)</li>
              <li>Start the counting session</li>
            </ul>
          </div>
          
          <UFormGroup label="Notes" hint="Add any special instructions for this opname session" :ui="{ hint: 'text-xs text-gray-400' }">
            <UTextarea v-model="startOpnameNotes" rows="3" placeholder="e.g., Focus on Zone A first, count high-value items twice..." />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showStartModal = false">Cancel</UButton>
            <UButton color="green" :loading="submitting" @click="confirmStartOpname">
              <UIcon name="i-heroicons-play" class="mr-1" /> Start Now
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Delete Confirmation Modal (SweetAlert style) -->
    <UModal v-model="showDeleteModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
              <UIcon name="i-heroicons-trash" class="text-red-600 w-5 h-5" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-red-600">Delete Schedule</h3>
              <p class="text-sm text-gray-500">This action cannot be undone</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-3">
          <p>Are you sure you want to delete <strong>"{{ scheduleToDelete?.name }}"</strong>?</p>
          
          <div class="p-3 bg-red-50 rounded-lg text-sm text-red-700">
            <p class="font-medium">⚠️ Warning:</p>
            <ul class="mt-1 ml-4 list-disc">
              <li>All team assignments will be removed</li>
              <li>This schedule cannot be recovered</li>
            </ul>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showDeleteModal = false">Cancel</UButton>
            <UButton color="red" :loading="submitting" @click="confirmDelete">
              <UIcon name="i-heroicons-trash" class="mr-1" /> Delete
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Assign Team Modal -->
    <UModal v-model="showAssignModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Assign Team</h3>
        </template>
        
        <div class="space-y-4">
          <div v-if="selectedSchedule?.assignments?.length" class="space-y-2">
            <p class="text-sm font-medium text-gray-700">Current Team:</p>
            <div v-for="a in selectedSchedule.assignments" :key="a.id" class="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span>{{ a.user?.username || 'Unknown' }} - {{ a.role }}</span>
            </div>
          </div>
          
          <UFormGroup label="Add Team Member" hint="Select user to assign" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="assignForm.user_id" :options="users" option-attribute="username" value-attribute="id" placeholder="Select user" />
          </UFormGroup>
          
          <UFormGroup label="Role" hint="Counter, Supervisor, or Approver" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="assignForm.role" :options="['Counter', 'Supervisor', 'Approver']" />
          </UFormGroup>
          
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showAssignModal = false">Close</UButton>
            <UButton @click="addTeamMember" :loading="submitting">Add Member</UButton>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const showCreateModal = ref(false)
const showAssignModal = ref(false)
const showStartModal = ref(false)
const showDeleteModal = ref(false)
const showViewModal = ref(false)

const schedules = ref<any[]>([])
const warehouses = ref<any[]>([])
const users = ref<any[]>([])
const selectedSchedule = ref<any>(null)
const scheduleToStart = ref<any>(null)
const scheduleToDelete = ref<any>(null)
const startOpnameNotes = ref('')

const frequencyOptions = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly', 'Ad-hoc']

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'scheduled_date', label: 'Scheduled Date', sortable: true },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'frequency', label: 'Frequency' },
  { key: 'team', label: 'Team' },
  { key: 'actions', label: '' }
]

const form = reactive({
  name: '',
  warehouse_id: '',
  frequency: 'Monthly',
  scheduled_date: '',
  description: ''
})

const assignForm = reactive({
  user_id: '',
  role: 'Counter'
})

const isFormValid = computed(() => {
  return form.name && form.warehouse_id && form.scheduled_date
})

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [schedRes, whRes, userRes] = await Promise.all([
      $api.get('/opname/schedule', { baseURL: '/api' }),
      $api.get('/inventory/warehouses'),
      $api.get('/users', { baseURL: '/api' })
    ])
    schedules.value = schedRes.data?.data || []
    warehouses.value = whRes.data?.data || []
    users.value = userRes.data?.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  Object.assign(form, { name: '', warehouse_id: '', frequency: 'Monthly', scheduled_date: '', description: '' })
  showCreateModal.value = true
}

const createSchedule = async () => {
  if (!form.name || !form.warehouse_id || !form.scheduled_date) {
    toast.add({ title: 'Error', description: 'Please fill required fields', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    await $api.post('/opname/schedule', {
      ...form,
      scheduled_date: new Date(form.scheduled_date).toISOString()
    })
    toast.add({ title: 'Success', description: 'Schedule created', color: 'green' })
    showCreateModal.value = false
    await fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const viewSchedule = (schedule: any) => {
  selectedSchedule.value = schedule
  showViewModal.value = true
}

const openStartOpnameModal = (schedule: any) => {
  if (!schedule.assignments?.length) {
    toast.add({ title: 'Warning', description: 'Please assign team members first', color: 'yellow' })
    return
  }
  scheduleToStart.value = schedule
  startOpnameNotes.value = ''
  showStartModal.value = true
}

const confirmStartOpname = async () => {
  if (!scheduleToStart.value) return
  
  submitting.value = true
  try {
    const res = await $api.post('/opname/create', {
      warehouse_id: scheduleToStart.value.warehouse_id,
      schedule_id: scheduleToStart.value.id,
      notes: startOpnameNotes.value || null
    })
    
    // Notify assigned users
    if (scheduleToStart.value.assignments?.length) {
      toast.add({ 
        title: 'Opname Started', 
        description: `Notification sent to ${scheduleToStart.value.assignments.length} team member(s)`, 
        color: 'green' 
      })
    }
    
    showStartModal.value = false
    showViewModal.value = false
    router.push(`/inventory/opname/counting?id=${res.data.id}`)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const openDeleteModal = (schedule: any) => {
  scheduleToDelete.value = schedule
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!scheduleToDelete.value) return
  
  submitting.value = true
  try {
    await $api.delete(`/opname/schedule/${scheduleToDelete.value.id}`)
    toast.add({ title: 'Deleted', description: 'Schedule removed successfully', color: 'green' })
    showDeleteModal.value = false
    await fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Delete failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const printSheet = async (schedule: any) => {
  try {
    const res = await $api.get(`/opname/print-list/${schedule.warehouse_id}`)
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Count Sheet - ${res.data.warehouse_name}</title>
        <style>
          body { font-family: Arial; padding: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background: #f4f4f4; }
          .count-box { width: 80px; height: 30px; border: 1px solid #333; }
        </style>
        </head><body>
        <h1>Stock Count Sheet</h1>
        <p><strong>Warehouse:</strong> ${res.data.warehouse_name}</p>
        <p><strong>Date:</strong> ${res.data.date}</p>
        <table>
          <thead>
            <tr><th>Code</th><th>Product</th><th>Location</th><th>System Qty</th><th>UoM</th><th>Counted Qty</th></tr>
          </thead>
          <tbody>
            ${res.data.items.map((i: any) => `
              <tr>
                <td>${i.product_code}</td>
                <td>${i.product_name}</td>
                <td>${i.location}</td>
                <td>${i.system_qty}</td>
                <td>${i.uom}</td>
                <td><div class="count-box"></div></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        </body></html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to generate count sheet', color: 'red' })
  }
}

const assignTeam = (schedule: any) => {
  selectedSchedule.value = schedule
  Object.assign(assignForm, { user_id: '', role: 'Counter' })
  showAssignModal.value = true
}

const addTeamMember = async () => {
  if (!assignForm.user_id) return
  
  submitting.value = true
  try {
    await $api.post('/opname/assign-team', {
      schedule_id: selectedSchedule.value.id,
      user_id: assignForm.user_id,
      role: assignForm.role
    })
    toast.add({ title: 'Success', description: 'Team member added', color: 'green' })
    showAssignModal.value = false
    await fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Export functions
const exportData = (format: string) => {
  const data = schedules.value.map((s: any) => ({
    'Name': s.name,
    'Warehouse': s.warehouse?.name || '-',
    'Scheduled Date': formatDate(s.scheduled_date),
    'Frequency': s.frequency,
    'Team Count': s.assignments?.length || 0
  }))
  
  if (format === 'csv') exportToCSV(data, 'opname_schedules')
  else if (format === 'xlsx') exportToXLSX(data, 'opname_schedules')
  else if (format === 'pdf') exportToPDF(data, 'Opname Schedules', 'opname_schedules')
}

const exportToCSV = (data: any[], filename: string) => {
  if (!data.length) return
  const headers = Object.keys(data[0])
  const csv = [headers.join(','), ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))].join('\n')
  downloadFile(new Blob([csv], { type: 'text/csv;charset=utf-8;' }), `${filename}.csv`)
}

const exportToXLSX = (data: any[], filename: string) => {
  if (!data.length) return
  const headers = Object.keys(data[0])
  const html = `<table><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>${data.map(row => `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`).join('')}</table>`
  downloadFile(new Blob([html], { type: 'application/vnd.ms-excel' }), `${filename}.xls`)
}

const exportToPDF = (data: any[], title: string, filename: string) => {
  if (!data.length) return
  const headers = Object.keys(data[0])
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`<html><head><title>${title}</title><style>body{font-family:Arial;padding:20px}table{width:100%;border-collapse:collapse;margin-top:20px}th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px}th{background:#f4f4f4}</style></head><body><h1>${title}</h1><p>Generated: ${new Date().toLocaleString()}</p><table><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>${data.map(row => `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`).join('')}</table></body></html>`)
    printWindow.document.close()
    printWindow.print()
  }
}

const downloadFile = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  fetchData()
})
</script>
