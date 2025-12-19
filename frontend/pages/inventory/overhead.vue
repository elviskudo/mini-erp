<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Overhead & Energy Report</h1>
        <p class="text-gray-500">Storage zone energy costs and overhead allocation</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
    </div>

    <!-- Summary Cards -->
    <template v-if="loading">
      <ShimmerLoading type="cards" :count="4" :gridCols="4" />
    </template>
    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <UIcon name="i-heroicons-building-storefront" class="w-8 h-8 text-blue-500 mx-auto mb-2" />
          <p class="text-2xl font-bold text-blue-600">{{ summary.total_zones }}</p>
          <p class="text-sm text-gray-500">Total Zones</p>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <UIcon name="i-heroicons-bolt" class="w-8 h-8 text-yellow-500 mx-auto mb-2" />
          <p class="text-2xl font-bold text-yellow-600">{{ formatNumber(summary.total_monthly_kwh) }}</p>
          <p class="text-sm text-gray-500">Monthly kWh</p>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <UIcon name="i-heroicons-currency-dollar" class="w-8 h-8 text-green-500 mx-auto mb-2" />
          <p class="text-2xl font-bold text-green-600">Rp {{ formatNumber(summary.total_monthly_cost) }}</p>
          <p class="text-sm text-gray-500">Monthly Cost</p>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <UIcon name="i-heroicons-chart-pie" class="w-8 h-8 text-purple-500 mx-auto mb-2" />
          <p class="text-2xl font-bold text-purple-600">{{ summary.utilization_percent }}%</p>
          <p class="text-sm text-gray-500">Utilization</p>
        </div>
      </UCard>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Cost by Zone Type -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Cost by Zone Type</h3>
        </template>
        <div class="space-y-4">
          <div v-for="zone in summary.by_zone_type" :key="zone.zone_type" class="space-y-2">
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-2">
                <UBadge :color="getZoneColor(zone.zone_type)" variant="soft">{{ zone.zone_type }}</UBadge>
                <span class="text-sm text-gray-500">{{ zone.count }} zones</span>
              </div>
              <span class="font-medium">Rp {{ formatNumber(zone.monthly_cost) }}</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div 
                class="h-2 rounded-full"
                :class="getZoneBarColor(zone.zone_type)"
                :style="{ width: `${(zone.monthly_cost / summary.total_monthly_cost * 100) || 0}%` }"
              ></div>
            </div>
          </div>
          <div v-if="!summary.by_zone_type?.length" class="text-center py-8 text-gray-400">
            No zone data available
          </div>
        </div>
      </UCard>

      <!-- Allocation Rates -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Overhead Allocation Rates</h3>
        </template>
        <div class="space-y-4">
          <div class="p-4 bg-blue-50 rounded-lg">
            <p class="text-sm text-blue-600">Simple Rate (All Zones)</p>
            <p class="text-2xl font-bold text-blue-700">Rp {{ formatNumber(allocation.simple_per_unit_rate) }} / unit</p>
          </div>
          
          <div class="border-t pt-4">
            <p class="text-sm font-medium mb-3">Zone-Specific Rates:</p>
            <div class="space-y-2">
              <div v-for="(data, zoneType) in allocation.by_zone_type" :key="zoneType" class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <div>
                  <UBadge :color="getZoneColor(zoneType)" variant="soft" size="xs">{{ zoneType }}</UBadge>
                  <span class="text-xs text-gray-500 ml-2">{{ data.units_stored }} units</span>
                </div>
                <span class="font-medium">Rp {{ formatNumber(data.rate_per_unit) }}/unit</span>
              </div>
            </div>
          </div>
          
          <div class="p-3 bg-yellow-50 rounded-lg text-sm">
            <UIcon name="i-heroicons-light-bulb" class="w-4 h-4 inline text-yellow-600 mr-1" />
            <span class="text-yellow-700">{{ allocation.recommendation }}</span>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Zone Details Table -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Zone Energy Details</h3>
          <UButton size="sm" icon="i-heroicons-plus" @click="showLogModal = true">Log Energy</UButton>
        </div>
      </template>
      <UTable :columns="columns" :rows="zones" :loading="loading">
        <template #zone_type-data="{ row }">
          <UBadge :color="getZoneColor(row.zone_type)" variant="soft">{{ row.zone_type }}</UBadge>
        </template>
        <template #utilization-data="{ row }">
          <div class="w-20">
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  class="h-2 rounded-full bg-primary-500" 
                  :style="{ width: `${row.utilization}%` }"
                ></div>
              </div>
              <span class="text-xs">{{ row.utilization }}%</span>
            </div>
          </div>
        </template>
        <template #efficiency-data="{ row }">
          <UBadge 
            :color="row.efficiency === 'Good' ? 'green' : row.efficiency === 'Near Limit' ? 'yellow' : 'red'" 
            variant="soft"
          >
            {{ row.efficiency }}
          </UBadge>
        </template>
        <template #monthly_cost-data="{ row }">
          <span class="font-medium">Rp {{ formatNumber(row.monthly_cost) }}</span>
        </template>
      </UTable>
    </UCard>

    <!-- Log Energy Modal -->
    <UModal v-model="showLogModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Log Daily Energy Usage</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Select Zone" required>
            <USelect v-model="logForm.zone_id" :options="zoneOptions" placeholder="Choose zone..." />
          </UFormGroup>
          <UFormGroup label="Daily kWh Usage" required>
            <UInput v-model="logForm.daily_kwh" type="number" step="0.1" placeholder="e.g. 45.5" />
          </UFormGroup>
          <UFormGroup label="Current Temperature (°C)">
            <UInput v-model="logForm.current_temp" type="number" step="0.1" placeholder="e.g. 4.5" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showLogModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="submitEnergyLog">Save Log</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const toast = useToast()
