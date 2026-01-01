<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Assets</h2>
        <p class="text-gray-500">Manage equipment and machines for maintenance</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchAssets">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Asset</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ assets.length }}</p>
          <p class="text-sm text-gray-500">Total Assets</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ assets.filter(a => a.status === 'OPERATIONAL').length }}</p>
          <p class="text-sm text-gray-500">Operational</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ assets.filter(a => a.status === 'UNDER_MAINTENANCE').length }}</p>
          <p class="text-sm text-gray-500">Under Maintenance</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ assets.filter(a => a.status === 'BROKEN').length }}</p>
          <p class="text-sm text-gray-500">Broken</p>
        </div>
      </UCard>
    </div>

    <!-- Data Table -->
    <UCard>
      <DataTable :columns="columns" :rows="assets" :loading="loading" searchable :search-keys="['code', 'name', 'category', 'location']" empty-message="No assets yet. Add your first asset to get started.">
        <template #code-data="{ row }">
          <div>
            <p class="font-medium font-mono">{{ row.code }}</p>
            <p class="text-xs text-gray-400">{{ row.category }}</p>
          </div>
        </template>
        <template #name-data="{ row }">
          <p class="font-medium">{{ row.name }}</p>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ formatStatus(row.status) }}</UBadge>
        </template>
        <template #location-data="{ row }">
          <span class="text-sm">{{ row.location || '-' }}</span>
        </template>
        <template #work_order_count-data="{ row }">
          <div class="text-center">
            <span class="font-medium">{{ row.work_order_count }}</span>
            <span v-if="row.pending_work_orders > 0" class="text-xs text-orange-600 ml-1">({{ row.pending_work_orders }} pending)</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteAsset(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingAsset ? 'Edit Asset' : 'Add Asset'" :loading="saving" :disabled="!isFormValid" @submit="saveAsset">
      <UFormGroup label="Asset Code" required hint="Unique identifier e.g. EQP-001">
        <UInput v-model="form.code" placeholder="EQP-001" />
      </UFormGroup>
      <UFormGroup label="Name" required hint="Asset/equipment name">
        <UInput v-model="form.name" placeholder="CNC Machine #1" />
      </UFormGroup>
      <UFormGroup label="Category" required hint="Equipment type">
        <USelect v-model="form.category" :options="categoryOptions" placeholder="Select category..." />
      </UFormGroup>
      
      <UDivider label="Location" />
      
      <UFormGroup label="Warehouse" required hint="Select warehouse location">
        <USelect 
          v-model="selectedWarehouse" 
          :options="warehouseOptions" 
          placeholder="Select warehouse..."
          @change="onWarehouseChange"
        />
      </UFormGroup>
      <UFormGroup v-if="floorOptions.length > 0" label="Floor" hint="Optional - select floor">
        <USelect 
          v-model="selectedFloor" 
          :options="floorOptions" 
          placeholder="Select floor..."
          @change="onFloorChange"
        />
      </UFormGroup>
      <UFormGroup v-if="roomOptions.length > 0" label="Room" hint="Optional - select room">
        <USelect 
          v-model="selectedRoom" 
          :options="roomOptions" 
          placeholder="Select room..."
        />
      </UFormGroup>
      <UFormGroup v-if="zoneOptions.length > 0" label="Storage Zone" hint="Optional - select storage zone">
        <USelect 
          v-model="selectedZone" 
          :options="zoneOptions" 
          placeholder="Select zone..."
        />
      </UFormGroup>
      
      <UFormGroup label="Status" required hint="Current operational status">
        <USelect v-model="form.status" :options="statusOptions" />
      </UFormGroup>
      
      <UDivider label="Equipment Details" />
      
      <UFormGroup label="Manufacturer" required hint="Equipment manufacturer">
        <UInput v-model="form.manufacturer" placeholder="Fanuc" />
      </UFormGroup>
      <UFormGroup label="Model" required hint="Model number/name">
        <UInput v-model="form.model" placeholder="Robodrill α-D21MiB5" />
      </UFormGroup>
      <UFormGroup label="Serial Number" required hint="Unique serial number">
        <UInput v-model="form.serial_number" placeholder="SN12345678" />
      </UFormGroup>
      
      <UDivider label="Purchase & Warranty" />
      
      <UFormGroup label="Purchase Date" hint="When asset was acquired">
        <UInput v-model="form.purchase_date" type="date" />
      </UFormGroup>
      <UFormGroup label="Purchase Cost" hint="Acquisition cost">
        <UInput v-model.number="form.purchase_cost" type="number" placeholder="0" />
      </UFormGroup>
      <UFormGroup label="Warranty Expiry" required hint="Warranty end date">
        <UInput v-model="form.warranty_expiry" type="date" />
      </UFormGroup>
      <UFormGroup label="Notes" hint="Additional notes">
        <UTextarea v-model="form.notes" :rows="3" />
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
const editingAsset = ref<any>(null)
const assets = ref<any[]>([])

// Location hierarchy data
const locationHierarchy = ref<any[]>([])
const selectedWarehouse = ref('')
const selectedFloor = ref('')
const selectedRoom = ref('')
const selectedZone = ref('')

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'status', label: 'Status' },
  { key: 'location', label: 'Location' },
  { key: 'work_order_count', label: 'Work Orders' },
  { key: 'actions', label: '' }
]

