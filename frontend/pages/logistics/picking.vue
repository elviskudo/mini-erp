<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Stock Picking</h2>
        <p class="text-gray-500">Picking lists for warehouse team to prepare shipments</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ pickingLists.length }}</p>
          <p class="text-sm text-gray-500">Total Picks</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ pendingPicks }}</p>
          <p class="text-sm text-gray-500">Pending</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ inProgressPicks }}</p>
          <p class="text-sm text-gray-500">In Progress</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ completedToday }}</p>
          <p class="text-sm text-gray-500">Completed Today</p>
        </div>
      </UCard>
    </div>

    <!-- Tabs for different pick statuses -->
    <UTabs :items="tabs" v-model="activeTab">
      <template #pending>
        <UCard class="mt-4">
          <DataTable 
            :columns="columns" 
            :rows="pendingLists" 
            :loading="loading"
            searchable
            :search-keys="['pick_number', 'so_number']"
            empty-message="No pending picks"
          >
            <template #pick_number-data="{ row }">
              <span class="font-mono font-medium text-blue-600">{{ row.pick_number }}</span>
            </template>
            <template #priority-data="{ row }">
              <UBadge :color="row.priority === 'Urgent' ? 'red' : row.priority === 'High' ? 'orange' : 'gray'">{{ row.priority || 'Normal' }}</UBadge>
            </template>
            <template #items_count-data="{ row }">
              {{ row.items_count || 0 }} items
            </template>
            <template #actions-data="{ row }">
              <div class="flex gap-1">
                <UButton icon="i-heroicons-play" size="xs" color="blue" @click="startPicking(row)">Start</UButton>
                <UButton icon="i-heroicons-printer" size="xs" color="gray" variant="ghost" @click="printPickList(row)" title="Print" />
              </div>
            </template>
          </DataTable>
        </UCard>
      </template>
      
      <template #in_progress>
        <UCard class="mt-4">
          <DataTable 
            :columns="progressColumns" 
            :rows="inProgressLists" 
            :loading="loading"
            empty-message="No picks in progress"
          >
            <template #pick_number-data="{ row }">
              <span class="font-mono font-medium">{{ row.pick_number }}</span>
            </template>
            <template #progress-data="{ row }">
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-100 rounded-full h-2">
                  <div class="h-2 rounded-full bg-blue-500" :style="{ width: `${row.progress || 0}%` }"></div>
                </div>
                <span class="text-sm">{{ row.progress || 0 }}%</span>
              </div>
            </template>
            <template #picker-data="{ row }">
              {{ row.picker_name || 'Unassigned' }}
            </template>
            <template #actions-data="{ row }">
              <UButton icon="i-heroicons-check" size="xs" color="green" @click="completePicking(row)">Complete</UButton>
            </template>
          </DataTable>
        </UCard>
      </template>
      
      <template #completed>
        <UCard class="mt-4">
          <DataTable 
            :columns="completedColumns" 
            :rows="completedLists" 
            :loading="loading"
            empty-message="No completed picks"
          >
            <template #pick_number-data="{ row }">
              <span class="font-mono">{{ row.pick_number }}</span>
            </template>
            <template #completed_at-data="{ row }">
              {{ formatDateTime(row.completed_at) }}
            </template>
          </DataTable>
        </UCard>
      </template>
    </UTabs>

    <!-- Pick Detail Modal -->
    <UModal v-model="showDetailModal" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedPick">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedPick.pick_number }}</h3>
              <p class="text-sm text-gray-500">SO: {{ selectedPick.so_number }} | Location: {{ selectedPick.warehouse_name }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedPick.status)" size="lg">{{ selectedPick.status }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <h4 class="font-medium">Items to Pick</h4>
          <div v-for="item in (selectedPick.items || [])" :key="item.id" class="p-3 border rounded-lg flex justify-between items-center">
            <div>
              <p class="font-medium">{{ item.product_name }}</p>
              <p class="text-sm text-gray-500">Location: {{ item.location_code }} | Batch: {{ item.batch_number || 'N/A' }}</p>
            </div>
            <div class="text-right">
              <p class="text-lg font-bold">{{ item.quantity }}</p>
              <p class="text-xs text-gray-400">{{ item.uom }}</p>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDetailModal = false">Close</UButton>
            <UButton icon="i-heroicons-printer" @click="printPickList(selectedPick)">Print Pick List</UButton>
          </div>
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
const activeTab = ref(0)
const showDetailModal = ref(false)

