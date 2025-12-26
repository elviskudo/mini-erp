<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Overhead & Energy Report</h1>
        <p class="text-gray-500">Storage zone energy costs and overhead allocation</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
      </div>
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
            <UIcon name="i-heroicons-building-storefront" class="w-12 h-12 mx-auto mb-2" />
            <p>No zone data available</p>
            <UButton size="sm" variant="link" to="/inventory/storage-zones">Create Storage Zones →</UButton>
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
          
          <div v-if="Object.keys(allocation.by_zone_type || {}).length" class="border-t pt-4">
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
            <span class="text-yellow-700">{{ allocation.recommendation || 'Create storage zones and log energy to see allocation rates.' }}</span>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Zone Details DataTable -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Zone Energy Details</h3>
          <div class="flex gap-2">
            <UButton size="sm" variant="outline" to="/inventory/storage-zones">Manage Zones</UButton>
            <UButton size="sm" icon="i-heroicons-plus" @click="showLogModal = true" :disabled="!zones.length">Log Energy</UButton>
          </div>
        </div>
      </template>
      
      <DataTable 
        :columns="columns" 
        :rows="zones" 
        :loading="loading"
        searchable
        :search-keys="['zone_name', 'warehouse', 'zone_type']"
        empty-message="No storage zones found. Create zones to track energy costs."
      >
        <template #zone_type-data="{ row }">
          <UBadge :color="getZoneColor(row.zone_type)" variant="soft">{{ row.zone_type }}</UBadge>
        </template>
        <template #daily_kwh-data="{ row }">
          <span class="font-mono">{{ row.daily_kwh || 0 }} kWh</span>
        </template>
        <template #monthly_cost-data="{ row }">
          <span class="font-medium text-green-600">Rp {{ formatNumber(row.monthly_cost || 0) }}</span>
        </template>
        <template #utilization-data="{ row }">
          <div class="flex items-center gap-2">
            <div class="w-16 bg-gray-200 rounded-full h-2">
              <div class="h-2 rounded-full bg-primary-500" :style="{ width: `${row.utilization || 0}%` }"></div>
            </div>
            <span class="text-xs">{{ row.utilization || 0 }}%</span>
          </div>
        </template>
        <template #current_temp-data="{ row }">
          <span v-if="row.current_temp != null" class="font-mono">{{ row.current_temp }}°C</span>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #efficiency-data="{ row }">
          <UBadge 
            :color="row.efficiency === 'Good' ? 'green' : row.efficiency === 'Near Limit' ? 'yellow' : 'red'" 
            variant="subtle"
          >
            {{ row.efficiency || 'N/A' }}
          </UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-bolt" color="yellow" variant="ghost" size="xs" @click="openLogForZone(row)" title="Log Energy" />
        </template>
      </DataTable>
      
      <!-- Empty State -->
      <div v-if="!loading && !zones.length" class="text-center py-12">
        <UIcon name="i-heroicons-building-storefront" class="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 class="text-lg font-medium text-gray-600 mb-2">No Storage Zones Yet</h3>
        <p class="text-gray-500 mb-4">Create storage zones to start tracking energy costs</p>
        <UButton to="/inventory/storage-zones" icon="i-heroicons-plus">Create Storage Zone</UButton>
      </div>
    </UCard>

    <!-- Log Energy Modal -->
    <UModal v-model="showLogModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center">
              <UIcon name="i-heroicons-bolt" class="text-yellow-600 w-6 h-6" />
            </div>
            <h3 class="text-lg font-semibold">Log Daily Energy Usage</h3>
          </div>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Select Zone" required>
            <USelect v-model="logForm.zone_id" :options="zoneOptions" placeholder="Choose zone..." />
          </UFormGroup>
          <UFormGroup label="Daily kWh Usage" required hint="Enter meter reading" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="logForm.daily_kwh" type="number" step="0.1" placeholder="e.g. 45.5" />
          </UFormGroup>
          <UFormGroup label="Current Temperature (°C)" hint="For cold storage monitoring" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="logForm.current_temp" type="number" step="0.1" placeholder="e.g. 4.5" />
          </UFormGroup>
          
          <div v-if="estimatedCost > 0" class="p-3 bg-green-50 rounded-lg">
            <p class="text-sm text-green-700">
              <strong>Estimated Monthly Cost:</strong> Rp {{ formatNumber(estimatedCost) }}
            </p>
          </div>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showLogModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="submitEnergyLog" :disabled="!logForm.zone_id">Save Log</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({
  middleware: 'auth'
})

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
  { key: 'zone_name', label: 'Zone', sortable: true },
  { key: 'zone_type', label: 'Type' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'daily_kwh', label: 'Daily kWh', sortable: true },
  { key: 'monthly_cost', label: 'Monthly Cost', sortable: true },
  { key: 'utilization', label: 'Utilization' },
  { key: 'current_temp', label: 'Temp °C' },
  { key: 'efficiency', label: 'Status' },
  { key: 'actions', label: '' }
]

