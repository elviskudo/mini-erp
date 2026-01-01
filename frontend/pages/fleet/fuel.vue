<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Fuel Logs</h2>
        <p class="text-gray-500">Track fuel purchases and consumption</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchFuelLogs">Refresh</UButton>
        <UButton icon="i-heroicons-user-group" variant="outline" @click="showDriverModal = true">Drivers</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Fuel Log</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-primary-500">{{ formatCurrency(totalCost) }}</p>
          <p class="text-sm text-gray-500">Total Fuel Cost</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-500">{{ totalLiters.toFixed(1) }} L</p>
          <p class="text-sm text-gray-500">Total Liters</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-green-500">{{ avgEfficiency.toFixed(1) }} km/L</p>
          <p class="text-sm text-gray-500">Avg Fuel Efficiency</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-500">{{ fuelLogs.length }}</p>
          <p class="text-sm text-gray-500">Total Records</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="fuelLogs" :loading="loading" searchable :search-keys="['gas_station', 'notes']" empty-message="No fuel logs yet.">
        <template #vehicle_id-data="{ row }">
          <p class="font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #driver_id-data="{ row }">
          <p class="text-sm">{{ getDriverName(row.driver_id) }}</p>
        </template>
        <template #date-data="{ row }">
          <p class="text-sm">{{ formatDate(row.date) }}</p>
        </template>
        <template #liters-data="{ row }">
          <p class="font-medium">{{ row.liters?.toFixed(2) }} L</p>
        </template>
        <template #total_cost-data="{ row }">
          <p class="font-medium text-green-600">{{ formatCurrency(row.total_cost) }}</p>
        </template>
        <template #fuel_efficiency-data="{ row }">
          <UBadge v-if="row.fuel_efficiency" :color="getEfficiencyColor(row.fuel_efficiency)" variant="subtle">
            {{ row.fuel_efficiency?.toFixed(1) }} km/L
          </UBadge>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #receipt_url-data="{ row }">
          <UButton v-if="row.receipt_url" size="xs" icon="i-heroicons-document" variant="ghost" :to="row.receipt_url" target="_blank">View</UButton>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteFuelLog(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Fuel Log Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingLog ? 'Edit Fuel Log' : 'Add Fuel Log'" :loading="saving" @submit="saveFuelLog" size="lg">
      <UFormGroup label="Vehicle" required hint="Select vehicle being refueled">
        <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." />
      </UFormGroup>

      <UFormGroup label="Driver" hint="Driver who refueled (optional)">
        <USelect v-model="form.driver_id" :options="driverOptions" placeholder="Select driver..." />
      </UFormGroup>

      <UFormGroup label="Date" required hint="Date of refueling">
        <UInput v-model="form.date" type="date" />
      </UFormGroup>

      <UFormGroup label="Odometer (km)" required hint="Current odometer reading">
        <UInput v-model.number="form.odometer" type="number" placeholder="e.g. 45000" />
      </UFormGroup>

      <UDivider label="Fuel Details" />

      <UFormGroup label="Fuel Type" hint="Type of fuel">
        <USelect v-model="form.fuel_type" :options="fuelTypeOptions" />
      </UFormGroup>

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Liters" required hint="Amount of fuel purchased">
          <UInput v-model.number="form.liters" type="number" step="0.01" placeholder="e.g. 45.5" />
        </UFormGroup>
        <UFormGroup label="Price per Liter" required hint="Price in Rupiah">
          <UInput v-model.number="form.price_per_liter" type="number" placeholder="e.g. 13000" />
        </UFormGroup>
      </div>

      <UFormGroup label="Total Cost" hint="Auto-calculated from liters × price">
        <UInput :model-value="calculatedTotalCost" disabled class="bg-gray-50" />
      </UFormGroup>

      <UDivider label="Location" />

      <UFormGroup label="Gas Station" required hint="Name of gas station">
        <UInput v-model="form.gas_station" placeholder="e.g. Pertamina, Shell, BP" />
      </UFormGroup>

      <UDivider label="Receipt Upload" />

      <UFormGroup label="Receipt Image" hint="Upload receipt from Cloudinary">
        <div class="space-y-2">
          <div 
            class="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer hover:border-primary-500 transition-colors"
            :class="{ 'border-green-500 bg-green-50': form.receipt_url }"
            @click="triggerFileUpload"
            @drop.prevent="handleFileDrop"
            @dragover.prevent
          >
            <input ref="fileInput" type="file" class="hidden" accept="image/*,.pdf" @change="handleFileSelect" />
            <div v-if="uploading" class="flex items-center justify-center gap-2">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
              <span>Uploading...</span>
            </div>
            <div v-else-if="form.receipt_url" class="space-y-2">
              <UIcon name="i-heroicons-check-circle" class="text-green-500 text-2xl" />
              <p class="text-sm text-green-600">Receipt uploaded!</p>
              <img v-if="isImageUrl(form.receipt_url)" :src="form.receipt_url" class="max-h-24 mx-auto rounded" />
              <a v-else :href="form.receipt_url" target="_blank" class="text-primary-500 underline text-sm">View document</a>
            </div>
            <div v-else>
              <UIcon name="i-heroicons-cloud-arrow-up" class="text-3xl text-gray-400" />
              <p class="text-sm text-gray-500 mt-2">Click or drag to upload receipt image/PDF</p>
            </div>
          </div>
          <UInput v-model="form.receipt_url" placeholder="Or paste receipt URL directly" size="sm" />
        </div>
      </UFormGroup>

      <UFormGroup label="Notes" hint="Additional notes about this refueling">
        <UTextarea v-model="form.notes" :rows="2" placeholder="e.g. Full tank, premium fuel, etc." />
      </UFormGroup>
    </FormSlideover>

    <!-- Driver Management Modal -->
    <UModal v-model="showDriverModal" :ui="{ width: 'sm:max-w-2xl' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{{ editingDriver ? 'Edit Driver' : 'Add Driver' }}</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="closeDriverModal" />
          </div>
        </template>
        <div class="space-y-4 max-h-[70vh] overflow-y-auto">
          <UFormGroup label="Name" required hint="Driver's full legal name">
            <UInput v-model="driverForm.name" placeholder="e.g. Budi Santoso" />
          </UFormGroup>
          <UFormGroup label="Phone Number" required hint="Active phone number">
            <UInput v-model="driverForm.phone" placeholder="e.g. 081234567890" />
          </UFormGroup>
          <UFormGroup label="Card ID Number (KTP)" required hint="16-digit KTP number">
            <UInput v-model="driverForm.card_id_number" placeholder="e.g. 3175012345678901" />
          </UFormGroup>
          <UFormGroup label="Employment Status" required hint="Type of employment">
            <USelect v-model="driverForm.employment_status" :options="employmentOptions" placeholder="Select..." />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="License Number (SIM)" required hint="SIM number">
              <UInput v-model="driverForm.license_number" placeholder="e.g. 123456789012" />
            </UFormGroup>
            <UFormGroup label="License Type" required hint="Type of license">
              <USelect v-model="driverForm.license_type" :options="licenseOptions" placeholder="Select..." />
            </UFormGroup>
          </div>
          <div class="flex justify-end gap-2 pt-4 border-t">
            <UButton v-if="editingDriver" variant="outline" @click="cancelEditDriver">Cancel</UButton>
            <UButton @click="saveDriver" :loading="savingDriver">{{ editingDriver ? 'Update' : 'Add' }} Driver</UButton>
          </div>
          
          <UDivider label="Existing Drivers" />
          <div class="divide-y max-h-48 overflow-y-auto">
            <div v-for="driver in drivers" :key="driver.id" class="py-2 flex items-center justify-between">
              <div>
                <p class="font-medium">{{ driver.code }} - {{ driver.name }}</p>
                <p class="text-xs text-gray-400">📞 {{ driver.phone || 'No phone' }}</p>
              </div>
              <div class="flex gap-1">
                <UButton icon="i-heroicons-pencil" size="xs" variant="ghost" @click="editDriver(driver)" />
                <UButton icon="i-heroicons-trash" size="xs" variant="ghost" color="red" @click="deleteDriver(driver)" />
              </div>
            </div>
            <p v-if="drivers.length === 0" class="py-4 text-center text-gray-400">No drivers yet</p>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const savingDriver = ref(false)
const uploading = ref(false)
const isSlideoverOpen = ref(false)
const editingLog = ref<any>(null)
const fuelLogs = ref<any[]>([])
const vehicles = ref<any[]>([])
const drivers = ref<any[]>([])
const showDriverModal = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const editingDriver = ref<any>(null)
const driverForm = reactive({
  name: '', phone: '', card_id_number: '', employment_status: '', license_number: '', license_type: ''
})

const columns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'driver_id', label: 'Driver' },
  { key: 'date', label: 'Date' },
  { key: 'liters', label: 'Liters' },
  { key: 'total_cost', label: 'Total Cost' },
  { key: 'fuel_efficiency', label: 'Efficiency' },
  { key: 'receipt_url', label: 'Receipt' },
  { key: 'actions', label: '' }
]

