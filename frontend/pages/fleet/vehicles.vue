<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Vehicles</h2>
        <p class="text-gray-500 text-small">Manage your fleet vehicles</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }" :disabled="vehicles.length === 0">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" :disabled="vehicles.length === 0">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchVehicles">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Vehicle</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xl font-bold">{{ vehicles.length }}</p>
          <p class="text-xs text-gray-500">Total</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xl font-bold text-green-600">{{ vehicles.filter(v => v.status === 'AVAILABLE').length }}</p>
          <p class="text-xs text-gray-500">Available</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xl font-bold text-blue-600">{{ vehicles.filter(v => v.status === 'IN_USE').length }}</p>
          <p class="text-xs text-gray-500">In Use</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xl font-bold text-orange-600">{{ vehicles.filter(v => v.status === 'MAINTENANCE').length }}</p>
          <p class="text-xs text-gray-500">Maintenance</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xl font-bold text-red-600">{{ vehicles.filter(v => v.status === 'BROKEN').length }}</p>
          <p class="text-xs text-gray-500">Broken</p>
        </div>
      </UCard>
    </div>

    <!-- Data Table -->
    <UCard>
      <DataTable :columns="columns" :rows="vehicles" :loading="loading" searchable :search-keys="['code', 'plate_number', 'brand', 'model']" empty-message="No vehicles yet. Add your first vehicle to begin.">
        <template #code-data="{ row }">
          <div>
            <p class="font-medium font-mono">{{ row.code }}</p>
            <p class="text-xs text-gray-400">{{ row.plate_number }}</p>
          </div>
        </template>
        <template #brand-data="{ row }">
          <div>
            <p class="font-medium">{{ row.brand }} {{ row.model }}</p>
            <p class="text-xs text-gray-400">{{ row.year || '-' }} | {{ row.vehicle_type || row.category }}</p>
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ formatStatus(row.status) }}</UBadge>
        </template>
        <template #current_odometer-data="{ row }">
          <span class="font-mono text-sm">{{ row.current_odometer?.toLocaleString() || 0 }} km</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteVehicle(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingVehicle ? 'Edit Vehicle' : 'Add Vehicle'" :loading="saving" @submit="saveVehicle">
      <UFormGroup label="Plate Number" required hint="e.g. B 1234 ABC">
        <UInput v-model="form.plate_number" placeholder="B 1234 ABC" />
      </UFormGroup>
      <UFormGroup label="Brand" required>
        <UInput v-model="form.brand" placeholder="Toyota" />
      </UFormGroup>
      <UFormGroup label="Model" required>
        <UInput v-model="form.model" placeholder="Avanza" />
      </UFormGroup>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Year">
          <UInput v-model.number="form.year" type="number" placeholder="2023" />
        </UFormGroup>
        <UFormGroup label="Color">
          <UInput v-model="form.color" placeholder="White" />
        </UFormGroup>
      </div>
      <UFormGroup label="Vehicle Type">
        <USelect v-model="form.vehicle_type" :options="vehicleTypeOptions" />
      </UFormGroup>
      <UFormGroup label="Category">
        <USelect v-model="form.category" :options="categoryOptions" />
      </UFormGroup>
      <UFormGroup label="Capacity" hint="e.g. 5 passengers or 2 tons">
        <UInput v-model="form.capacity" placeholder="5 passengers" />
      </UFormGroup>
      <UFormGroup label="Fuel Type">
        <USelect v-model="form.fuel_type" :options="fuelTypeOptions" />
      </UFormGroup>
      <UDivider label="Registration" />
      <UFormGroup label="Chassis Number">
        <UInput v-model="form.chassis_number" placeholder="MHFM1BA3J..." />
      </UFormGroup>
      <UFormGroup label="Engine Number">
        <UInput v-model="form.engine_number" placeholder="2NR-..." />
      </UFormGroup>
      <UFormGroup label="STNK Number">
        <UInput v-model="form.stnk_number" />
      </UFormGroup>
      <UFormGroup label="BPKB Number">
        <UInput v-model="form.bpkb_number" />
      </UFormGroup>
      <UDivider label="Purchase Info" />
      <UFormGroup label="Purchase Date">
        <UInput v-model="form.purchase_date" type="date" />
      </UFormGroup>
      <UFormGroup label="Purchase Cost">
        <UInput v-model.number="form.purchase_cost" type="number" placeholder="0" />
      </UFormGroup>
      <UFormGroup label="Current Odometer (km)">
        <UInput v-model.number="form.current_odometer" type="number" placeholder="0" />
      </UFormGroup>
      <UFormGroup label="Status">
        <USelect v-model="form.status" :options="statusOptions" />
      </UFormGroup>
      <UFormGroup label="Notes">
        <UTextarea v-model="form.notes" :rows="2" />
      </UFormGroup>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const isSlideoverOpen = ref(false)
const editingVehicle = ref<any>(null)
const vehicles = ref<any[]>([])

const columns = [
  { key: 'code', label: 'Code / Plate' },
  { key: 'brand', label: 'Vehicle' },
  { key: 'status', label: 'Status' },
  { key: 'current_odometer', label: 'Odometer' },
  { key: 'actions', label: '' }
]

const vehicleTypeOptions = ['Car', 'Truck', 'Van', 'Pickup', 'Bus', 'Motorcycle', 'Other']
const categoryOptions = [
  { label: 'Operational', value: 'OPERATIONAL' },
  { label: 'Logistics', value: 'LOGISTICS' },
  { label: 'Rental', value: 'RENTAL' },
  { label: 'Executive', value: 'EXECUTIVE' },
  { label: 'Other', value: 'OTHER' }
]
const fuelTypeOptions = ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'LPG']
const statusOptions = [
  { label: 'Available', value: 'AVAILABLE' },
  { label: 'In Use', value: 'IN_USE' },
  { label: 'Maintenance', value: 'MAINTENANCE' },
  { label: 'Broken', value: 'BROKEN' },
  { label: 'Retired', value: 'RETIRED' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  plate_number: '', brand: '', model: '', year: null as number | null, color: '',
  vehicle_type: 'Car', category: 'OPERATIONAL', capacity: '', fuel_type: 'Gasoline',
  chassis_number: '', engine_number: '', stnk_number: '', bpkb_number: '',
  purchase_date: '', purchase_cost: 0, current_odometer: 0, status: 'AVAILABLE', notes: ''
})

