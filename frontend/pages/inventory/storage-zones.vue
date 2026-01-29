<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Storage Zones</h2>
        <p class="text-gray-500">Manage warehouse storage zones with temperature and energy monitoring</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Add Zone</UButton>
    </div>

    <!-- Zone Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard v-for="stat in zoneStats" :key="stat.type" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div :class="['p-2 rounded-lg', stat.bgColor]">
            <UIcon :name="stat.icon" :class="['w-5 h-5', stat.iconColor]" />
          </div>
          <div>
            <p class="text-2xl font-bold">{{ stat.count }}</p>
            <p class="text-sm text-gray-500">{{ stat.label }}</p>
          </div>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable :columns="columns" :rows="zones" :loading="loading" search-placeholder="Search zones...">
        <template #zone_type-data="{ row }">
          <UBadge :color="getZoneTypeColor(row.zone_type)" variant="soft">
            {{ row.zone_type }}
          </UBadge>
        </template>
        <template #temperature-data="{ row }">
          <div v-if="row.min_temp !== null && row.max_temp !== null" class="text-sm">
            <span class="font-medium">{{ row.min_temp }}°C</span>
            <span class="text-gray-400 mx-1">to</span>
            <span class="font-medium">{{ row.max_temp }}°C</span>
          </div>
          <span v-else class="text-gray-400">N/A</span>
        </template>
        <template #energy-data="{ row }">
          <div v-if="row.daily_kwh_usage > 0" class="text-sm">
            <span class="font-medium">{{ row.daily_kwh_usage }} kWh</span>
            <span class="text-gray-400">/day</span>
          </div>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #cost-data="{ row }">
          <span v-if="row.monthly_energy_cost > 0" class="font-medium text-green-600">
            Rp {{ formatNumber(row.monthly_energy_cost) }}
          </span>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-bolt" color="yellow" variant="ghost" size="xs" @click="openEnergyLog(row)" title="Log Energy" />
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Storage Zone' : 'Add Storage Zone'"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="saveZone"
    >
      <div class="space-y-4">
        <UFormGroup label="Warehouse" required hint="Select parent warehouse" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.warehouse_id" :options="warehouseOptions" placeholder="Select warehouse" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Zone Name" required hint="Unique zone identifier" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.zone_name" placeholder="e.g. Cold Storage A" />
          </UFormGroup>
          <UFormGroup label="Zone Type" required hint="Storage classification" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.zone_type" :options="zoneTypeOptions" />
          </UFormGroup>
        </div>

        <!-- Temperature Settings -->
        <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h4 class="text-sm font-medium text-gray-700 mb-3">Temperature Settings</h4>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Min Temp (°C)" hint="Minimum allowed" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model="form.min_temp" type="number" step="0.1" />
            </UFormGroup>
            <UFormGroup label="Max Temp (°C)" hint="Maximum allowed" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model="form.max_temp" type="number" step="0.1" />
            </UFormGroup>
          </div>
        </div>

        <!-- Capacity -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Capacity (Units)" hint="Max storage capacity" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.capacity_units" type="number" />
          </UFormGroup>
          <UFormGroup label="Electricity Tariff (Rp/kWh)" hint="Cost per kWh" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.electricity_tariff" type="number" step="0.01" />
          </UFormGroup>
        </div>

        <!-- IoT Integration -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Sensor ID" hint="IoT temp sensor" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.sensor_id" placeholder="e.g. SENSOR-001" />
          </UFormGroup>
          <UFormGroup label="Meter ID" hint="Energy meter ID" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.electricity_meter_id" placeholder="e.g. METER-001" />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>

    <!-- Energy Log Modal -->
    <UModal v-model="showEnergyModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Log Daily Energy Usage</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Zone">
            <UInput :model-value="selectedZone?.zone_name" disabled />
          </UFormGroup>
          <UFormGroup label="Daily kWh Usage" required>
            <UInput v-model="energyForm.daily_kwh" type="number" step="0.1" placeholder="Enter kWh" />
          </UFormGroup>
          <p class="text-sm text-gray-500">
            Estimated Monthly Cost: <span class="font-medium text-green-600">Rp {{ formatNumber(estimatedMonthlyCost) }}</span>
          </p>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showEnergyModal = false">Cancel</UButton>
            <UButton @click="saveEnergyLog" :loading="submitting">Save</UButton>
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
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const editMode = ref(false)
const zones = ref<any[]>([])
const warehouses = ref<any[]>([])
const showEnergyModal = ref(false)
const selectedZone = ref<any>(null)

const columns = [
  { key: 'zone_name', label: 'Zone Name' },
  { key: 'zone_type', label: 'Type' },
  { key: 'warehouse_name', label: 'Warehouse' },
  { key: 'temperature', label: 'Temperature Range' },
  { key: 'energy', label: 'Energy Usage' },
  { key: 'cost', label: 'Monthly Cost' },
  { key: 'actions', label: '' }
]

const zoneTypeOptions = [
  { label: 'Ambient (25-30°C)', value: 'Ambient' },
  { label: 'Chiller (2-8°C)', value: 'Chiller' },
  { label: 'Frozen (-18 to -25°C)', value: 'Frozen' },
  { label: 'Dangerous Goods', value: 'Dangerous' }
]

const form = reactive({
  id: '',
  warehouse_id: '',
  zone_name: '',
  zone_type: 'Ambient',
  min_temp: null as number | null,
  max_temp: null as number | null,
  capacity_units: 0,
  electricity_tariff: 1500,
  sensor_id: '',
  electricity_meter_id: ''
})

