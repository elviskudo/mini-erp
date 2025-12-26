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
      <template #header>Select Opname to Count</template>
      <UTable :columns="opnameColumns" :rows="opnames" :loading="loading">
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
            <UProgress :value="getProgress(row)" size="sm" class="w-20" />
            <span class="text-xs">{{ row.counted_items || 0 }}/{{ row.total_items || 0 }}</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" @click="selectOpname(row)">
            {{ ['Scheduled', 'In Progress'].includes(row.status) ? 'Open' : 'View' }}
          </UButton>
        </template>
      </UTable>
    </UCard>

    <!-- Counting Interface -->
    <div v-else class="space-y-4">
      <!-- Header Card -->
      <UCard>
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-bold text-lg">{{ selectedOpname.opname_number }}</h3>
            <p class="text-gray-500">{{ selectedOpname.warehouse?.name }} | {{ formatDate(selectedOpname.date) }}</p>
          </div>
          <div class="text-right">
            <UBadge :color="getStatusColor(selectedOpname.status)" size="lg">{{ selectedOpname.status }}</UBadge>
            <p class="text-sm text-gray-500 mt-1">{{ selectedOpname.counted_items || 0 }} / {{ selectedOpname.total_items || 0 }} counted</p>
          </div>
        </div>
        <UProgress :value="getProgress(selectedOpname)" class="mt-4" />
      </UCard>

      <!-- Quick Entry -->
      <UCard v-if="['Scheduled', 'In Progress'].includes(selectedOpname.status)">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-bolt" class="text-yellow-500" />
            <span>Quick Entry</span>
          </div>
        </template>
        <div class="flex gap-4 items-end">
          <UFormGroup label="Search Product" class="flex-1">
            <UInput v-model="searchQuery" placeholder="Product name or code..." icon="i-heroicons-magnifying-glass" />
          </UFormGroup>
          <UButton icon="i-heroicons-qr-code" variant="outline" disabled>Scan</UButton>
        </div>
      </UCard>

      <!-- Items List -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <span>Items to Count</span>
            <UButton v-if="hasUnsavedChanges" size="xs" color="green" @click="saveAllCounts" :loading="saving">
              Save All Changes
            </UButton>
          </div>
        </template>
        
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b">
                <th class="text-left py-2 px-3">Product</th>
                <th class="text-left py-2 px-3">Location</th>
                <th class="text-right py-2 px-3">System Qty</th>
                <th class="text-center py-2 px-3 w-32">Counted</th>
                <th class="text-right py-2 px-3">Variance</th>
                <th class="text-left py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredItems" :key="item.id" 
                  class="border-b hover:bg-gray-50"
                  :class="{ 'bg-red-50': item.variance < 0, 'bg-green-50': item.variance > 0 }">
                <td class="py-3 px-3">
                  <p class="font-medium">{{ item.product?.name || 'Unknown' }}</p>
                  <p class="text-xs text-gray-400">{{ item.product?.code }}</p>
                </td>
                <td class="py-3 px-3 text-gray-600">{{ item.location?.name || '-' }}</td>
                <td class="py-3 px-3 text-right font-mono">{{ item.system_qty }}</td>
                <td class="py-3 px-3">
                  <UInput 
                    v-if="canEdit"
                    v-model.number="item.counted_qty" 
                    type="number" 
                    size="sm" 
                    class="w-24"
                    @change="markChanged(item)"
                  />
                  <span v-else class="font-mono">{{ item.counted_qty ?? '-' }}</span>
                </td>
                <td class="py-3 px-3 text-right font-mono font-bold"
                    :class="{ 'text-red-600': item.variance < 0, 'text-green-600': item.variance > 0 }">
                  {{ item.counted_qty != null ? (item.variance > 0 ? '+' : '') + item.variance : '-' }}
                </td>
                <td class="py-3 px-3">
                  <UIcon v-if="item.counted_qty != null" name="i-heroicons-check-circle" class="text-green-500" />
                  <UIcon v-else name="i-heroicons-clock" class="text-gray-400" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const route = useRoute()

const loading = ref(false)
const saving = ref(false)
const opnames = ref<any[]>([])
const selectedOpname = ref<any>(null)
const searchQuery = ref('')
const changedItems = ref<Set<string>>(new Set())

const opnameColumns = [
  { key: 'opname_number', label: 'Number' },
  { key: 'date', label: 'Date' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'actions', label: '' }
]

const canEdit = computed(() => 
  selectedOpname.value && ['Scheduled', 'In Progress'].includes(selectedOpname.value.status)
)

const hasUnsavedChanges = computed(() => changedItems.value.size > 0)

const filteredItems = computed(() => {
  if (!selectedOpname.value?.details) return []
  const items = selectedOpname.value.details.map((d: any) => ({
    ...d,
    variance: d.counted_qty != null ? d.counted_qty - d.system_qty : 0
  }))
  
  if (!searchQuery.value) return items
  const q = searchQuery.value.toLowerCase()
  return items.filter((i: any) => 
    i.product?.name?.toLowerCase().includes(q) || 
    i.product?.code?.toLowerCase().includes(q)
  )
})

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Scheduled': 'blue', 'In Progress': 'yellow', 'Counting Done': 'orange',
    'Reviewed': 'purple', 'Approved': 'teal', 'Posted': 'green', 'Cancelled': 'red'
  }
  return colors[status] || 'gray'
}

const getProgress = (o: any) => o.total_items ? Math.round((o.counted_items / o.total_items) * 100) : 0

const fetchOpnames = async () => {
  loading.value = true
  try {
    const res = await $api.get('/opname/list')
    opnames.value = (res.data || []).filter((o: any) => 
      ['Scheduled', 'In Progress', 'Counting Done'].includes(o.status)
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
    selectedOpname.value = res.data
    changedItems.value.clear()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load opname', color: 'red' })
  } finally {
    loading.value = false
  }
}

const startCounting = async () => {
  try {
    await $api.post('/opname/start-counting', { opname_id: selectedOpname.value.id })
    selectedOpname.value.status = 'In Progress'
    toast.add({ title: 'Started', description: 'Counting started', color: 'green' })
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const markChanged = (item: any) => {
  changedItems.value.add(item.id)
  item.variance = item.counted_qty != null ? item.counted_qty - item.system_qty : 0
}

const saveAllCounts = async () => {
  saving.value = true
  try {
    const items = selectedOpname.value.details
      .filter((d: any) => changedItems.value.has(d.id))
      .map((d: any) => ({
        detail_id: d.id,
        counted_qty: d.counted_qty
      }))
    
    await $api.post('/opname/update-count', {
      opname_id: selectedOpname.value.id,
      items
    })
    
    changedItems.value.clear()
    toast.add({ title: 'Saved', description: `${items.length} items updated`, color: 'green' })
    
    // Refresh
    await selectOpname(selectedOpname.value)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    saving.value = false
  }
}

const completeCounting = async () => {
  if (!confirm('Mark counting as complete? This will move to review stage.')) return
  
  try {
    await $api.post('/opname/complete-counting', null, { params: { opname_id: selectedOpname.value.id } })
    toast.add({ title: 'Complete', description: 'Ready for review', color: 'green' })
    selectedOpname.value = null
    await fetchOpnames()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

onMounted(async () => {
  await fetchOpnames()
  
  // Auto-select if ID in query
  const id = route.query.id as string
  if (id) {
    const opname = opnames.value.find(o => o.id === id)
    if (opname) await selectOpname(opname)
  }
})
</script>