const fuelTypeOptions = [
  { label: 'Pertalite', value: 'Pertalite' },
  { label: 'Pertamax', value: 'Pertamax' },
  { label: 'Pertamax Turbo', value: 'Pertamax Turbo' },
  { label: 'Shell V-Power', value: 'Shell V-Power' },
  { label: 'Dexlite', value: 'Dexlite' },
  { label: 'Solar', value: 'Solar' },
  { label: 'Gasoline', value: 'Gasoline' }
]

const employmentOptions = [
  { label: 'Permanent', value: 'PERMANENT' },
  { label: 'Contract', value: 'CONTRACT' },
  { label: 'Freelance', value: 'FREELANCE' }
]

const licenseOptions = [
  { label: 'SIM A - Personal Car', value: 'A' },
  { label: 'SIM B1 - Truck/Bus', value: 'B1' },
  { label: 'SIM B2 - Trailer/Tank', value: 'B2' },
  { label: 'SIM C - Motorcycle', value: 'C' }
]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const driverOptions = computed(() => [
  { label: '-- No Driver --', value: null },
  ...drivers.value.map((d: any) => ({ label: `${d.code} - ${d.name}`, value: d.id }))
])

const totalCost = computed(() => fuelLogs.value.reduce((sum: number, log: any) => sum + (log.total_cost || 0), 0))
const totalLiters = computed(() => fuelLogs.value.reduce((sum: number, log: any) => sum + (log.liters || 0), 0))
const avgEfficiency = computed(() => {
  const withEff = fuelLogs.value.filter((l: any) => l.fuel_efficiency && l.fuel_efficiency > 0)
  if (withEff.length === 0) return 0
  return withEff.reduce((sum: number, l: any) => sum + l.fuel_efficiency, 0) / withEff.length
})

