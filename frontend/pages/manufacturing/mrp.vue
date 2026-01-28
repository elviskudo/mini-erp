<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Material Requirements Planning (MRP)</h2>
        <p class="text-gray-500">Plan production, forecast demand, and manage material requirements</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="refreshData" :loading="loading">Refresh</UButton>
        <UButton icon="i-heroicons-play" color="primary" @click="runMRP" :loading="runningMRP">Run MRP</UButton>
      </div>
    </div>

    <!-- MRP Tabs -->
    <UTabs v-model="activeTab" :items="tabs" class="w-full">
      <template #item="{ item }">
        <!-- MRP Run Tab -->
        <div v-if="item.key === 'run'" class="space-y-4 pt-4">
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h3 class="font-semibold">MRP Execution</h3>
                <UBadge v-if="lastRun" color="green" variant="subtle">Last run: {{ lastRun }}</UBadge>
              </div>
            </template>
            <div class="space-y-4">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center p-4 bg-blue-50 rounded-lg">
                  <p class="text-2xl font-bold text-blue-600">{{ stats.pending_orders }}</p>
                  <p class="text-sm text-gray-500">Pending Orders</p>
                </div>
                <div class="text-center p-4 bg-green-50 rounded-lg">
                  <p class="text-2xl font-bold text-green-600">{{ stats.materials_ok }}</p>
                  <p class="text-sm text-gray-500">Materials OK</p>
                </div>
                <div class="text-center p-4 bg-orange-50 rounded-lg">
                  <p class="text-2xl font-bold text-orange-600">{{ stats.shortages }}</p>
                  <p class="text-sm text-gray-500">Shortages</p>
                </div>
                <div class="text-center p-4 bg-purple-50 rounded-lg">
                  <p class="text-2xl font-bold text-purple-600">{{ stats.planned_orders }}</p>
                  <p class="text-sm text-gray-500">Planned Orders</p>
                </div>
              </div>
              <div v-if="mrpResult" class="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p class="font-medium text-green-800">✓ MRP Run Completed</p>
                <p class="text-sm text-green-600">{{ mrpResult.message }}</p>
              </div>
            </div>
          </UCard>
        </div>

        <!-- MPS Tab -->
        <div v-if="item.key === 'mps'" class="space-y-4 pt-4">
          <UCard>
            <template #header><h3 class="font-semibold">Master Production Schedule</h3></template>
            <UTable :columns="mpsColumns" :rows="mpsList" :loading="loading">
              <template #period-data="{ row }">
                <span class="font-mono">{{ row.period }}</span>
              </template>
              <template #quantity-data="{ row }">
                <span class="font-bold">{{ formatNumber(row.quantity) }}</span>
              </template>
            </UTable>
          </UCard>
        </div>

        <!-- Forecast Tab -->
        <div v-if="item.key === 'forecast'" class="space-y-4 pt-4">
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h3 class="font-semibold">Demand Forecasting</h3>
                <UBadge color="blue" variant="subtle">Accuracy: {{ forecastData.accuracy }}</UBadge>
              </div>
            </template>
            <div class="space-y-4">
              <div class="h-64 flex items-end justify-between gap-2 pt-4 px-2">
                <div v-for="f in forecastData.forecast" :key="f.month" class="flex-1 flex flex-col items-center gap-1">
                  <div class="w-full flex gap-1 h-48">
                    <div class="flex-1 bg-blue-500 rounded-t transition-all" :style="{ height: `${(f.predicted / maxForecast) * 100}%` }" title="Predicted"></div>
                    <div class="flex-1 bg-green-500 rounded-t transition-all" :style="{ height: `${(f.actual / maxForecast) * 100}%` }" title="Actual"></div>
                  </div>
                  <p class="text-xs text-gray-500">{{ f.month }}</p>
                </div>
              </div>
              <div class="flex justify-center gap-4 text-sm">
                <span class="flex items-center gap-1"><span class="w-3 h-3 bg-blue-500 rounded"></span> Predicted</span>
                <span class="flex items-center gap-1"><span class="w-3 h-3 bg-green-500 rounded"></span> Actual</span>
              </div>
            </div>
          </UCard>
        </div>

        <!-- Net Requirements Tab -->
        <div v-if="item.key === 'requirements'" class="space-y-4 pt-4">
          <UCard>
            <template #header><h3 class="font-semibold">Net Requirements</h3></template>
            <UTable :columns="reqColumns" :rows="requirementsList" :loading="loading">
              <template #material-data="{ row }">
                <span class="font-medium">{{ row.material }}</span>
              </template>
              <template #shortage-data="{ row }">
                <UBadge :color="row.shortage > 0 ? 'red' : 'green'" variant="subtle">
                  {{ row.shortage > 0 ? `-${row.shortage}` : 'OK' }}
                </UBadge>
              </template>
            </UTable>
          </UCard>
        </div>

        <!-- Exceptions Tab -->
        <div v-if="item.key === 'exceptions'" class="space-y-4 pt-4">
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h3 class="font-semibold">MRP Exceptions & Alerts</h3>
                <UBadge :color="exceptionsList.length > 0 ? 'red' : 'green'" variant="subtle">
                  {{ exceptionsList.length }} Active
                </UBadge>
              </div>
            </template>
            <div class="space-y-2">
              <div v-for="(ex, idx) in exceptionsList" :key="idx" 
                   class="p-3 border rounded-lg flex items-start gap-3"
                   :class="ex.severity === 'HIGH' ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'">
                <UIcon :name="ex.type === 'SHORTAGE' ? 'i-heroicons-exclamation-triangle' : 'i-heroicons-clock'" 
                       :class="ex.severity === 'HIGH' ? 'text-red-500' : 'text-yellow-500'" class="w-5 h-5 mt-0.5" />
                <div>
                  <p class="font-medium" :class="ex.severity === 'HIGH' ? 'text-red-800' : 'text-yellow-800'">{{ ex.message }}</p>
                  <p class="text-xs text-gray-500">Type: {{ ex.type }} | Severity: {{ ex.severity }}</p>
                </div>
              </div>
              <p v-if="!exceptionsList.length" class="text-center text-gray-400 py-8">No active exceptions</p>
            </div>
          </UCard>
        </div>

        <!-- Analytics Tab -->
        <div v-if="item.key === 'analytics'" class="space-y-4 pt-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UCard :ui="{ body: { padding: 'p-6' } }">
              <div class="text-center">
                <p class="text-3xl font-bold text-blue-600">{{ analyticsData.lead_time_variance }}</p>
                <p class="text-sm text-gray-500">Lead Time Variance</p>
                <p class="text-xs text-gray-400 mt-1">ISO 9001 KPI</p>
              </div>
            </UCard>
            <UCard :ui="{ body: { padding: 'p-6' } }">
              <div class="text-center">
                <p class="text-3xl font-bold text-green-600">{{ analyticsData.planning_accuracy }}</p>
                <p class="text-sm text-gray-500">Planning Accuracy</p>
                <p class="text-xs text-gray-400 mt-1">ISO 9001 KPI</p>
              </div>
            </UCard>
            <UCard :ui="{ body: { padding: 'p-6' } }">
              <div class="text-center">
                <p class="text-3xl font-bold" :class="analyticsData.stockout_risk === 'Low' ? 'text-green-600' : 'text-orange-600'">
                  {{ analyticsData.stockout_risk }}
                </p>
                <p class="text-sm text-gray-500">Stockout Risk</p>
              </div>
            </UCard>
          </div>
        </div>
      </template>
    </UTabs>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const runningMRP = ref(false)