const categoryOptions = ['Equipment', 'Vehicle', 'Building', 'Machinery', 'Electrical', 'HVAC', 'Plumbing', 'Other']
const statusOptions = [
  { label: 'Operational', value: 'OPERATIONAL' },
  { label: 'Under Maintenance', value: 'UNDER_MAINTENANCE' },
  { label: 'Broken', value: 'BROKEN' },
  { label: 'Retired', value: 'RETIRED' }
]

// Location computed options
const warehouseOptions = computed(() => 
  locationHierarchy.value.map(wh => ({ label: wh.name, value: wh.id }))
)

const floorOptions = computed(() => {
  const wh = locationHierarchy.value.find(w => w.id === selectedWarehouse.value)
  if (!wh?.floors?.length) return []
  return wh.floors.map((f: any) => ({ label: `${f.name} (Floor ${f.floor_number})`, value: f.id }))
})

const roomOptions = computed(() => {
  const wh = locationHierarchy.value.find(w => w.id === selectedWarehouse.value)
  if (!wh) return []
  const floor = wh.floors?.find((f: any) => f.id === selectedFloor.value)
  if (!floor?.rooms?.length) return []
  return floor.rooms.map((r: any) => ({ label: `${r.name} (${r.code})`, value: r.id }))
})

const zoneOptions = computed(() => {
  const wh = locationHierarchy.value.find(w => w.id === selectedWarehouse.value)
  if (!wh?.zones?.length) return []
  return wh.zones.map((z: any) => ({ label: `${z.name} (${z.type || 'General'})`, value: z.id }))
})

// Form validation
const isFormValid = computed(() => {
  return form.code.trim() !== '' &&
         form.name.trim() !== '' &&
         form.category !== '' &&
         selectedWarehouse.value !== '' &&
         form.status !== '' &&
         form.manufacturer.trim() !== '' &&
         form.model.trim() !== '' &&
         form.serial_number.trim() !== '' &&
         form.warranty_expiry !== ''
})

// Build location string from selections
const buildLocationString = () => {
  const parts: string[] = []
  const wh = locationHierarchy.value.find(w => w.id === selectedWarehouse.value)
  if (wh) {
    parts.push(wh.name)
    const floor = wh.floors?.find((f: any) => f.id === selectedFloor.value)
    if (floor) {
      parts.push(floor.name)
      const room = floor.rooms?.find((r: any) => r.id === selectedRoom.value)
      if (room) parts.push(room.name)
    }
    const zone = wh.zones?.find((z: any) => z.id === selectedZone.value)
    if (zone) parts.push(`[${zone.name}]`)
  }
  return parts.join(' / ')
}

