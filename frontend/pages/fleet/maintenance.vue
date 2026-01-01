<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Vehicle Maintenance</h2>
        <p class="text-gray-500">Track service and repair history</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchLogs">Refresh</UButton>
        <UButton icon="i-heroicons-building-storefront" variant="outline" @click="showVendorModal = true">Vendors</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Maintenance</UButton>
      </div>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="logs" :loading="loading" searchable :search-keys="['description', 'service_type']" empty-message="No maintenance records yet.">
        <template #vehicle_id-data="{ row }">
          <p class="font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #date-data="{ row }">
          <div>
            <p>{{ formatDate(row.date) }}</p>
            <p class="text-xs text-gray-400">{{ row.odometer?.toLocaleString() }} km</p>
          </div>
        </template>
        <template #service_type-data="{ row }">
          <div>
            <UBadge :color="getServiceColor(row.service_type)" variant="subtle" size="sm">{{ row.service_type }}</UBadge>
            <p class="text-xs text-gray-400 mt-1 truncate max-w-48">{{ row.description }}</p>
          </div>
        </template>
        <template #vendor_id-data="{ row }">
          <p class="text-sm">{{ getVendorName(row.vendor_id) }}</p>
        </template>
        <template #total_cost-data="{ row }">
          <p class="font-medium">Rp{{ formatNumber(row.total_cost) }}</p>
        </template>
        <template #next_service_date-data="{ row }">
          <UBadge v-if="row.next_service_date" :color="isOverdue(row.next_service_date) ? 'red' : 'gray'" size="sm">
            {{ formatDate(row.next_service_date) }}
          </UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingLog ? 'Edit Maintenance' : 'Add Maintenance'" :loading="saving" @submit="saveLog" size="lg">
      <UFormGroup label="Vehicle" required hint="Select the vehicle being serviced">
        <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." />
      </UFormGroup>

      <UFormGroup label="Vendor/Workshop" required hint="Service provider performing the maintenance">
        <USelect v-model="form.vendor_id" :options="vendorOptions" placeholder="Select vendor..." />
      </UFormGroup>

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Date" required hint="Date of service">
          <UInput v-model="form.date" type="date" />
        </UFormGroup>
        <UFormGroup label="Odometer (km)" required hint="Current odometer reading">
          <UInput v-model.number="form.odometer" type="number" placeholder="e.g. 45000" />
        </UFormGroup>
      </div>

      <UFormGroup label="Service Type" required hint="Type of maintenance performed">
        <USelect v-model="form.service_type" :options="serviceTypeOptions" />
      </UFormGroup>

      <UFormGroup label="Description" required hint="Detailed description of work performed">
        <UTextarea v-model="form.description" :rows="3" placeholder="Describe the service, parts replaced, issues found..." />
      </UFormGroup>

      <UDivider label="Location" />

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Latitude" hint="GPS latitude of service location">
          <UInput v-model.number="form.lat" type="number" step="any" placeholder="-6.2088" />
        </UFormGroup>
        <UFormGroup label="Longitude" hint="GPS longitude of service location">
          <UInput v-model.number="form.lng" type="number" step="any" placeholder="106.8456" />
        </UFormGroup>
      </div>

      <UDivider label="Costs" />

      <div class="grid grid-cols-3 gap-4">
        <UFormGroup label="Parts Cost (Rp)" required hint="Cost of replacement parts">
          <UInput v-model.number="form.parts_cost" type="number" placeholder="0" />
        </UFormGroup>
        <UFormGroup label="Labor Cost (Rp)" required hint="Service labor charges">
          <UInput v-model.number="form.labor_cost" type="number" placeholder="0" />
        </UFormGroup>
        <UFormGroup label="Total Cost (Rp)" hint="Auto-calculated">
          <UInput :model-value="(form.parts_cost || 0) + (form.labor_cost || 0)" type="number" disabled />
        </UFormGroup>
      </div>

      <UDivider label="Next Service" />

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Next Service Date" required hint="Recommended next service date">
          <UInput v-model="form.next_service_date" type="date" />
        </UFormGroup>
        <UFormGroup label="Next Service Odometer" hint="Recommended next service at km">
          <UInput v-model.number="form.next_service_odometer" type="number" placeholder="e.g. 50000" />
        </UFormGroup>
      </div>

      <UFormGroup label="Performed By" hint="Mechanic or technician name">
        <UInput v-model="form.performed_by" placeholder="Mechanic name" />
      </UFormGroup>

      <UFormGroup label="Invoice Number" hint="Invoice or work order number">
        <UInput v-model="form.invoice_number" placeholder="INV-123456" />
      </UFormGroup>

      <UFormGroup label="Receipt URL" hint="Link to receipt/invoice image">
        <UInput v-model="form.receipt_url" placeholder="URL to receipt" />
      </UFormGroup>

      <UFormGroup label="Notes" hint="Additional notes">
        <UTextarea v-model="form.notes" :rows="2" />
      </UFormGroup>
    </FormSlideover>

    <!-- Vendor Management Modal -->
    <UModal v-model="showVendorModal" :ui="{ width: 'sm:max-w-2xl' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Vendor Management</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showVendorModal = false" />
          </div>
        </template>
        <div class="space-y-4">
          <div class="grid grid-cols-5 gap-2">
            <UInput v-model="newVendor.name" placeholder="Vendor Name *" class="col-span-2" />
            <UInput v-model="newVendor.phone" placeholder="Phone" />
            <UInput v-model="newVendor.city" placeholder="City" />
            <UButton icon="i-heroicons-plus" @click="addVendor" />
          </div>
          <div class="divide-y max-h-64 overflow-y-auto">
            <div v-for="vendor in vendors" :key="vendor.id" class="py-2 flex items-center justify-between">
              <div>
                <p class="font-medium">{{ vendor.code }} - {{ vendor.name }}</p>
                <p class="text-xs text-gray-400">{{ vendor.city || 'No city' }} | {{ vendor.phone || 'No phone' }}</p>
              </div>
              <UButton icon="i-heroicons-trash" size="xs" variant="ghost" color="red" @click="deleteVendor(vendor)" />
            </div>
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
const isSlideoverOpen = ref(false)
const editingLog = ref<any>(null)
const logs = ref<any[]>([])
const vehicles = ref<any[]>([])
const vendors = ref<any[]>([])
const showVendorModal = ref(false)
const newVendor = reactive({ name: '', phone: '', city: '' })