const loading = ref(false)
const submitting = ref(false)
const showLogModal = ref(false)

const summary = ref({
  total_zones: 0,
  total_monthly_kwh: 0,
  total_monthly_cost: 0,
  utilization_percent: 0,
  by_zone_type: [] as any[]
})

const allocation = ref({
  total_monthly_overhead: 0,
  simple_per_unit_rate: 0,
  by_zone_type: {} as Record<string, any>,
  recommendation: ''
})

const zones = ref<any[]>([])

const logForm = reactive({
  zone_id: '',
  daily_kwh: 0,
  current_temp: null as number | null
})

const columns = [
  { key: 'zone_name', label: 'Zone' },
  { key: 'zone_type', label: 'Type' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'daily_kwh', label: 'Daily kWh' },
  { key: 'monthly_cost', label: 'Monthly Cost' },
  { key: 'utilization', label: 'Utilization' },
  { key: 'current_temp', label: 'Temp °C' },
  { key: 'efficiency', label: 'Status' }
]

const zoneOptions = computed(() => 
  zones.value.map(z => ({ label: z.zone_name, value: z.id }))
)

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('id-ID').format(num || 0)
}

const getZoneColor = (type: string) => {
  switch (type) {
    case 'AMBIENT': return 'gray'
    case 'CHILLER': return 'blue'
    case 'FROZEN': return 'cyan'
    case 'DANGEROUS': return 'red'
    default: return 'gray'
  }
}

const getZoneBarColor = (type: string) => {
  switch (type) {
    case 'AMBIENT': return 'bg-gray-500'
    case 'CHILLER': return 'bg-blue-500'
    case 'FROZEN': return 'bg-cyan-500'
    case 'DANGEROUS': return 'bg-red-500'
    default: return 'bg-gray-500'
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    const [summaryRes, allocationRes, zonesRes]: any = await Promise.all([
      $fetch('/api/inventory/overhead/summary', { headers }),
      $fetch('/api/inventory/overhead/allocation', { headers }),
      $fetch('/api/inventory/overhead/zones', { headers })
    ])
    
    summary.value = summaryRes
    allocation.value = allocationRes
    zones.value = zonesRes.zones || []
  } catch (e) {
    console.error('Failed to fetch overhead data', e)
  } finally {
    loading.value = false
  }
}

const submitEnergyLog = async () => {
  if (!logForm.zone_id) {
    toast.add({ title: 'Error', description: 'Please select a zone', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/inventory/overhead/log-energy/${logForm.zone_id}`, {
      method: 'POST',
      headers,
      body: {
        daily_kwh: logForm.daily_kwh,
        current_temp: logForm.current_temp
      }
    })
    
    toast.add({ title: 'Success', description: 'Energy logged successfully', color: 'green' })
    showLogModal.value = false
    logForm.zone_id = ''
    logForm.daily_kwh = 0
    logForm.current_temp = null
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to log energy', color: 'red' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
