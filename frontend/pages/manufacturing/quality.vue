<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Quality Control</h2>
        <p class="text-gray-500">Inspect and verify production quality</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New QC Check</UButton>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ stats.total }}</p>
          <p class="text-sm text-gray-500">Total Checks</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.passed }}</p>
          <p class="text-sm text-gray-500">Passed</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ stats.failed }}</p>
          <p class="text-sm text-gray-500">Failed</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ stats.pass_rate }}%</p>
          <p class="text-sm text-gray-500">Pass Rate</p>
        </div>
      </UCard>
    </div>

    <!-- QC List -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span>Quality Checks</span>
          <USelect v-model="statusFilter" :options="statusOptions" placeholder="All Statuses" class="w-40" size="sm" />
        </div>
      </template>
      <DataTable 
        :columns="columns" 
        :rows="filteredChecks" 
        :loading="loading"
        searchable
        :search-keys="['qc_number', 'product_name']"
        empty-message="No quality checks yet"
      >
        <template #qc_number-data="{ row }">
          <span class="font-mono">{{ row.qc_number }}</span>
        </template>
        <template #product_name-data="{ row }">
          {{ row.product_name || 'Unknown' }}
        </template>
        <template #check_date-data="{ row }">
          {{ formatDate(row.check_date) }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #quantities-data="{ row }">
          <div class="text-sm">
            <span class="text-green-600">{{ row.passed_qty }}</span> / 
            <span class="text-gray-600">{{ row.inspected_qty }}</span>
            <span v-if="row.failed_qty > 0" class="text-red-600 ml-1">({{ row.failed_qty }} failed)</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status === 'Pending'" icon="i-heroicons-check" size="xs" color="green" @click="openExecute(row)" title="Execute QC" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create QC Modal -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit QC Check' : 'New Quality Check'"
      :loading="submitting"
      :disabled="!form.product_id"
      @submit="save"
    >
      <div class="space-y-4">
        <UFormGroup label="Product" required>
          <USelect v-model="form.product_id" :options="productOptions" placeholder="Select product" />
        </UFormGroup>
        
        <UFormGroup label="Production Order" hint="Optional - link to production order" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.production_order_id" :options="productionOrderOptions" placeholder="None (standalone check)" />
        </UFormGroup>
        
        <UFormGroup label="Quantity to Inspect" required>
          <UInput v-model.number="form.inspected_qty" type="number" placeholder="0" />
        </UFormGroup>
        
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="2" placeholder="Quality check notes..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Execute QC Modal -->
    <UModal v-model="showExecuteModal" :ui="{ width: 'max-w-xl' }">
      <UCard v-if="selectedCheck">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <UIcon name="i-heroicons-clipboard-document-check" class="text-blue-600 w-6 h-6" />
            </div>
            <div>
              <h3 class="text-lg font-semibold">Execute Quality Check</h3>
              <p class="text-sm text-gray-500">{{ selectedCheck.qc_number }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="p-3 bg-gray-50 rounded-lg">
            <p class="font-medium">{{ selectedCheck.product_name }}</p>
            <p class="text-sm text-gray-500">Inspecting {{ selectedCheck.inspected_qty }} units</p>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="✅ Passed Quantity" required>
              <UInput v-model.number="executeForm.passed_qty" type="number" class="border-green-300" />
            </UFormGroup>
            <UFormGroup label="❌ Failed Quantity">
              <UInput v-model.number="executeForm.failed_qty" type="number" class="border-red-300" />
            </UFormGroup>
          </div>
          
          <div v-if="executeForm.failed_qty > 0" class="p-3 bg-red-50 rounded-lg">
            <UFormGroup label="Defect Types">
              <UInput v-model="executeForm.defect_types" placeholder="e.g. Scratch, Dent, Color mismatch" />
            </UFormGroup>
          </div>
          
          <UFormGroup label="Inspector Notes">
            <UTextarea v-model="executeForm.notes" rows="2" placeholder="Observations..." />
          </UFormGroup>
          
          <div class="p-3 rounded-lg" :class="qcResultStatus === 'Passed' ? 'bg-green-50' : qcResultStatus === 'Failed' ? 'bg-red-50' : 'bg-yellow-50'">
            <p class="font-medium" :class="qcResultStatus === 'Passed' ? 'text-green-700' : qcResultStatus === 'Failed' ? 'text-red-700' : 'text-yellow-700'">
              Result: {{ qcResultStatus }}
            </p>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showExecuteModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="submitQCResult" :color="qcResultStatus === 'Passed' ? 'green' : 'red'">
              Submit Result
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Detail Modal -->
    <UModal v-model="showDetailsModal">
      <UCard v-if="selectedCheck">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedCheck.qc_number }}</h3>
              <p class="text-sm text-gray-500">{{ selectedCheck.product_name }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedCheck.status)" size="lg">{{ selectedCheck.status }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-3 bg-gray-50 rounded">
              <p class="text-lg font-bold">{{ selectedCheck.inspected_qty }}</p>
              <p class="text-xs text-gray-500">Inspected</p>
            </div>
            <div class="p-3 bg-green-50 rounded">
              <p class="text-lg font-bold text-green-600">{{ selectedCheck.passed_qty }}</p>
              <p class="text-xs text-gray-500">Passed</p>
            </div>
            <div class="p-3 bg-red-50 rounded">
              <p class="text-lg font-bold text-red-600">{{ selectedCheck.failed_qty }}</p>
              <p class="text-xs text-gray-500">Failed</p>
            </div>
          </div>
          
          <div v-if="selectedCheck.notes" class="p-3 bg-gray-50 rounded">
            <p class="text-sm font-medium mb-1">Notes:</p>
            <p class="text-sm text-gray-600">{{ selectedCheck.notes }}</p>
          </div>
          
          <div v-if="selectedCheck.defect_types" class="p-3 bg-red-50 rounded">
            <p class="text-sm font-medium mb-1 text-red-700">Defects:</p>
            <p class="text-sm text-red-600">{{ selectedCheck.defect_types }}</p>
          </div>
        </div>
        
        <template #footer>
          <UButton variant="ghost" @click="showDetailsModal = false">Close</UButton>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)