const form = reactive({
  vehicle_id: '',
  driver_id: null as string | null,
  date: '',
  odometer: null as number | null,
  fuel_type: 'Pertalite',
  liters: null as number | null,
  price_per_liter: null as number | null,
  gas_station: '',
  receipt_url: '',
  notes: ''
})

const calculatedTotalCost = computed(() => {
  if (form.liters && form.price_per_liter) {
    return formatCurrency(form.liters * form.price_per_liter)
  }
  return 'Rp 0'
})

const fetchFuelLogs = async () => {
  loading.value = true
  try {
    const res = await $api.get('/fleet/fuel-logs')
    fuelLogs.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchVehicles = async () => {
  try { vehicles.value = (await $api.get('/fleet/vehicles')).data } catch (e) { console.error(e) }
}

const fetchDrivers = async () => {
  try { drivers.value = (await $api.get('/fleet/drivers')).data } catch (e) { console.error(e) }
}

const getVehicleName = (id: string) => vehicles.value.find((v: any) => v.id === id)?.plate_number || '-'
const getDriverName = (id: string) => drivers.value.find((d: any) => d.id === id)?.name || '-'
const getEfficiencyColor = (eff: number) => eff >= 12 ? 'green' : eff >= 8 ? 'yellow' : 'red'
const isImageUrl = (url: string) => /\.(jpg|jpeg|png|gif|webp)$/i.test(url)

const openCreate = () => {
  editingLog.value = null
  Object.assign(form, {
    vehicle_id: '', driver_id: null, date: new Date().toISOString().split('T')[0],
    odometer: null, fuel_type: 'Pertalite', liters: null, price_per_liter: null,
    gas_station: '', receipt_url: '', notes: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (log: any) => {
  editingLog.value = log
  Object.assign(form, {
    vehicle_id: log.vehicle_id,
    driver_id: log.driver_id || null,
    date: log.date,
    odometer: log.odometer,
    fuel_type: log.fuel_type || 'Pertalite',
    liters: log.liters,
    price_per_liter: log.price_per_liter,
    gas_station: log.gas_station || '',
    receipt_url: log.receipt_url || '',
    notes: log.notes || ''
  })
  isSlideoverOpen.value = true
}

const saveFuelLog = async () => {
  if (!form.vehicle_id) return toast.add({ title: 'Vehicle is required', color: 'red' })
  if (!form.date) return toast.add({ title: 'Date is required', color: 'red' })
  if (!form.odometer) return toast.add({ title: 'Odometer is required', color: 'red' })
  if (!form.liters || !form.price_per_liter) return toast.add({ title: 'Liters and price are required', color: 'red' })
  if (!form.gas_station) return toast.add({ title: 'Gas station is required', color: 'red' })
  if (!form.receipt_url) return toast.add({ title: 'Receipt is required', color: 'red' })
  
  saving.value = true
  try {
    const payload: any = { 
      ...form, 
      total_cost: form.liters! * form.price_per_liter!
    }
    if (!payload.driver_id) delete payload.driver_id
    
    if (editingLog.value) {
      await $api.put(`/fleet/fuel-logs/${editingLog.value.id}`, payload)
      toast.add({ title: 'Fuel log updated!' })
    } else {
      await $api.post('/fleet/fuel-logs', payload)
      toast.add({ title: 'Fuel log added!' })
    }
    isSlideoverOpen.value = false
    fetchFuelLogs()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteFuelLog = async (log: any) => {
  if (!confirm('Delete this fuel log?')) return
  try {
    await $api.delete(`/fleet/fuel-logs/${log.id}`)
    toast.add({ title: 'Fuel log deleted!' })
    fetchFuelLogs()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

// ========== FILE UPLOAD ==========
const triggerFileUpload = () => fileInput.value?.click()

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) await uploadFile(target.files[0])
}

const handleFileDrop = async (event: DragEvent) => {
  const file = event.dataTransfer?.files?.[0]
  if (file) await uploadFile(file)
}

const uploadFile = async (file: File) => {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await $api.post('/upload/media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    form.receipt_url = res.data.url
    toast.add({ title: 'Receipt uploaded!' })
  } catch (e: any) {
    toast.add({ title: 'Upload failed', description: e.response?.data?.detail, color: 'red' })
  } finally {
    uploading.value = false
  }
}

// ========== DRIVER CRUD ==========
const closeDriverModal = () => { showDriverModal.value = false; cancelEditDriver() }
const editDriver = (driver: any) => {
  editingDriver.value = driver
  Object.assign(driverForm, {
    name: driver.name || '', phone: driver.phone || '', card_id_number: driver.card_id_number || '',
    employment_status: driver.employment_status || '', license_number: driver.license_number || '',
    license_type: driver.license_type || ''
  })
}
const cancelEditDriver = () => {
  editingDriver.value = null
  Object.assign(driverForm, { name: '', phone: '', card_id_number: '', employment_status: '', license_number: '', license_type: '' })
}
const saveDriver = async () => {
  if (!driverForm.name || !driverForm.phone || !driverForm.card_id_number || !driverForm.employment_status || !driverForm.license_number || !driverForm.license_type) {
    return toast.add({ title: 'All fields are required', color: 'red' })
  }
  savingDriver.value = true
  try {
    if (editingDriver.value) {
      await $api.put(`/fleet/drivers/${editingDriver.value.id}`, driverForm)
      toast.add({ title: 'Driver updated!' })
    } else {
      await $api.post('/fleet/drivers', driverForm)
      toast.add({ title: 'Driver added!' })
    }
    cancelEditDriver()
    fetchDrivers()
  } catch (e: any) { toast.add({ title: 'Error', description: e.response?.data?.detail, color: 'red' }) }
  finally { savingDriver.value = false }
}
const deleteDriver = async (driver: any) => {
  if (!confirm(`Delete driver "${driver.name}"?`)) return
  try {
    await $api.delete(`/fleet/drivers/${driver.id}`)
    toast.add({ title: 'Driver deleted!' })
    fetchDrivers()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) }
}

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const formatDate = (dt: string) => dt ? new Date(dt).toLocaleDateString('id-ID', { dateStyle: 'medium' }) : '-'

onMounted(() => {
  fetchFuelLogs()
  fetchVehicles()
  fetchDrivers()
})
</script>
