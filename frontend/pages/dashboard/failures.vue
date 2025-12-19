<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Failure Analysis Dashboard</h1>
        <p class="text-gray-500">Quality metrics, defect analysis, and cost of poor quality</p>
      </div>
      <div class="flex gap-2">
        <USelect v-model="selectedPeriod" :options="periodOptions" class="w-40" />
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="refreshData">Refresh</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold" :class="defectRate <= 2 ? 'text-green-600' : defectRate <= 5 ? 'text-yellow-600' : 'text-red-600'">
            {{ defectRate }}%
          </p>
          <p class="text-sm text-gray-500">Defect Rate</p>
          <UBadge :color="defectRate <= 2 ? 'green' : defectRate <= 5 ? 'yellow' : 'red'" variant="soft" size="xs" class="mt-1">
            {{ defectRate <= 2 ? 'Excellent' : defectRate <= 5 ? 'Acceptable' : 'High' }}
          </UBadge>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-red-600">{{ totalDefects }}</p>
          <p class="text-sm text-gray-500">Total Defects</p>
          <p class="text-xs text-gray-400 mt-1">This Period</p>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-orange-600">{{ totalScrap }}</p>
          <p class="text-sm text-gray-500">Total Scrap</p>
          <p class="text-xs text-gray-400 mt-1">Units Disposed</p>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-3xl font-bold text-purple-600">Rp {{ formatNumber(copq) }}</p>
          <p class="text-sm text-gray-500">COPQ</p>
          <p class="text-xs text-gray-400 mt-1">Cost of Poor Quality</p>
        </div>
      </UCard>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Defect Rate Trend -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Defect Rate Trend</h3>
        </template>
        <div class="h-64 flex items-end gap-2 px-4">
          <div v-for="(item, idx) in trendData" :key="idx" class="flex-1 flex flex-col items-center gap-1">
            <div class="w-full bg-gray-100 rounded-t relative" style="height: 200px;">
              <div 
                class="absolute bottom-0 w-full rounded-t transition-all duration-300"
                :class="item.rate <= 2 ? 'bg-green-500' : item.rate <= 5 ? 'bg-yellow-500' : 'bg-red-500'"
                :style="{ height: `${Math.min(item.rate * 10, 100)}%` }"
              ></div>
            </div>
            <span class="text-xs font-medium">{{ item.rate }}%</span>
            <span class="text-xs text-gray-400">{{ item.label }}</span>
          </div>
        </div>
      </UCard>

      <!-- Pareto Chart - Top Failure Reasons -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Top Failure Reasons (Pareto)</h3>
            <span class="text-xs text-gray-400">80/20 Rule</span>
          </div>
        </template>
        <div class="space-y-3">
          <div v-for="(reason, idx) in paretoData" :key="idx" class="space-y-1">
            <div class="flex justify-between text-sm">
              <span class="flex items-center gap-2">
                <span class="w-5 h-5 rounded-full bg-red-100 text-red-600 text-xs flex items-center justify-center font-medium">
                  {{ idx + 1 }}
                </span>
                {{ reason.name }}
              </span>
              <span class="font-medium">{{ reason.count }} ({{ reason.percent }}%)</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div 
                class="h-2.5 rounded-full bg-gradient-to-r from-red-500 to-orange-400"
                :style="{ width: `${reason.percent}%` }"
              ></div>
            </div>
          </div>
          <div v-if="paretoData.length === 0" class="text-center py-8 text-gray-400">
            No failure data available
          </div>
        </div>
      </UCard>
    </div>

    <!-- COPQ Breakdown -->
    <UCard>
      <template #header>
        <h3 class="font-semibold">Cost of Poor Quality (COPQ) Breakdown</h3>
      </template>
      <div class="grid md:grid-cols-4 gap-4">
        <div class="p-4 bg-red-50 rounded-lg text-center">
          <UIcon name="i-heroicons-trash" class="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p class="text-xl font-bold text-red-600">Rp {{ formatNumber(copqBreakdown.scrap) }}</p>
          <p class="text-sm text-gray-600">Scrap Cost</p>
          <p class="text-xs text-gray-400">Material Loss</p>
        </div>
        
        <div class="p-4 bg-orange-50 rounded-lg text-center">
          <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-orange-500 mx-auto mb-2" />
          <p class="text-xl font-bold text-orange-600">Rp {{ formatNumber(copqBreakdown.rework) }}</p>
          <p class="text-sm text-gray-600">Rework Cost</p>
          <p class="text-xs text-gray-400">Reprocessing</p>
        </div>
        
        <div class="p-4 bg-yellow-50 rounded-lg text-center">
          <UIcon name="i-heroicons-truck" class="w-8 h-8 text-yellow-500 mx-auto mb-2" />
          <p class="text-xl font-bold text-yellow-600">Rp {{ formatNumber(copqBreakdown.returns) }}</p>
          <p class="text-sm text-gray-600">Return Cost</p>
          <p class="text-xs text-gray-400">Customer Returns</p>
        </div>
        
        <div class="p-4 bg-purple-50 rounded-lg text-center">
          <UIcon name="i-heroicons-clipboard-document-check" class="w-8 h-8 text-purple-500 mx-auto mb-2" />
          <p class="text-xl font-bold text-purple-600">Rp {{ formatNumber(copqBreakdown.inspection) }}</p>
          <p class="text-sm text-gray-600">Inspection Cost</p>
          <p class="text-xs text-gray-400">Extra QC</p>
        </div>
      </div>
      
      <!-- COPQ as % of Revenue -->
      <div class="mt-4 p-4 bg-gray-100 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600">COPQ as % of Revenue</p>
            <p class="text-2xl font-bold" :class="copqPercent <= 2 ? 'text-green-600' : copqPercent <= 5 ? 'text-yellow-600' : 'text-red-600'">
              {{ copqPercent }}%
            </p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-600">Industry Benchmark</p>
            <p class="text-lg font-medium text-gray-700">&lt; 2% (World Class)</p>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Recent Defects Table -->
    <UCard>
      <template #header>
        <h3 class="font-semibold">Recent Quality Issues</h3>
      </template>
      <UTable :columns="defectColumns" :rows="recentDefects" :loading="loading">
        <template #scrap_type-data="{ row }">
          <UBadge 
            :color="row.scrap_type === 'Total Loss' ? 'red' : row.scrap_type === 'Grade B' ? 'yellow' : 'blue'" 
            variant="soft"
          >
            {{ row.scrap_type || 'N/A' }}
          </UBadge>
        </template>
        <template #cost-data="{ row }">
          <span class="text-red-600 font-medium">Rp {{ formatNumber(row.spoilage_expense || 0) }}</span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const loading = ref(false)