const editMode = ref(false)
const showExecuteModal = ref(false)
const showDetailsModal = ref(false)
const statusFilter = ref('')

const checks = ref<any[]>([])
const products = ref<any[]>([])
const productionOrders = ref<any[]>([])
const selectedCheck = ref<any>(null)

const columns = [
  { key: 'qc_number', label: 'QC Number', sortable: true },
  { key: 'product_name', label: 'Product' },
  { key: 'check_date', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'quantities', label: 'Passed/Total' },
  { key: 'actions', label: '' }
]

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'Pending' },
  { label: 'Passed', value: 'Passed' },
  { label: 'Failed', value: 'Failed' },
  { label: 'Partial Pass', value: 'Partial Pass' }
]

const form = reactive({
  product_id: '',
  production_order_id: '',
  inspected_qty: 0,
  notes: ''
})

const executeForm = reactive({
  passed_qty: 0,
  failed_qty: 0,
  defect_types: '',
  notes: ''
})

const stats = computed(() => {
  const total = checks.value.length
  const passed = checks.value.filter(c => c.status === 'Passed').length
  const failed = checks.value.filter(c => c.status === 'Failed').length
  return {
    total,
    passed,
    failed,
    pass_rate: total > 0 ? Math.round((passed / total) * 100) : 0
  }
})

const filteredChecks = computed(() => {
  if (!statusFilter.value) return checks.value
  return checks.value.filter(c => c.status === statusFilter.value)
})

const productOptions = computed(() => 
  products.value.map(p => ({ label: `${p.code} - ${p.name}`, value: p.id }))
)

const productionOrderOptions = computed(() => [
  { label: 'None', value: '' },
  ...productionOrders.value.map(o => ({ label: o.order_no, value: o.id }))
])

const qcResultStatus = computed(() => {
  if (!selectedCheck.value) return 'Pending'
  const total = executeForm.passed_qty + executeForm.failed_qty
  if (total === 0) return 'Pending'
  if (executeForm.failed_qty === 0) return 'Passed'
  if (executeForm.passed_qty === 0) return 'Failed'
  return 'Partial Pass'
})

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { 'Pending': 'yellow', 'Passed': 'green', 'Failed': 'red', 'Partial Pass': 'orange' }
  return colors[status] || 'gray'
}

// Helper to safely extract array from API response
const extractArray = (res: any): any[] => {
  if (Array.isArray(res)) return res
  // if (res?.data && Array.isArray(res.data)) return res.data
  if (res?.data?.data && Array.isArray(res.data.data)) return res.data.data
  return []
}

const fetchData = async () => {
  loading.value = true
  try {
    const [checksRes, productsRes, ordersRes] = await Promise.all([
      $api.get('/manufacturing/quality-checks'),
      $api.get('/manufacturing/products'),
      $api.get('/manufacturing/orders')
    ])
    checks.value = extractArray(checksRes)
    products.value = extractArray(productsRes)
    productionOrders.value = extractArray(ordersRes)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { product_id: '', production_order_id: '', inspected_qty: 0, notes: '' })
  editMode.value = false
  isOpen.value = true
}

const viewDetails = (row: any) => {
  selectedCheck.value = row
  showDetailsModal.value = true
}

const openExecute = (row: any) => {
  selectedCheck.value = row
  Object.assign(executeForm, { passed_qty: row.inspected_qty, failed_qty: 0, defect_types: '', notes: '' })
  showExecuteModal.value = true
}

const save = async () => {
  submitting.value = true
  try {
    await $api.post('/manufacturing/quality-checks', form)
    toast.add({ title: 'Created', description: 'QC check created', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const submitQCResult = async () => {
  if (!selectedCheck.value) return
  submitting.value = true
  try {
    await $api.put(`/manufacturing/quality-checks/${selectedCheck.value.id}/execute`, {
      passed_qty: executeForm.passed_qty,
      failed_qty: executeForm.failed_qty,
      defect_types: executeForm.defect_types,
      notes: executeForm.notes,
      status: qcResultStatus.value
    })
    toast.add({ title: 'Submitted', description: `QC Result: ${qcResultStatus.value}`, color: qcResultStatus.value === 'Passed' ? 'green' : 'red' })
    showExecuteModal.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Export functions
const exportData = (format: string) => {
  const data = checks.value.map((c: any) => ({
    'QC Number': c.qc_number, 'Product': c.product_name, 'Date': formatDate(c.check_date),
    'Status': c.status, 'Inspected': c.inspected_qty, 'Passed': c.passed_qty, 'Failed': c.failed_qty
  }))
  if (format === 'csv') {
    const headers = Object.keys(data[0] || {})
    const csv = [headers.join(','), ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'qc_checks.csv'; a.click()
  }
}

onMounted(() => { fetchData() })
</script>