const onWarehouseChange = () => {
  selectedFloor.value = ''
  selectedRoom.value = ''
  selectedZone.value = ''
}

const onFloorChange = () => {
  selectedRoom.value = ''
}

const form = reactive({
  code: '', name: '', category: '', location: '', status: 'OPERATIONAL',
  manufacturer: '', model: '', serial_number: '',
  purchase_date: '', purchase_cost: 0, warranty_expiry: '', notes: ''
})

const fetchAssets = async () => {
  loading.value = true
  try {
    const res = await $api.get('/maintenance/assets')
    assets.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchLocationHierarchy = async () => {
  try {
    const res = await $api.get('/inventory/locations-hierarchy')
    locationHierarchy.value = res.data
  } catch (e) {
    console.error('Failed to fetch locations:', e)
  }
}

const resetLocationSelections = () => {
  selectedWarehouse.value = ''
  selectedFloor.value = ''
  selectedRoom.value = ''
  selectedZone.value = ''
}

const openCreate = () => {
  editingAsset.value = null
  Object.assign(form, { code: '', name: '', category: '', location: '', status: 'OPERATIONAL', manufacturer: '', model: '', serial_number: '', purchase_date: '', purchase_cost: 0, warranty_expiry: '', notes: '' })
  resetLocationSelections()
  isSlideoverOpen.value = true
}

const openEdit = (asset: any) => {
  editingAsset.value = asset
  Object.assign(form, {
    code: asset.code, name: asset.name, category: asset.category || '', location: asset.location || '', status: asset.status,
    manufacturer: asset.manufacturer || '', model: asset.model || '', serial_number: asset.serial_number || '',
    purchase_date: asset.purchase_date?.split('T')[0] || '', purchase_cost: asset.purchase_cost || 0, warranty_expiry: asset.warranty_expiry?.split('T')[0] || '', notes: asset.notes || ''
  })
  // Try to parse location back to selections (best effort)
  resetLocationSelections()
  if (asset.location) {
    const wh = locationHierarchy.value.find(w => asset.location.startsWith(w.name))
    if (wh) selectedWarehouse.value = wh.id
  }
  isSlideoverOpen.value = true
}

const saveAsset = async () => {
  saving.value = true
  try {
    // Build location string from selections
    form.location = buildLocationString()
    
    const payload = { ...form }
    if (!payload.purchase_date) delete payload.purchase_date
    if (!payload.warranty_expiry) delete payload.warranty_expiry
    
    if (editingAsset.value) {
      await $api.put(`/maintenance/assets/${editingAsset.value.id}`, payload)
      toast.add({ title: 'Asset updated!' })
    } else {
      await $api.post('/maintenance/assets', payload)
      toast.add({ title: 'Asset created!' })
    }
    isSlideoverOpen.value = false
    fetchAssets()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteAsset = async (asset: any) => {
  if (!confirm(`Delete asset "${asset.name}"?`)) return
  try {
    await $api.delete(`/maintenance/assets/${asset.id}`)
    toast.add({ title: 'Asset deleted!' })
    fetchAssets()
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    OPERATIONAL: 'green', UNDER_MAINTENANCE: 'orange', BROKEN: 'red', RETIRED: 'gray'
  }
  return colors[status] || 'gray'
}

const formatStatus = (status: string) => {
  const labels: Record<string, string> = {
    OPERATIONAL: 'Operational', UNDER_MAINTENANCE: 'Under Maintenance', BROKEN: 'Broken', RETIRED: 'Retired'
  }
  return labels[status] || status
}

onMounted(() => {
  fetchAssets()
  fetchLocationHierarchy()
})
</script>