const zoneOptions = computed(() => 
  zones.value.map(z => ({ label: `${z.zone_name} (${z.zone_type})`, value: z.id }))
)

const selectedZone = computed(() => 
  zones.value.find(z => z.id === logForm.zone_id)
)

const estimatedCost = computed(() => {
  if (!logForm.daily_kwh || !selectedZone.value) return 0
  return logForm.daily_kwh * 30 * (selectedZone.value.tariff_per_kwh || 1500)
})

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('id-ID').format(num || 0)
}

const getZoneColor = (type: string) => {
  const t = type?.toUpperCase() || ''
  if (t.includes('AMBIENT')) return 'gray'
  if (t.includes('CHILLER')) return 'blue'
  if (t.includes('FROZEN')) return 'cyan'
  if (t.includes('DANGEROUS')) return 'red'
  return 'gray'
}

const getZoneBarColor = (type: string) => {
  const t = type?.toUpperCase() || ''
  if (t.includes('AMBIENT')) return 'bg-gray-500'
  if (t.includes('CHILLER')) return 'bg-blue-500'
  if (t.includes('FROZEN')) return 'bg-cyan-500'
  if (t.includes('DANGEROUS')) return 'bg-red-500'
  return 'bg-gray-500'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [summaryRes, allocationRes, zonesRes]: any = await Promise.all([
      $api.get('/inventory/overhead/summary'),
      $api.get('/inventory/overhead/allocation'),
      $api.get('/inventory/overhead/zones')
    ])
    
    summary.value = summaryRes.data || { total_zones: 0, total_monthly_kwh: 0, total_monthly_cost: 0, utilization_percent: 0, by_zone_type: [] }
    allocation.value = allocationRes.data || { simple_per_unit_rate: 0, by_zone_type: {}, recommendation: '' }
    zones.value = zonesRes.data?.zones || []
  } catch (e) {
    console.error('Failed to fetch overhead data', e)
  } finally {
    loading.value = false
  }
}

const openLogForZone = (zone: any) => {
  logForm.zone_id = zone.id
  logForm.daily_kwh = zone.daily_kwh || 0
  logForm.current_temp = zone.current_temp
  showLogModal.value = true
}

const submitEnergyLog = async () => {
  if (!logForm.zone_id) {
    toast.add({ title: 'Error', description: 'Please select a zone', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    await $api.post(`/inventory/overhead/log-energy/${logForm.zone_id}`, {
      daily_kwh: logForm.daily_kwh,
      current_temp: logForm.current_temp
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

// Export functions
const exportData = (format: string) => {
  const data = zones.value.map((z: any) => ({
    'Zone': z.zone_name,
    'Type': z.zone_type,
    'Warehouse': z.warehouse,
    'Daily kWh': z.daily_kwh || 0,
    'Monthly Cost': z.monthly_cost || 0,
    'Utilization %': z.utilization || 0,
    'Temperature': z.current_temp || '-',
    'Status': z.efficiency || 'N/A'
  }))
  
  if (format === 'csv') exportToCSV(data, 'overhead_report')
  else if (format === 'xlsx') exportToXLSX(data, 'overhead_report')
  else if (format === 'pdf') exportToPDF(data, 'Overhead & Energy Report', 'overhead_report')
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
  fetchData()
})
</script>