const pickingLists = ref<any[]>([])
const selectedPick = ref<any>(null)

const tabs = [
  { label: 'Pending', slot: 'pending' },
  { label: 'In Progress', slot: 'in_progress' },
  { label: 'Completed', slot: 'completed' }
]

const columns = [
  { key: 'pick_number', label: 'Pick #' },
  { key: 'so_number', label: 'Sales Order' },
  { key: 'priority', label: 'Priority' },
  { key: 'items_count', label: 'Items' },
  { key: 'actions', label: '' }
]

const progressColumns = [
  { key: 'pick_number', label: 'Pick #' },
  { key: 'so_number', label: 'Sales Order' },
  { key: 'progress', label: 'Progress' },
  { key: 'picker', label: 'Picker' },
  { key: 'actions', label: '' }
]

const completedColumns = [
  { key: 'pick_number', label: 'Pick #' },
  { key: 'so_number', label: 'Sales Order' },
  { key: 'picker_name', label: 'Picked By' },
  { key: 'completed_at', label: 'Completed' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const pendingLists = computed(() => pickingLists.value.filter(p => p.status === 'Pending'))
const inProgressLists = computed(() => pickingLists.value.filter(p => p.status === 'In Progress'))
const completedLists = computed(() => pickingLists.value.filter(p => p.status === 'Completed'))

const pendingPicks = computed(() => pendingLists.value.length)
const inProgressPicks = computed(() => inProgressLists.value.length)
const completedToday = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return completedLists.value.filter(p => p.completed_at?.startsWith(today)).length
})

const formatDateTime = (date: string) => date ? new Date(date).toLocaleString('en-US', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Pending: 'yellow', 'In Progress': 'blue', Completed: 'green' }
  return colors[status] || 'gray'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/logistics/picking').catch(() => ({ data: [] }))
    pickingLists.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const startPicking = async (row: any) => {
  try {
    await $api.put(`/logistics/picking/${row.id}/start`)
    toast.add({ title: 'Picking Started', description: 'Pick list is now in progress', color: 'blue' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const completePicking = async (row: any) => {
  try {
    await $api.put(`/logistics/picking/${row.id}/complete`)
    toast.add({ title: 'Completed', description: 'Picking completed, ready for shipment', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const printPickList = (row: any) => {
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`
      <html><head><title>Pick List - ${row.pick_number}</title>
      <style>
        body{font-family:Arial;padding:20px;}
        h1{border-bottom:2px solid #333;padding-bottom:10px;}
        table{width:100%;border-collapse:collapse;margin-top:20px;}
        th,td{border:1px solid #ddd;padding:10px;text-align:left;}
        th{background:#f4f4f4;}
        .header{display:flex;justify-content:space-between;margin-bottom:20px;}
        .checkbox{width:20px;height:20px;border:1px solid #333;display:inline-block;}
      </style>
      </head><body>
      <h1>Pick List</h1>
      <div class="header">
        <div><strong>Pick #:</strong> ${row.pick_number}</div>
        <div><strong>SO:</strong> ${row.so_number || 'N/A'}</div>
        <div><strong>Date:</strong> ${new Date().toLocaleDateString()}</div>
      </div>
      <table>
        <tr><th>✓</th><th>Product</th><th>Location</th><th>Batch</th><th>Qty</th><th>Picked</th></tr>
        ${(row.items || []).map((i: any) => `
          <tr>
            <td><span class="checkbox"></span></td>
            <td>${i.product_name}</td>
            <td>${i.location_code || '-'}</td>
            <td>${i.batch_number || '-'}</td>
            <td>${i.quantity}</td>
            <td></td>
          </tr>
        `).join('')}
      </table>
      <p style="margin-top:30px;"><strong>Picked By:</strong> ______________________ <strong>Date:</strong> ______________________</p>
      </body></html>
    `)
    printWindow.document.close()
    printWindow.print()
  }
}

const exportData = (format: string) => {
  const data = pickingLists.value.map((p: any) => ({
    'Pick #': p.pick_number,
    'Sales Order': p.so_number || '',
    'Priority': p.priority || 'Normal',
    'Status': p.status,
    'Items': p.items_count || 0,
    'Picker': p.picker_name || ''
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `picking_lists.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Picking lists exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Picking Lists</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Picking Lists Report</h1>
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

onMounted(() => { fetchData() })
</script>