const columns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'date', label: 'Date / Odometer' },
  { key: 'service_type', label: 'Service' },
  { key: 'vendor_id', label: 'Vendor' },
  { key: 'total_cost', label: 'Cost' },
  { key: 'next_service_date', label: 'Next Service' },
  { key: 'actions', label: '' }
]

const serviceTypeOptions = [
  { label: 'Routine Service', value: 'Routine' },
  { label: 'Oil Change', value: 'Oil Change' },
  { label: 'Tire Change', value: 'Tire' },
  { label: 'Brake Service', value: 'Brake' },
  { label: 'Engine Repair', value: 'Engine' },
  { label: 'Body Repair', value: 'Body' },
  { label: 'Electrical', value: 'Electrical' },
  { label: 'AC Service', value: 'AC' },
  { label: 'Inspection', value: 'Inspection' },
  { label: 'Other', value: 'Other' }
]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const vendorOptions = computed(() => 
  vendors.value.map((v: any) => ({ label: `${v.code} - ${v.name}`, value: v.id }))
)

const form = reactive({
  vehicle_id: '',
  vendor_id: '',
  date: '',
  odometer: 0,
  service_type: 'Routine',
  description: '',
  lat: null as number | null,
  lng: null as number | null,
  parts_cost: 0,
  labor_cost: 0,
  next_service_date: '',
  next_service_odometer: null as number | null,
  performed_by: '',
  invoice_number: '',
  receipt_url: '',
  notes: ''
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await $api.get('/fleet/maintenance')
    logs.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchVehicles = async () => {
  try {
    const res = await $api.get('/fleet/vehicles')
    vehicles.value = res.data
  } catch (e) { console.error(e) }
}

const fetchVendors = async () => {
  try {
    const res = await $api.get('/fleet/vendors')
    vendors.value = res.data
  } catch (e) { console.error(e) }
}

const getVehicleName = (id: string) => {
  const v = vehicles.value.find((v: any) => v.id === id)
  return v ? v.plate_number : '-'
}

const getVendorName = (id: string) => {
  if (!id) return '-'
  const v = vendors.value.find((v: any) => v.id === id)
  return v ? v.name : '-'
}

const openCreate = () => {
  editingLog.value = null
  const today = new Date().toISOString().slice(0, 10)
  const nextMonth = new Date(Date.now() + 30*24*60*60*1000).toISOString().slice(0, 10)
  Object.assign(form, {
    vehicle_id: '', vendor_id: '', date: today, odometer: 0,
    service_type: 'Routine', description: '', lat: null, lng: null,
    parts_cost: 0, labor_cost: 0, next_service_date: nextMonth,
    next_service_odometer: null, performed_by: '', invoice_number: '',
    receipt_url: '', notes: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (log: any) => {
  editingLog.value = log
  Object.assign(form, {
    vehicle_id: log.vehicle_id,
    vendor_id: log.vendor_id,
    date: log.date,
    odometer: log.odometer,
    service_type: log.service_type,
    description: log.description,
    lat: log.lat,
    lng: log.lng,
    parts_cost: log.parts_cost,
    labor_cost: log.labor_cost,
    next_service_date: log.next_service_date,
    next_service_odometer: log.next_service_odometer,
    performed_by: log.performed_by || '',
    invoice_number: log.invoice_number || '',
    receipt_url: log.receipt_url || '',
    notes: log.notes || ''
  })
  isSlideoverOpen.value = true
}

const saveLog = async () => {
  if (!form.vehicle_id || !form.vendor_id || !form.odometer || !form.description || !form.next_service_date) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const payload = { ...form }
    if (editingLog.value) {
      await $api.put(`/fleet/maintenance/${editingLog.value.id}`, payload)
      toast.add({ title: 'Maintenance record updated!' })
    } else {
      await $api.post('/fleet/maintenance', payload)
      toast.add({ title: 'Maintenance record added!' })
    }
    isSlideoverOpen.value = false
    fetchLogs()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const addVendor = async () => {
  if (!newVendor.name) {
    toast.add({ title: 'Vendor name is required', color: 'red' })
    return
  }
  try {
    await $api.post('/fleet/vendors', newVendor)
    toast.add({ title: 'Vendor added!' })
    newVendor.name = ''
    newVendor.phone = ''
    newVendor.city = ''
    fetchVendors()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const deleteVendor = async (vendor: any) => {
  if (!confirm(`Delete vendor "${vendor.name}"?`)) return
  try {
    await $api.delete(`/fleet/vendors/${vendor.id}`)
    toast.add({ title: 'Vendor deleted!' })
    fetchVendors()
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const getServiceColor = (type: string) => {
  const colors: Record<string, string> = {
    Routine: 'blue', 'Oil Change': 'yellow', Tire: 'gray', Brake: 'red',
    Engine: 'orange', Body: 'purple', Electrical: 'cyan', AC: 'teal'
  }
  return colors[type] || 'gray'
}

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'
const formatNumber = (n: number) => n?.toLocaleString('id-ID') || '0'
const isOverdue = (d: string) => new Date(d) < new Date()

onMounted(() => {
  fetchLogs()
  fetchVehicles()
  fetchVendors()
})
</script>