const energyForm = reactive({
  daily_kwh: 0
})

// Form validation - button enabled only when required fields are filled
const isFormValid = computed(() => {
    return form.warehouse_id !== '' && form.zone_name.trim() !== '' && form.zone_type !== ''
})

const zoneStats = computed(() => {
  const ambient = zones.value.filter(z => z.zone_type === 'Ambient').length
  const chiller = zones.value.filter(z => z.zone_type === 'Chiller').length
  const frozen = zones.value.filter(z => z.zone_type === 'Frozen').length
  const dangerous = zones.value.filter(z => z.zone_type === 'Dangerous').length
  
  return [
    { type: 'Ambient', label: 'Ambient', count: ambient, icon: 'i-heroicons-sun', bgColor: 'bg-yellow-100', iconColor: 'text-yellow-600' },
    { type: 'Chiller', label: 'Chiller', count: chiller, icon: 'i-heroicons-beaker', bgColor: 'bg-blue-100', iconColor: 'text-blue-600' },
    { type: 'Frozen', label: 'Frozen', count: frozen, icon: 'i-heroicons-cube', bgColor: 'bg-cyan-100', iconColor: 'text-cyan-600' },
    { type: 'Dangerous', label: 'Dangerous', count: dangerous, icon: 'i-heroicons-exclamation-triangle', bgColor: 'bg-red-100', iconColor: 'text-red-600' }
  ]
})

const warehouseOptions = computed(() => {
  return warehouses.value.map(w => ({ label: `${w.code} - ${w.name}`, value: w.id }))
})

const estimatedMonthlyCost = computed(() => {
  return (energyForm.daily_kwh * 30 * (selectedZone.value?.electricity_tariff || 1500))
})

const resetForm = () => {
  Object.assign(form, {
    id: '',
    warehouse_id: '',
    zone_name: '',
    zone_type: 'Ambient',
    min_temp: null,
    max_temp: null,
    capacity_units: 0,
    electricity_tariff: 1500,
    sensor_id: '',
    electricity_meter_id: ''
  })
}

const getZoneTypeColor = (type: string) => {
  switch (type) {
    case 'Ambient': return 'yellow'
    case 'Chiller': return 'blue'
    case 'Frozen': return 'cyan'
    case 'Dangerous': return 'red'
    default: return 'gray'
  }
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('id-ID').format(num)
}

// Helper to safely extract array from API response
const extractArray = (res: any): any[] => {
  if (Array.isArray(res)) return res
  if (res?.data && Array.isArray(res.data)) return res.data
  if (res?.data?.data && Array.isArray(res.data.data)) return res.data.data
  return []
}

const fetchData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // Use $api if available or $fetch with proper handling
    // We already use useNuxtApp().$api in other components, standardizing here would be better but keeping minimal changes
    const [zonesRes, warehousesRes] = await Promise.all([
      $fetch('/api/inventory/storage-zones', { headers }),
      $fetch('/api/inventory/warehouses', { headers })
    ])
    
    // Unwrap data using helper
    const zonesData = extractArray(zonesRes)
    const warehousesData = extractArray(warehousesRes)

    warehouses.value = warehousesData
    
    zones.value = zonesData.map((z: any) => ({
      ...z,
      zone_name: z.zone_name || z.name || 'Unknown Zone',
      zone_type: z.zone_type || z.type || 'Ambient',
      min_temp: z.min_temp ?? 25,
      max_temp: z.max_temp ?? 30,
      warehouse_name: warehouses.value.find((w: any) => w.id === z.warehouse_id)?.name || 'N/A'
    }))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  resetForm()
  editMode.value = false
  isOpen.value = true
}

const openEdit = (row: any) => {
  Object.assign(form, row)
  editMode.value = true
  isOpen.value = true
}

const openEnergyLog = (row: any) => {
  selectedZone.value = row
  energyForm.daily_kwh = row.daily_kwh_usage || 0
  showEnergyModal.value = true
}

const saveZone = async () => {
  if (!form.warehouse_id || !form.zone_name) {
    toast.add({ title: 'Error', description: 'Please fill required fields', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    if (editMode.value) {
      await $fetch(`/api/inventory/storage-zones/${form.id}`, {
        method: 'PUT',
        body: form,
        headers
      })
      toast.add({ title: 'Updated', description: 'Storage zone updated.', color: 'green' })
    } else {
      await $fetch('/api/inventory/storage-zones', {
        method: 'POST',
        body: form,
        headers
      })
      toast.add({ title: 'Created', description: 'Storage zone created.', color: 'green' })
    }
    isOpen.value = false
    fetchData()
    resetForm()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to save zone.', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const saveEnergyLog = async () => {
  if (!selectedZone.value) return
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const monthlyCost = energyForm.daily_kwh * 30 * selectedZone.value.electricity_tariff
    
    await $fetch(`/api/inventory/storage-zones/${selectedZone.value.id}`, {
      method: 'PUT',
      body: {
        ...selectedZone.value,
        daily_kwh_usage: energyForm.daily_kwh,
        monthly_energy_cost: monthlyCost
      },
      headers
    })
    
    toast.add({ title: 'Saved', description: 'Energy usage logged.', color: 'green' })
    showEnergyModal.value = false
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to log energy.', color: 'red' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
