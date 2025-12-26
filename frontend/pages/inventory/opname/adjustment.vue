<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/inventory/opname" />
        <div>
          <h2 class="text-xl font-bold">Review & Approval</h2>
          <p class="text-gray-500">Review and approve stock adjustments</p>
        </div>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
      </div>
    </div>

    <!-- Pending Reviews -->
    <UCard>
      <template #header>Pending Review & Approval</template>
      
      <DataTable 
        :columns="columns" 
        :rows="pendingOpnames" 
        :loading="loading"
        searchable
        :search-keys="['opname_number', 'warehouse.name']"
        empty-message="No pending reviews"
      >
        <template #opname_number-data="{ row }">
          <span class="font-mono">{{ row.opname_number || row.id?.substring(0, 8) }}</span>
        </template>
        <template #date-data="{ row }">
          {{ formatDate(row.date) }}
        </template>
        <template #warehouse-data="{ row }">
          {{ row.warehouse?.name || '-' }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #variance-data="{ row }">
          <span :class="row.total_variance_value < 0 ? 'text-red-600 font-bold' : 'text-green-600 font-bold'">
            {{ formatCurrency(row.total_variance_value || 0) }}
          </span>
        </template>
        <template #items-data="{ row }">
          {{ row.items_with_variance || 0 }} items
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" title="View Details" />
            <UButton v-if="row.status === 'Counting Done'" icon="i-heroicons-document-check" size="xs" color="purple" variant="ghost" @click="submitReview(row)" title="Submit Review" />
            <UButton v-if="row.status === 'Reviewed'" icon="i-heroicons-check-circle" size="xs" color="green" @click="openApproveModal(row)" title="Approve" />
            <UButton v-if="row.status === 'Reviewed'" icon="i-heroicons-x-circle" size="xs" color="red" variant="ghost" @click="openRejectModal(row)" title="Reject" />
            <UButton v-if="row.status === 'Approved'" icon="i-heroicons-arrow-up-tray" size="xs" color="primary" @click="openPostModal(row)" title="Post Adjustments" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Detail Modal -->
    <UModal v-model="showDetailModal" :ui="{ width: 'max-w-4xl' }">
      <UCard v-if="selectedOpname">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedOpname.opname_number }}</h3>
              <p class="text-sm text-gray-500">{{ selectedOpname.warehouse?.name }} | {{ formatDate(selectedOpname.date) }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedOpname.status)" size="lg">{{ selectedOpname.status }}</UBadge>
          </div>
        </template>
        
        <!-- Summary -->
        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="text-center p-3 bg-gray-50 rounded">
            <p class="text-lg font-bold">{{ selectedOpname.total_items }}</p>
            <p class="text-xs text-gray-500">Total Items</p>
          </div>
          <div class="text-center p-3 bg-orange-50 rounded">
            <p class="text-lg font-bold text-orange-600">{{ selectedOpname.items_with_variance }}</p>
            <p class="text-xs text-gray-500">With Variance</p>
          </div>
          <div class="text-center p-3 rounded" :class="selectedOpname.total_variance_value < 0 ? 'bg-red-50' : 'bg-green-50'">
            <p class="text-lg font-bold" :class="selectedOpname.total_variance_value < 0 ? 'text-red-600' : 'text-green-600'">
              {{ formatCurrency(selectedOpname.total_variance_value) }}
            </p>
            <p class="text-xs text-gray-500">Net Variance</p>
          </div>
        </div>
        
        <!-- Items with variance -->
        <div class="max-h-80 overflow-y-auto">
          <table class="w-full text-sm">
            <thead class="sticky top-0 bg-white">
              <tr class="border-b">
                <th class="text-left py-2">Product</th>
                <th class="text-left py-2">Code</th>
                <th class="text-left py-2">UoM</th>
                <th class="text-right py-2">System</th>
                <th class="text-right py-2">Counted</th>
                <th class="text-right py-2">Variance</th>
                <th class="text-right py-2">Value</th>
                <th class="text-left py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in varianceItems" :key="item.id" class="border-b">
                <td class="py-2">{{ item.product?.name }}</td>
                <td class="py-2 text-gray-500">{{ item.product?.code }}</td>
                <td class="py-2 text-gray-500">{{ item.product?.uom || 'pcs' }}</td>
                <td class="py-2 text-right font-mono">{{ item.system_qty }}</td>
                <td class="py-2 text-right font-mono">{{ item.counted_qty }}</td>
                <td class="py-2 text-right font-mono" :class="item.variance < 0 ? 'text-red-600' : 'text-green-600'">
                  {{ item.variance > 0 ? '+' : '' }}{{ item.variance }}
                </td>
                <td class="py-2 text-right" :class="item.variance_value < 0 ? 'text-red-600' : 'text-green-600'">
                  {{ formatCurrency(item.variance_value || 0) }}
                </td>
                <td class="py-2">{{ item.variance_reason || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showDetailModal = false">Close</UButton>
            <UButton v-if="selectedOpname.status === 'Counting Done'" color="purple" @click="submitReview(selectedOpname)">Submit Review</UButton>
            <UButton v-if="selectedOpname.status === 'Reviewed'" color="red" variant="outline" @click="openRejectModal(selectedOpname)">Reject</UButton>
            <UButton v-if="selectedOpname.status === 'Reviewed'" color="green" @click="openApproveModal(selectedOpname)">Approve</UButton>
            <UButton v-if="selectedOpname.status === 'Approved'" color="primary" @click="openPostModal(selectedOpname)">Post Adjustments</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- SweetAlert: Approve Modal -->
    <UModal v-model="showApproveModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <UIcon name="i-heroicons-check-circle" class="text-green-600 w-7 h-7" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-green-700">Approve Opname</h3>
              <p class="text-sm text-gray-500">{{ opnameToAction?.opname_number }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <p>Are you sure you want to approve this opname?</p>
          
          <div class="p-4 bg-green-50 rounded-lg">
            <div class="flex items-center gap-2 text-green-800 font-medium mb-2">
              <UIcon name="i-heroicons-clipboard-document-check" class="w-5 h-5" />
              <span>This will:</span>
            </div>
            <ul class="ml-7 list-disc text-sm text-green-700 space-y-1">
              <li>Mark this opname as <strong>Approved</strong></li>
              <li>Enable the <strong>Post Adjustments</strong> action</li>
              <li>Record your approval timestamp</li>
            </ul>
          </div>
          
          <div class="p-3 bg-gray-50 rounded-lg text-sm">
            <div class="grid grid-cols-2 gap-2">
              <div><span class="text-gray-500">Variance Items:</span> <strong>{{ opnameToAction?.items_with_variance }}</strong></div>
              <div><span class="text-gray-500">Net Variance:</span> <strong :class="(opnameToAction?.total_variance_value || 0) < 0 ? 'text-red-600' : 'text-green-600'">{{ formatCurrency(opnameToAction?.total_variance_value || 0) }}</strong></div>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showApproveModal = false">Cancel</UButton>
            <UButton color="green" :loading="submitting" @click="confirmApprove">
              <UIcon name="i-heroicons-check" class="mr-1" /> Approve
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- SweetAlert: Reject Modal -->
    <UModal v-model="showRejectModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <UIcon name="i-heroicons-x-circle" class="text-red-600 w-7 h-7" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-red-700">Reject Opname</h3>
              <p class="text-sm text-gray-500">{{ opnameToAction?.opname_number }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="p-4 bg-red-50 rounded-lg">
            <div class="flex items-center gap-2 text-red-800 font-medium mb-2">
              <UIcon name="i-heroicons-exclamation-triangle" class="w-5 h-5" />
              <span>This will:</span>
            </div>
            <ul class="ml-7 list-disc text-sm text-red-700 space-y-1">
              <li>Return status to <strong>Counting Done</strong></li>
              <li>Require team to <strong>recount</strong> items</li>
              <li>Add rejection notes to the opname</li>
            </ul>
          </div>
          
          <UFormGroup label="Reason for Rejection" required hint="Explain why the count needs to be redone" :ui="{ hint: 'text-xs text-gray-400' }">
            <UTextarea v-model="rejectReason" rows="3" placeholder="e.g., Several items have large unexplained variances..." />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showRejectModal = false">Cancel</UButton>
            <UButton color="red" :loading="submitting" :disabled="!rejectReason" @click="confirmReject">
              <UIcon name="i-heroicons-x-mark" class="mr-1" /> Reject
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- SweetAlert: Post Modal -->
    <UModal v-model="showPostModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <UIcon name="i-heroicons-arrow-up-tray" class="text-blue-600 w-7 h-7" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-blue-700">Post Adjustments</h3>
              <p class="text-sm text-gray-500">{{ opnameToAction?.opname_number }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div class="flex items-center gap-2 text-yellow-800 font-medium mb-2">
              <UIcon name="i-heroicons-exclamation-triangle" class="w-5 h-5" />
              <span>Warning: This action is irreversible!</span>
            </div>
          </div>
          
          <div class="p-4 bg-blue-50 rounded-lg">
            <div class="flex items-center gap-2 text-blue-800 font-medium mb-2">
              <UIcon name="i-heroicons-document-arrow-up" class="w-5 h-5" />
              <span>This will:</span>
            </div>
            <ul class="ml-7 list-disc text-sm text-blue-700 space-y-1">
              <li>Create <strong>Inventory Movement</strong> records</li>
              <li>Update <strong>Stock Quantities</strong> in the system</li>
              <li>Mark opname as <strong>Posted</strong></li>
              <li>Generate <strong>Adjustment Journal</strong> entries</li>
            </ul>
          </div>
          
          <div class="p-3 bg-gray-50 rounded-lg text-sm">
            <div class="grid grid-cols-2 gap-2">
              <div><span class="text-gray-500">Items to Adjust:</span> <strong>{{ opnameToAction?.items_with_variance }}</strong></div>
              <div><span class="text-gray-500">Net Adjustment:</span> <strong :class="(opnameToAction?.total_variance_value || 0) < 0 ? 'text-red-600' : 'text-green-600'">{{ formatCurrency(opnameToAction?.total_variance_value || 0) }}</strong></div>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showPostModal = false">Cancel</UButton>
            <UButton color="primary" :loading="submitting" @click="confirmPost">
              <UIcon name="i-heroicons-arrow-up-tray" class="mr-1" /> Post Adjustments
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

const loading = ref(false)
const submitting = ref(false)
const pendingOpnames = ref<any[]>([])
const selectedOpname = ref<any>(null)
const opnameToAction = ref<any>(null)
const showDetailModal = ref(false)
const showApproveModal = ref(false)
const showRejectModal = ref(false)
const showPostModal = ref(false)
const rejectReason = ref('')

const columns = [
  { key: 'opname_number', label: 'Number', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'status', label: 'Status' },
  { key: 'variance', label: 'Total Variance', sortable: true },
  { key: 'items', label: 'Variance Items' },
  { key: 'actions', label: '' }
]

const varianceItems = computed(() => {
  if (!selectedOpname.value?.details) return []
  return selectedOpname.value.details
    .filter((d: any) => d.counted_qty !== null && d.counted_qty !== d.system_qty)
    .map((d: any) => ({
      ...d,
      variance: d.counted_qty - d.system_qty,
      variance_value: d.variance_value || 0
    }))
})

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatCurrency = (value: number) => 
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Counting Done': 'orange', 'Reviewed': 'purple', 'Approved': 'teal', 'Posted': 'green'
  }
  return colors[status] || 'gray'
}

const fetchPending = async () => {
  loading.value = true
  try {
    const res = await $api.get('/opname/list')
    pendingOpnames.value = (res.data || []).filter((o: any) => 
      ['Counting Done', 'Reviewed', 'Approved'].includes(o.status)
    )
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const viewDetails = async (opname: any) => {
  try {
    const res = await $api.get(`/opname/${opname.id}`)
    selectedOpname.value = res.data
    showDetailModal.value = true
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load details', color: 'red' })
  }
}

const submitReview = async (opname: any) => {
  submitting.value = true
  try {
    await $api.post('/opname/review', { opname_id: opname.id })
    toast.add({ title: 'Submitted', description: 'Opname submitted for approval', color: 'green' })
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const openApproveModal = (opname: any) => {
  opnameToAction.value = opname
  showApproveModal.value = true
}

const confirmApprove = async () => {
  if (!opnameToAction.value) return
  
  submitting.value = true
  try {
    await $api.post('/opname/approve', { opname_id: opnameToAction.value.id, approved: true })
    toast.add({ title: 'Approved!', description: 'Opname approved and ready for posting', color: 'green' })
    showApproveModal.value = false
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Approval failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const openRejectModal = (opname: any) => {
  opnameToAction.value = opname
  rejectReason.value = ''
  showRejectModal.value = true
}

const confirmReject = async () => {
  if (!opnameToAction.value || !rejectReason.value) return
  
  submitting.value = true
  try {
    await $api.post('/opname/approve', { 
      opname_id: opnameToAction.value.id, 
      approved: false, 
      rejection_reason: rejectReason.value 
    })
    toast.add({ title: 'Rejected', description: 'Opname returned for recount', color: 'orange' })
    showRejectModal.value = false
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Rejection failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const openPostModal = (opname: any) => {
  opnameToAction.value = opname
  showPostModal.value = true
}

const confirmPost = async () => {
  if (!opnameToAction.value) return
  
  submitting.value = true
  try {
    await $api.post('/opname/post', { opname_id: opnameToAction.value.id })
    toast.add({ title: 'Posted!', description: 'Stock adjustments have been applied', color: 'green' })
    showPostModal.value = false
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Post failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Export functions
const exportData = (format: string) => {
  const data = pendingOpnames.value.map((o: any) => ({
    'Number': o.opname_number || '-',
    'Date': formatDate(o.date),
    'Warehouse': o.warehouse?.name || '-',
    'Status': o.status,
    'Total Items': o.total_items,
    'Variance Items': o.items_with_variance,
    'Net Variance': o.total_variance_value
  }))
  
  if (format === 'csv') exportToCSV(data, 'review_approval')
  else if (format === 'xlsx') exportToXLSX(data, 'review_approval')
  else if (format === 'pdf') exportToPDF(data, 'Review & Approval', 'review_approval')
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
  fetchPending()
})
</script>