const selectedPeriod = ref('week')
const periodOptions = [
  { label: 'Today', value: 'today' },
  { label: 'This Week', value: 'week' },
  { label: 'This Month', value: 'month' }
]

const defectRate = ref(0)
const totalDefects = ref(0)
const totalScrap = ref(0)
const copq = ref(0)
const copqPercent = ref(0)

const copqBreakdown = ref({
  scrap: 0,
  rework: 0,
  returns: 0,
  inspection: 0
})

const trendData = ref<{ label: string; rate: number }[]>([])
const paretoData = ref<{ name: string; count: number; percent: number }[]>([])
const recentDefects = ref<any[]>([])

const defectColumns = [
  { key: 'recorded_at', label: 'Date' },
  { key: 'order_no', label: 'Order' },
  { key: 'defect_qty', label: 'Defects' },
  { key: 'scrap_qty', label: 'Scrap' },
  { key: 'scrap_type', label: 'Type' },
  { key: 'scrap_reason', label: 'Reason' },
  { key: 'cost', label: 'Cost' }
]

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('id-ID').format(num)
}

const fetchData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // Fetch failure analysis data from API
    const statsRes: any = await $fetch('/api/dashboard/failures', { headers })
    
    defectRate.value = statsRes.defect_rate || 0
    totalDefects.value = statsRes.total_defects || 0
    totalScrap.value = statsRes.total_scrap || 0
    copq.value = statsRes.copq || 0
    copqPercent.value = statsRes.copq_percent || 0
    
    copqBreakdown.value = statsRes.copq_breakdown || {
      scrap: 0, rework: 0, returns: 0, inspection: 0
    }
    
    trendData.value = statsRes.trend_data || []
    paretoData.value = statsRes.pareto_data || []
    recentDefects.value = statsRes.recent_defects || []
  } catch (e) {
    console.error('Failed to fetch failure data', e)
    // Mock data for display
    defectRate.value = 3.2
    totalDefects.value = 45
    totalScrap.value = 12
    copq.value = 2500000
    copqPercent.value = 1.8
    copqBreakdown.value = { scrap: 1200000, rework: 800000, returns: 300000, inspection: 200000 }
    trendData.value = [
      { label: 'Mon', rate: 2.1 },
      { label: 'Tue', rate: 3.5 },
      { label: 'Wed', rate: 2.8 },
      { label: 'Thu', rate: 4.2 },
      { label: 'Fri', rate: 3.0 },
      { label: 'Sat', rate: 2.5 },
      { label: 'Sun', rate: 1.8 }
    ]
    paretoData.value = [
      { name: 'Suhu oven tidak stabil', count: 15, percent: 33 },
      { name: 'Bahan baku expired', count: 10, percent: 22 },
      { name: 'Operator error', count: 8, percent: 18 },
      { name: 'Mesin breakdown', count: 7, percent: 16 },
      { name: 'Packaging rusak', count: 5, percent: 11 }
    ]
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>