const fetchVehicles = async () => {
  loading.value = true
  try {
    const res = await $api.get('/fleet/vehicles')
    vehicles.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingVehicle.value = null
  Object.assign(form, {
    plate_number: '', brand: '', model: '', year: null, color: '',
    vehicle_type: 'Car', category: 'OPERATIONAL', capacity: '', fuel_type: 'Gasoline',
    chassis_number: '', engine_number: '', stnk_number: '', bpkb_number: '',
    purchase_date: '', purchase_cost: 0, current_odometer: 0, status: 'AVAILABLE', notes: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (vehicle: any) => {
  editingVehicle.value = vehicle
  Object.assign(form, {
    plate_number: vehicle.plate_number, brand: vehicle.brand, model: vehicle.model,
    year: vehicle.year, color: vehicle.color || '', vehicle_type: vehicle.vehicle_type || 'Car',
    category: vehicle.category || 'OPERATIONAL', capacity: vehicle.capacity || '',
    fuel_type: vehicle.fuel_type || 'Gasoline', chassis_number: vehicle.chassis_number || '',
    engine_number: vehicle.engine_number || '', stnk_number: vehicle.stnk_number || '',
    bpkb_number: vehicle.bpkb_number || '', purchase_date: vehicle.purchase_date?.split('T')[0] || '',
    purchase_cost: vehicle.purchase_cost || 0, current_odometer: vehicle.current_odometer || 0,
    status: vehicle.status, notes: vehicle.notes || ''
  })
  isSlideoverOpen.value = true
}

const saveVehicle = async () => {
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.purchase_date) delete (payload as any).purchase_date
    if (!payload.year) delete (payload as any).year
    
    if (editingVehicle.value) {
      await $api.put(`/fleet/vehicles/${editingVehicle.value.id}`, payload)
      toast.add({ title: 'Vehicle updated!' })
    } else {
      await $api.post('/fleet/vehicles', payload)
      toast.add({ title: 'Vehicle created!' })
    }
    isSlideoverOpen.value = false
    fetchVehicles()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteVehicle = async (vehicle: any) => {
  if (!confirm(`Delete vehicle "${vehicle.plate_number}"?`)) return
  try {
    await $api.delete(`/fleet/vehicles/${vehicle.id}`)
    toast.add({ title: 'Vehicle deleted!' })
    fetchVehicles()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' })
  }
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    AVAILABLE: 'green', IN_USE: 'blue', MAINTENANCE: 'orange', BROKEN: 'red', RETIRED: 'gray'
  }
  return colors[status] || 'gray'
}

const formatStatus = (status: string) => {
  const labels: Record<string, string> = {
    AVAILABLE: 'Available', IN_USE: 'In Use', MAINTENANCE: 'Maintenance', BROKEN: 'Broken', RETIRED: 'Retired'
  }
  return labels[status] || status
}

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)

const exportData = (format: string) => {
  const data = vehicles.value.map((v: any) => ({
    'Code': v.code || '',
    'Plate Number': v.plate_number,
    'Brand': v.brand,
    'Model': v.model,
    'Year': v.year || '',
    'Type': v.vehicle_type || '',
    'Category': v.category || '',
    'Status': formatStatus(v.status),
    'Odometer': v.current_odometer || 0,
    'Purchase Cost': v.purchase_cost || 0
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `vehicles.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Vehicles exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Vehicles</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Fleet Vehicles Report</h1>
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

onMounted(() => {
  fetchVehicles()
})
</script>
