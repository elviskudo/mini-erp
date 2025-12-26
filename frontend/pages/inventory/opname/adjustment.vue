<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/inventory/opname" />
      <div>
        <h2 class="text-xl font-bold">Review & Approval</h2>
        <p class="text-gray-500">Review and approve stock adjustments</p>
      </div>
    </div>

    <!-- Pending Reviews -->
    <UCard>
      <template #header>Pending Review & Approval</template>
      
      <UTable :columns="columns" :rows="pendingOpnames" :loading="loading">
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
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status === 'Reviewed'" icon="i-heroicons-check" size="xs" color="green" @click="approve(row)" title="Approve" />
            <UButton v-if="row.status === 'Reviewed'" icon="i-heroicons-x-mark" size="xs" color="red" variant="ghost" @click="reject(row)" title="Reject" />
            <UButton v-if="row.status === 'Approved'" icon="i-heroicons-arrow-up-tray" size="xs" color="primary" @click="postAdjustments(row)" title="Post" />
          </div>
        </template>
      </UTable>
      
      <div v-if="!loading && pendingOpnames.length === 0" class="text-center py-8 text-gray-500">
        <UIcon name="i-heroicons-inbox" class="w-12 h-12 mx-auto mb-2" />
        <p>No pending reviews</p>
      </div>
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
            <UButton v-if="selectedOpname.status === 'Reviewed'" color="red" variant="outline" @click="reject(selectedOpname)">Reject</UButton>
            <UButton v-if="selectedOpname.status === 'Reviewed'" color="green" @click="approve(selectedOpname)">Approve</UButton>
            <UButton v-if="selectedOpname.status === 'Approved'" color="primary" @click="postAdjustments(selectedOpname)">Post Adjustments</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Reject Modal -->
    <UModal v-model="showRejectModal">
      <UCard>
        <template #header>Reject Opname</template>
        <UFormGroup label="Reason for rejection">
          <UTextarea v-model="rejectReason" rows="3" placeholder="Provide reason..." />
        </UFormGroup>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showRejectModal = false">Cancel</UButton>
            <UButton color="red" @click="confirmReject" :loading="submitting">Reject</UButton>
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
const showDetailModal = ref(false)
const showRejectModal = ref(false)
const rejectReason = ref('')

const columns = [
  { key: 'opname_number', label: 'Number' },
  { key: 'date', label: 'Date' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'status', label: 'Status' },
  { key: 'variance', label: 'Total Variance' },
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

const approve = async (opname: any) => {
  if (!confirm('Approve this opname for posting?')) return
  
  submitting.value = true
  try {
    await $api.post('/opname/approve', { opname_id: opname.id, approved: true })
    toast.add({ title: 'Approved', description: 'Ready for posting', color: 'green' })
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const reject = (opname: any) => {
  selectedOpname.value = opname
  rejectReason.value = ''
  showRejectModal.value = true
}

const confirmReject = async () => {
  if (!rejectReason.value) {
    toast.add({ title: 'Error', description: 'Please provide a reason', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    await $api.post('/opname/approve', { 
      opname_id: selectedOpname.value.id, 
      approved: false,
      rejection_reason: rejectReason.value
    })
    toast.add({ title: 'Rejected', description: 'Sent back for recount', color: 'orange' })
    showRejectModal.value = false
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const postAdjustments = async (opname: any) => {
  if (!confirm('Post adjustments to inventory? This will update stock quantities.')) return
  
  submitting.value = true
  try {
    const res = await $api.post('/opname/post', { opname_id: opname.id })
    toast.add({ title: 'Posted', description: `${res.data.adjustments_made} adjustments made`, color: 'green' })
    showDetailModal.value = false
    await fetchPending()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchPending()
})
</script>