const activeTab = ref(0)
const lastRun = ref<string | null>(null)
const mrpResult = ref<any>(null)

const stats = ref({ pending_orders: 5, materials_ok: 42, shortages: 3, planned_orders: 12 })
const mpsList = ref<any[]>([])
const forecastData = ref<any>({ forecast: [], accuracy: '0%' })
const requirementsList = ref<any[]>([])
const exceptionsList = ref<any[]>([])
const analyticsData = ref<any>({})

const tabs = [
  { key: 'run', label: 'MRP Run', icon: 'i-heroicons-play' },
  { key: 'mps', label: 'MPS', icon: 'i-heroicons-calendar' },
  { key: 'forecast', label: 'Forecast', icon: 'i-heroicons-chart-bar' },
  { key: 'requirements', label: 'Net Requirements', icon: 'i-heroicons-cube' },
  { key: 'exceptions', label: 'Exceptions', icon: 'i-heroicons-exclamation-triangle' },
  { key: 'analytics', label: 'Analytics', icon: 'i-heroicons-chart-pie' }
]

const mpsColumns = [
  { key: 'period', label: 'Period', sortable: true },
  { key: 'product', label: 'Product' },
  { key: 'quantity', label: 'Quantity' }
]

const reqColumns = [
  { key: 'material', label: 'Material' },
  { key: 'required', label: 'Required' },
  { key: 'available', label: 'Available' },
  { key: 'shortage', label: 'Status' }
]

const maxForecast = computed(() => {
  const all = forecastData.value.forecast?.flatMap((f: any) => [f.predicted, f.actual]) || [1]
  return Math.max(...all, 1)
})

const formatNumber = (n: number) => new Intl.NumberFormat('id-ID').format(n)

const runMRP = async () => {
  runningMRP.value = true
  try {
    const res = await $api.get('/manufacturing/mrp/run')
    mrpResult.value = res.data
    lastRun.value = new Date().toLocaleTimeString()
    toast.add({ title: 'MRP Run Started', description: res.data?.message || 'Calculation initiated', color: 'green' })
    refreshData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to run MRP', color: 'red' })
  } finally {
    runningMRP.value = false
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    const [mpsRes, forecastRes, reqRes, excRes, analyticsRes] = await Promise.all([
      $api.get('/manufacturing/mrp/mps').catch(() => ({ data: { data: [] } })),
      $api.get('/manufacturing/mrp/forecast').catch(() => ({ data: { forecast: [], accuracy: '0%' } })),
      $api.get('/manufacturing/mrp/requirements').catch(() => ({ data: { data: [] } })),
      $api.get('/manufacturing/mrp/exceptions').catch(() => ({ data: { data: [] } })),
      $api.get('/manufacturing/mrp/analytics').catch(() => ({ data: {} }))
    ])
    mpsList.value = mpsRes.data?.data || mpsRes.data || []
    forecastData.value = forecastRes.data || { forecast: [], accuracy: '0%' }
    requirementsList.value = reqRes.data?.data || reqRes.data || []
    exceptionsList.value = excRes.data?.data || excRes.data || []
    analyticsData.value = analyticsRes.data || {}
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => { refreshData() })
</script>
