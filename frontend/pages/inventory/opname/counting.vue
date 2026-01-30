<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/inventory/opname" />
        <div>
          <h2 class="text-xl font-bold">Physical Counting</h2>
          <p class="text-gray-500">Count and record stock quantities</p>
        </div>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
        <UButton v-if="selectedOpname && selectedOpname.status === 'Scheduled'" icon="i-heroicons-play" color="yellow" @click="startCounting">
          Start Counting
        </UButton>
        <UButton v-if="selectedOpname && selectedOpname.status === 'In Progress'" icon="i-heroicons-check" color="green" @click="completeCounting">
          Complete Counting
        </UButton>
      </div>
    </div>

    <!-- Opname Selector -->
    <UCard v-if="!selectedOpname">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-clipboard-document-list" class="w-5 h-5" />
          <span>Select Opname to Count</span>
        </div>
      </template>
      <DataTable 
        :columns="opnameColumns" 
        :rows="opnames" 
        :loading="loading"
        searchable
        :search-keys="['opname_number', 'warehouse.name']"
        empty-message="No opnames available for counting"
      >
        <template #opname_number-data="{ row }">
          <span class="font-medium text-gray-900">{{ row.opname_number || row.id.substring(0, 8) }}</span>
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
        <template #progress-data="{ row }">
          <div class="flex items-center gap-2">
            <div class="w-20 bg-gray-200 rounded-full h-2">
              <div class="bg-primary-500 h-2 rounded-full" :style="{ width: `${getProgress(row)}%` }"></div>
            </div>
            <span class="text-xs text-gray-500">{{ row.counted_items || 0 }}/{{ row.total_items }}</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <UButton 
            size="xs" 
            :color="row.status === 'In Progress' ? 'primary' : 'gray'"
            @click="selectOpname(row)"
          >
            {{ row.status === 'In Progress' ? 'Continue' : 'Start' }}
          </UButton>
        </template>
      </DataTable>
    </UCard>

    <!-- Counting Interface -->
    <template v-if="selectedOpname">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <UCard>
          <div class="text-center">
            <p class="text-2xl font-bold">{{ selectedOpname.total_items }}</p>
            <p class="text-sm text-gray-500">Total Items</p>
          </div>
        </UCard>
        <UCard>
          <div class="text-center">
            <p class="text-2xl font-bold text-blue-600">{{ countedCount }}</p>
            <p class="text-sm text-gray-500">Counted</p>
          </div>
        </UCard>
        <UCard>
          <div class="text-center">
            <p class="text-2xl font-bold text-orange-600">{{ pendingCount }}</p>
            <p class="text-sm text-gray-500">Pending</p>
          </div>
        </UCard>
        <UCard>
          <div class="text-center">
            <p class="text-2xl font-bold" :class="varianceCount > 0 ? 'text-red-600' : 'text-green-600'">
              {{ varianceCount }}
            </p>
            <p class="text-sm text-gray-500">With Variance</p>
          </div>
        </UCard>
      </div>

      <!-- Quick Entry -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <span>Quick Entry</span>
            <UButton icon="i-heroicons-x-mark" variant="ghost" size="xs" @click="selectedOpname = null">Back to List</UButton>
          </div>
        </template>
        <div class="flex gap-4">
          <UFormGroup label="Scan/Enter Product Code" class="flex-1">
            <UInput v-model="quickCode" placeholder="Scan barcode or enter product code" @keyup.enter="findAndFocus" />
          </UFormGroup>
          <UFormGroup label="Quantity">
            <UInput v-model.number="quickQty" type="number" class="w-24" @keyup.enter="quickEntry" />
          </UFormGroup>
          <div class="flex items-end">
            <UButton @click="quickEntry" :disabled="!quickCode">Add</UButton>
          </div>
        </div>
      </UCard>

      <!-- Items to Count -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <span>Items to Count</span>
            <div class="flex gap-2">
              <UButton size="xs" variant="outline" @click="showPendingOnly = !showPendingOnly">
                {{ showPendingOnly ? 'Show All' : 'Show Pending Only' }}
              </UButton>
              <UButton size="xs" variant="outline" icon="i-heroicons-arrow-path" @click="saveAllCounts" :loading="saving">
                Save All
              </UButton>
            </div>
          </div>
        </template>
        
        <DataTable
          :columns="itemColumns"
          :rows="displayItems"
          :loading="loading"
          searchable
          :search-keys="['product.name', 'product.code', 'location.name']"
          empty-message="No items to count"
        >
          <template #product-data="{ row }">
            <div>
              <p class="font-medium">{{ row.product?.name || 'Unknown' }}</p>
              <p class="text-xs text-gray-400">{{ row.product?.code }}</p>
            </div>
          </template>
          <template #location-data="{ row }">
            {{ row.location?.name || '-' }}
          </template>
          <template #system_qty-data="{ row }">
            <span class="font-mono">{{ row.system_qty }}</span>
          </template>
          <template #counted_qty-data="{ row }">
            <UInput 
              :model-value="row.counted_qty" 
              @update:model-value="val => updateCount(row, val)"
              type="number" 
              class="w-24"
              :class="{ 'ring-2 ring-green-500': row.counted_qty != null }"
            />
          </template>
          <template #variance-data="{ row }">
            <span v-if="row.counted_qty != null" class="font-mono font-bold" :class="getVariance(row) < 0 ? 'text-red-600' : getVariance(row) > 0 ? 'text-green-600' : ''">
              {{ getVariance(row) > 0 ? '+' : '' }}{{ getVariance(row) }}
            </span>
            <span v-else class="text-gray-400">-</span>
          </template>
          <template #status-data="{ row }">
            <UBadge v-if="row.counted_qty != null" color="green" variant="subtle">Counted</UBadge>
            <UBadge v-else color="orange" variant="subtle">Pending</UBadge>
          </template>
        </DataTable>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const opnames = ref<any[]>([])
