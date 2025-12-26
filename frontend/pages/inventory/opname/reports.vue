<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/inventory/opname" />
      <div>
        <h2 class="text-xl font-bold">Reports & Evaluation</h2>
        <p class="text-gray-500">Analyze opname results and trends</p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-primary-600">{{ stats.total_opnames }}</p>
          <p class="text-sm text-gray-500">Total Opnames</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-green-600">{{ stats.completed_opnames }}</p>
          <p class="text-sm text-gray-500">Completed</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold" :class="stats.total_variance_value < 0 ? 'text-red-600' : 'text-green-600'">
            {{ formatCurrency(stats.total_variance_value || 0) }}
          </p>
          <p class="text-sm text-gray-500">Total Variance</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-orange-600">{{ formatCurrency(stats.avg_variance_per_opname || 0) }}</p>
          <p class="text-sm text-gray-500">Avg per Opname</p>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Common Variance Reasons -->
      <UCard>
        <template #header>Common Variance Reasons</template>
        <div v-if="stats.common_variance_reasons?.length" class="space-y-3">
          <div v-for="(reason, idx) in stats.common_variance_reasons" :key="idx" class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                   :class="getReasonColor(reason.reason)">
                {{ idx + 1 }}
              </div>
              <span>{{ reason.reason }}</span>
            </div>
            <UBadge variant="subtle" color="gray">{{ reason.count }} items</UBadge>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500">
          <UIcon name="i-heroicons-chart-pie" class="w-8 h-8 mx-auto mb-2" />
          <p>No variance data yet</p>
        </div>
      </UCard>

      <!-- Recent Completed -->
      <UCard>
        <template #header>Recently Completed</template>
        <div class="space-y-3">
          <div v-for="opname in recentCompleted" :key="opname.id" 
               class="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer"
               @click="viewReport(opname)">
            <div>
              <p class="font-medium">{{ opname.opname_number || opname.id?.substring(0, 8) }}</p>
              <p class="text-xs text-gray-500">{{ opname.warehouse?.name }} • {{ formatDate(opname.date) }}</p>
            </div>
            <div class="text-right">
              <p class="font-bold" :class="opname.total_variance_value < 0 ? 'text-red-600' : 'text-green-600'">
                {{ formatCurrency(opname.total_variance_value || 0) }}
              </p>
              <p class="text-xs text-gray-500">{{ opname.items_with_variance }} variances</p>
            </div>
          </div>
        </div>
        <div v-if="!recentCompleted.length" class="text-center py-8 text-gray-500">
          No completed opnames
        </div>
      </UCard>
    </div>

    <!-- Variance Report Modal -->
    <UModal v-model="showReportModal" :ui="{ width: 'max-w-4xl' }">
      <UCard v-if="selectedReport">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">Variance Report</h3>
              <p class="text-sm text-gray-500">{{ selectedReport.opname_number }} | {{ selectedReport.warehouse_name }}</p>
            </div>
            <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportReport">Export</UButton>
          </div>
        </template>
        
        <div class="grid grid-cols-3 gap-4 mb-4">
          <div class="text-center p-3 bg-gray-50 rounded">
            <p class="text-lg font-bold">{{ selectedReport.total_items }}</p>
            <p class="text-xs text-gray-500">Total Items</p>
          </div>
          <div class="text-center p-3 bg-orange-50 rounded">
            <p class="text-lg font-bold text-orange-600">{{ selectedReport.items_with_variance }}</p>
            <p class="text-xs text-gray-500">With Variance</p>
          </div>
          <div class="text-center p-3 rounded" :class="selectedReport.total_variance_value < 0 ? 'bg-red-50' : 'bg-green-50'">
            <p class="text-lg font-bold" :class="selectedReport.total_variance_value < 0 ? 'text-red-600' : 'text-green-600'">
              {{ formatCurrency(selectedReport.total_variance_value) }}
            </p>
            <p class="text-xs text-gray-500">Net Variance</p>
          </div>
        </div>
        
        <UTable :columns="reportColumns" :rows="selectedReport.variance_items || []">
          <template #variance-data="{ row }">
            <span :class="row.variance < 0 ? 'text-red-600' : 'text-green-600'">
              {{ row.variance > 0 ? '+' : '' }}{{ row.variance }}
            </span>
          </template>
          <template #variance_value-data="{ row }">
            <span :class="row.variance_value < 0 ? 'text-red-600' : 'text-green-600'">
              {{ formatCurrency(row.variance_value) }}
            </span>
          </template>
        </UTable>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const stats = ref<any>({})
const opnames = ref<any[]>([])
const selectedReport = ref<any>(null)
const showReportModal = ref(false)

const reportColumns = [
  { key: 'product_name', label: 'Product' },
  { key: 'location', label: 'Location' },
  { key: 'system_qty', label: 'System' },
  { key: 'counted_qty', label: 'Counted' },
  { key: 'variance', label: 'Variance' },
  { key: 'variance_reason', label: 'Reason' },
  { key: 'variance_value', label: 'Value' }
]

const recentCompleted = computed(() => 
  opnames.value.filter(o => o.status === 'Posted').slice(0, 5)
)

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatCurrency = (value: number) => 
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)

const getReasonColor = (reason: string) => {
  const colors: Record<string, string> = {
    'Theft': 'bg-red-100 text-red-700',
    'Damage': 'bg-orange-100 text-orange-700',
    'Input Error': 'bg-yellow-100 text-yellow-700',
    'Shrinkage': 'bg-purple-100 text-purple-700',
    'Unknown': 'bg-gray-100 text-gray-700'
  }
  return colors[reason] || 'bg-blue-100 text-blue-700'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, opnamesRes] = await Promise.all([
      $api.get('/opname/evaluation/stats'),
      $api.get('/opname/list')
    ])
    stats.value = statsRes.data || {}
    opnames.value = opnamesRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const viewReport = async (opname: any) => {
  try {
    const res = await $api.get(`/opname/variance-report/${opname.id}`)
    selectedReport.value = res.data
    showReportModal.value = true
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load report', color: 'red' })
  }
}

const exportReport = () => {
  window.open(`/api/export/opnames?format=pdf`, '_blank')
}

onMounted(() => {
  fetchData()
})
</script>
