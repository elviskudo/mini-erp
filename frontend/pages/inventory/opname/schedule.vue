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
      <UButton icon="i-heroicons-plus" @click="openCreateModal">New Schedule</UButton>
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
                 class="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center text-xs font-bold text-primary-700 border-2 border-white">
              {{ a.user?.username?.charAt(0)?.toUpperCase() || '?' }}
            </div>
            <span v-if="(row.assignments?.length || 0) > 3" class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs border-2 border-white">
              +{{ row.assignments.length - 3 }}
            </span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-play" size="xs" color="green" variant="ghost" @click="startOpname(row)" title="Start Opname" />
            <UButton icon="i-heroicons-printer" size="xs" color="gray" variant="ghost" @click="printSheet(row)" title="Print Count Sheet" />
            <UButton icon="i-heroicons-user-plus" size="xs" color="blue" variant="ghost" @click="assignTeam(row)" title="Assign Team" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="deleteSchedule(row)" title="Delete" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create Schedule Modal -->
    <UModal v-model="showCreateModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Create Opname Schedule</h3>
        </template>
        
        <form @submit.prevent="createSchedule" class="space-y-4">
          <UFormGroup label="Name" required>
            <UInput v-model="form.name" placeholder="e.g., Monthly Full Count" />
          </UFormGroup>
          
          <UFormGroup label="Warehouse" required>
            <USelect v-model="form.warehouse_id" :options="warehouses" option-attribute="name" value-attribute="id" placeholder="Select warehouse" />
          </UFormGroup>
          
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Frequency">
              <USelect v-model="form.frequency" :options="frequencyOptions" />
            </UFormGroup>
            <UFormGroup label="Scheduled Date" required>
              <UInput v-model="form.scheduled_date" type="datetime-local" />
            </UFormGroup>
          </div>
          
          <UFormGroup label="Description">
            <UTextarea v-model="form.description" rows="2" placeholder="Optional notes..." />
          </UFormGroup>
          
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showCreateModal = false">Cancel</UButton>
            <UButton type="submit" :loading="submitting">Create</UButton>
          </div>
        </form>
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
          
          <UFormGroup label="Add Team Member">
            <USelect v-model="assignForm.user_id" :options="users" option-attribute="username" value-attribute="id" placeholder="Select user" />
          </UFormGroup>
          
          <UFormGroup label="Role">
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

const schedules = ref<any[]>([])
const warehouses = ref<any[]>([])
const users = ref<any[]>([])
const selectedSchedule = ref<any>(null)

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

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [schedRes, whRes, userRes] = await Promise.all([
      $api.get('/opname/schedules'),
      $api.get('/inventory/warehouses'),
      $api.get('/users')
    ])
    schedules.value = schedRes.data || []
    warehouses.value = whRes.data || []
    users.value = userRes.data || []
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

const startOpname = async (schedule: any) => {
  if (!confirm('Start this opname now? This will create a snapshot of current stock.')) return
  
  try {
    const res = await $api.post('/opname/create', {
      warehouse_id: schedule.warehouse_id,
      schedule_id: schedule.id
    })
    toast.add({ title: 'Success', description: 'Opname created', color: 'green' })
    router.push(`/inventory/opname/counting?id=${res.data.id}`)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const printSheet = async (schedule: any) => {
  try {
    const res = await $api.get(`/opname/print-list/${schedule.warehouse_id}`)
    // Open print dialog with count sheet
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

const deleteSchedule = async (schedule: any) => {
  if (!confirm('Delete this schedule?')) return
  toast.add({ title: 'Info', description: 'Delete not implemented yet', color: 'blue' })
}

onMounted(() => {
  fetchData()
})
</script>