const selectedOpname = ref<any>(null)
const showPendingOnly = ref(false)

const quickCode = ref('')
const quickQty = ref<number | null>(null)

const opnameColumns = [
  { key: 'opname_number', label: 'Number', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'actions', label: '' }
]

const itemColumns = [
  { key: 'product', label: 'Product', sortable: true },
  { key: 'location', label: 'Location' },
  { key: 'system_qty', label: 'System Qty', sortable: true },
  { key: 'counted_qty', label: 'Counted Qty' },
  { key: 'variance', label: 'Variance' },
  { key: 'status', label: 'Status' }
]

const displayItems = computed(() => {
  if (!selectedOpname.value?.details) return []
  if (showPendingOnly.value) {
    return selectedOpname.value.details.filter((d: any) => d.counted_qty == null)
  }
  return selectedOpname.value.details
})

const countedCount = computed(() => 
  selectedOpname.value?.details?.filter((d: any) => d.counted_qty != null).length || 0
)

const pendingCount = computed(() => 
  (selectedOpname.value?.total_items || 0) - countedCount.value
)

const varianceCount = computed(() => 
  selectedOpname.value?.details?.filter((d: any) => d.counted_qty != null && d.counted_qty !== d.system_qty).length || 0
)

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Scheduled': 'blue', 'In Progress': 'yellow', 'Counting Done': 'green'
  }
  return colors[status] || 'gray'
}

const getProgress = (opname: any) => {
  if (!opname.total_items) return 0
  return Math.round((opname.counted_items || 0) / opname.total_items * 100)
}

const getVariance = (row: any) => {
  if (row.counted_qty == null) return 0
  return row.counted_qty - row.system_qty
}

const fetchOpnames = async () => {
  loading.value = true
  try {
    const res = await $api.get('/opname/list')
    opnames.value = (res.data.data || []).filter((o: any) => 
      ['Scheduled', 'In Progress'].includes(o.status)
    )
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const selectOpname = async (opname: any) => {
  loading.value = true
  try {
    const res = await $api.get(`/opname/${opname.id}`)
    selectedOpname.value = res.data.data || res.data // Fallback to res.data if not wrapped
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load opname', color: 'red' })
  } finally {
    loading.value = false
  }
}

const startCounting = async () => {
  if (!selectedOpname.value) return
  try {
    await $api.post('/opname/start-counting', { opname_id: selectedOpname.value.id })
    selectedOpname.value.status = 'In Progress'
    toast.add({ title: 'Started', description: 'Counting started', color: 'green' })
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const updateCount = (row: any, value: any) => {
  row.counted_qty = value === '' || value === null ? null : Number(value)
}

const findAndFocus = () => {
  if (!quickCode.value) return
  const item = selectedOpname.value?.details?.find((d: any) => 
    d.product?.code?.toLowerCase() === quickCode.value.toLowerCase()
  )
  if (item) {
    toast.add({ title: 'Found', description: item.product?.name, color: 'green', timeout: 1500 })
  } else {
    toast.add({ title: 'Not Found', description: 'Product not in count list', color: 'orange' })
  }
}

const quickEntry = () => {
  if (!quickCode.value || quickQty.value == null) return
  const item = selectedOpname.value?.details?.find((d: any) => 
    d.product?.code?.toLowerCase() === quickCode.value.toLowerCase()
  )
  if (item) {
    item.counted_qty = quickQty.value
    toast.add({ title: 'Counted', description: `${item.product?.name}: ${quickQty.value}`, color: 'green', timeout: 1500 })
    quickCode.value = ''
    quickQty.value = null
  } else {
    toast.add({ title: 'Not Found', description: 'Product not in count list', color: 'orange' })
  }
}

const saveAllCounts = async () => {
  if (!selectedOpname.value) return
  
  const items = selectedOpname.value.details
    .filter((d: any) => d.counted_qty != null)
    .map((d: any) => ({
      detail_id: d.id,
      counted_qty: d.counted_qty
    }))
  
  if (!items.length) {
    toast.add({ title: 'No Changes', description: 'No counts to save', color: 'yellow' })
    return
  }
  
  saving.value = true
  try {
    await $api.post('/opname/update-count', {
      opname_id: selectedOpname.value.id,
      items
    })
    toast.add({ title: 'Saved', description: `${items.length} items saved`, color: 'green' })
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    saving.value = false
  }
}

const completeCounting = async () => {
  if (!selectedOpname.value) return
  
  // Check if all items counted
  const pending = selectedOpname.value.details?.filter((d: any) => d.counted_qty == null) || []
  if (pending.length > 0) {
    if (!confirm(`${pending.length} items not counted yet. Continue anyway?`)) return
  }
  
  // Save counts first
  await saveAllCounts()
  
  try {
    await $api.post('/opname/complete-counting', null, { params: { opname_id: selectedOpname.value.id } })
    toast.add({ title: 'Complete', description: 'Counting completed. Redirecting to Variance Analysis...', color: 'green' })
    
    // Redirect to Variance Analysis page
    setTimeout(() => {
      router.push('/inventory/opname/matching')
    }, 1500)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

// Export functions
const exportData = (format: string) => {
  const items = selectedOpname.value?.details || opnames.value
  const data = items.map((i: any) => ({
    'Product': i.product?.name || i.opname_number || 'Unknown',
    'Code': i.product?.code || '-',
    'Location': i.location?.name || i.warehouse?.name || '-',
    'System Qty': i.system_qty || i.total_items || 0,
    'Counted Qty': i.counted_qty ?? '-',
    'Variance': i.counted_qty != null ? i.counted_qty - i.system_qty : '-'
  }))
  
  if (format === 'csv') exportToCSV(data, 'counting_items')
  else if (format === 'xlsx') exportToXLSX(data, 'counting_items')
  else if (format === 'pdf') exportToPDF(data, 'Physical Counting Items', 'counting_items')
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
  fetchOpnames()
})
</script>
