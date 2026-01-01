<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Warehouses</h2>
        <p class="text-gray-500">Manage warehouse locations with floors and rooms</p>
      </div>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">Add Warehouse</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable :columns="columns" :rows="warehouses" :loading="loading" search-placeholder="Search warehouses...">
         <template #name-data="{ row }">
           <div>
             <p class="font-medium">{{ row.name }}</p>
             <p class="text-xs text-gray-400">{{ row.code }}</p>
           </div>
         </template>
         <template #total_floors-data="{ row }">
           <UBadge color="blue" variant="subtle">{{ row.total_floors || 1 }} floor(s)</UBadge>
         </template>
         <template #rooms_count-data="{ row }">
           <span class="text-sm">{{ countRooms(row) }} rooms</span>
         </template>
         <template #actions-data="{ row }">
            <div class="flex gap-1">
              <UButton icon="i-heroicons-building-office-2" color="blue" variant="ghost" size="xs" @click="openFloorManager(row)" title="Manage Floors & Rooms" />
              <UButton icon="i-heroicons-map-pin" color="gray" variant="ghost" size="xs" @click="viewLocations(row)" />
              <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="editWarehouse(row)" />
            </div>
         </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Warehouse Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Warehouse' : 'Add Warehouse'"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="saveWarehouse"
    >
      <div class="space-y-4">
        <UFormGroup label="Warehouse Code" name="code" required hint="Unique code e.g. WH-001, GDG-BEKASI-01" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.code" placeholder="WH-001" />
        </UFormGroup>
        <UFormGroup label="Warehouse Name" name="name" required hint="Descriptive name e.g. Central Warehouse Jakarta" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g. Central Warehouse" />
        </UFormGroup>
        
        <UDivider label="Location" />
        
        <UFormGroup label="Address" name="address" required hint="Full address including street, city, postal code" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.address" placeholder="Jl. Industri Raya No. 123, Bekasi 17520" rows="2" />
        </UFormGroup>
        
        <!-- Map Location Section -->
        <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h4 class="text-sm font-medium text-gray-700 mb-3">Map Location</h4>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Latitude" hint="e.g. -6.123456" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.latitude" type="number" step="0.000001" placeholder="-6.123456" />
            </UFormGroup>
            <UFormGroup label="Longitude" hint="e.g. 106.123456" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.longitude" type="number" step="0.000001" placeholder="106.123456" />
            </UFormGroup>
          </div>
          <UButton size="xs" variant="soft" icon="i-heroicons-magnifying-glass" class="mt-2" @click="searchAddress">Search from Address</UButton>
        </div>
        
        <UDivider label="Building Structure" />
        
        <UFormGroup label="Total Floors" hint="Number of floors including basement" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.total_floors" type="number" min="1" placeholder="1" />
        </UFormGroup>
        
        <!-- Quick Floor Setup -->
        <div v-if="!editMode && form.total_floors > 0" class="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h4 class="text-sm font-medium text-gray-700 mb-3">Quick Floor Setup</h4>
          <div class="space-y-2">
            <div v-for="i in Math.min(form.total_floors, 5)" :key="i" class="grid grid-cols-12 gap-2 items-center">
              <span class="col-span-2 text-xs text-gray-500">Floor {{ i }}</span>
              <UInput 
                v-model="floorsSetup[i-1].name" 
                :placeholder="`e.g. Ground Floor`" 
                size="sm"
                class="col-span-6"
              />
              <UInput 
                v-model.number="floorsSetup[i-1].area_sqm" 
                type="number" 
                placeholder="Area (m²)" 
                size="sm"
                class="col-span-4"
              />
            </div>
          </div>
          <p v-if="form.total_floors > 5" class="text-xs text-gray-400 mt-2">
            More floors can be added after creating the warehouse.
          </p>
        </div>
      </div>
    </FormSlideover>

    <!-- Floor & Room Manager Slideover -->
    <USlideover v-model="isFloorManagerOpen">
      <div class="space-y-4">
        <div class="flex flex-col h-full">
          <div class="flex items-center justify-between px-6 py-4 border-b">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedWarehouse?.name }}</h3>
              <p class="text-sm text-gray-500">Manage floors and rooms</p>
            </div>
            <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="isFloorManagerOpen = false" />
          </div>
          
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <!-- Add Floor Button -->
            <div class="flex justify-between items-center">
              <h4 class="font-medium">Floors</h4>
              <UButton size="sm" icon="i-heroicons-plus" @click="openAddFloor">Add Floor</UButton>
            </div>
            
            <!-- Floors List -->
            <div v-for="floor in selectedWarehouse?.floors || []" :key="floor.id" class="border rounded-lg">
              <div class="flex items-center justify-between p-3 bg-gray-50 border-b">
                <div>
                  <p class="font-medium">{{ floor.floor_name }}</p>
                  <p class="text-xs text-gray-500">Floor {{ floor.floor_number }} • {{ floor.area_sqm || 0 }} m² (Used: {{ getFloorUsedArea(floor) }} m²)</p>
                </div>
                <div class="flex gap-1">
                  <UButton size="xs" icon="i-heroicons-plus" variant="ghost" @click="openAddRoom(floor)">Add Room</UButton>
                  <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEditFloor(floor)" />
                  <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteFloor(floor)" />
                </div>
              </div>
              
              <!-- Rooms in Floor -->
              <div class="p-3 space-y-2">
                <div v-if="floor.rooms?.length === 0" class="text-sm text-gray-400 text-center py-2">
                  No rooms yet
                </div>
                <div v-for="room in floor.rooms" :key="room.id" class="flex items-center justify-between p-2 bg-white border rounded">
                  <div class="flex items-center gap-3">
                    <div class="p-2 bg-gray-100 rounded">
                      <UIcon name="i-heroicons-cube" class="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p class="font-medium text-sm">{{ room.room_name }}</p>
                      <p class="text-xs text-gray-500">{{ room.room_code }} • Capacity: {{ room.capacity }}</p>
                    </div>
                  </div>
                  <div class="flex gap-1">
                    <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEditRoom(room, floor)" />
                    <UButton size="xs" icon="i-heroicons-qr-code" variant="ghost" @click="showRoomQR(room)" title="Show QR" />
                    <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteRoom(room)" />
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="!selectedWarehouse?.floors?.length" class="text-center py-8 text-gray-400">
              No floors added yet. Click "Add Floor" to start.
            </div>
          </div>
        </div>
      </div>
    </USlideover>

    <!-- Add/Edit Floor Modal -->
    <UModal v-model="showAddFloorModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">{{ editingFloor ? 'Edit Floor' : 'Add Floor' }}</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Floor Number" required>
            <UInput v-model.number="floorForm.floor_number" type="number" min="1" placeholder="1" />
          </UFormGroup>
          <UFormGroup label="Floor Name" required>
            <UInput v-model="floorForm.floor_name" placeholder="e.g. Ground Floor, Lantai 1" />
          </UFormGroup>
          <UFormGroup label="Area (m²)" :hint="editingFloor ? `Min area: ${getFloorUsedArea(editingFloor)} m² (used by rooms)` : ''">
            <UInput v-model.number="floorForm.area_sqm" type="number" placeholder="0" :min="editingFloor ? getFloorUsedArea(editingFloor) : 0" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showAddFloorModal = false; editingFloor = null">Cancel</UButton>
            <UButton @click="saveFloor" :loading="submitting">{{ editingFloor ? 'Save Changes' : 'Add Floor' }}</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Add/Edit Room Modal -->
    <UModal v-model="showAddRoomModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">{{ editingRoom ? 'Edit Room' : 'Add Room to ' + selectedFloor?.floor_name }}</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Room Code" required hint="Unique code e.g. R001">
            <UInput v-model="roomForm.room_code" placeholder="R001" />
          </UFormGroup>
          <UFormGroup label="Room Name" required>
            <UInput v-model="roomForm.room_name" placeholder="e.g. Storage Room A" />
          </UFormGroup>
          <UFormGroup label="Capacity" hint="Number of units/pallets">
            <UInput v-model.number="roomForm.capacity" type="number" placeholder="0" />
          </UFormGroup>
          <UFormGroup label="Area (m²)" :hint="`Available: ${getAvailableFloorArea()} m²`">
            <UInput v-model.number="roomForm.area_sqm" type="number" placeholder="0" :max="getAvailableFloorArea() + (editingRoom?.area_sqm || 0)" />
          </UFormGroup>
          <p v-if="roomForm.area_sqm > getAvailableFloorArea() + (editingRoom?.area_sqm || 0)" class="text-red-500 text-xs">
            Room area exceeds available floor space!
          </p>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showAddRoomModal = false; editingRoom = null">Cancel</UButton>
            <UButton @click="saveRoom" :loading="submitting" :disabled="roomForm.area_sqm > getAvailableFloorArea() + (editingRoom?.area_sqm || 0)">{{ editingRoom ? 'Save Changes' : 'Add Room' }}</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Room QR Modal -->
    <UModal v-model="showQRModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Room QR Code</h3>
        </template>
        <div class="text-center space-y-4">
          <div class="p-4 bg-white border-2 border-dashed rounded-lg inline-block">
            <QRCode v-if="selectedRoom" :value="selectedRoom.qr_code || selectedRoom.id" :size="180" />
          </div>
          <div>
            <p class="font-medium">{{ selectedRoom?.room_name }}</p>
            <p class="text-sm text-gray-500">{{ selectedRoom?.room_code }}</p>
            <p class="text-xs text-gray-400 mt-1">Barcode: {{ selectedRoom?.barcode }}</p>
          </div>
        </div>
        <template #footer>
          <div class="flex justify-center">
            <UButton variant="ghost" @click="showQRModal = false">Close</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- View Locations Slideover (Legacy) -->
    <USlideover v-model="isLocationsOpen">
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <h3 class="text-lg font-semibold">Locations in {{ selectedWarehouse?.name }}</h3>
          <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="isLocationsOpen = false" />
        </div>
        
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <UButton size="sm" icon="i-heroicons-plus" @click="openCreateLocation">Add Location</UButton>
          
          <div class="space-y-2">
            <div v-for="loc in locations" :key="loc.id" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <div>
                <p class="font-medium">{{ loc.name }}</p>
                <p class="text-sm text-gray-500">{{ loc.code }}</p>
              </div>
              <UBadge color="gray" variant="subtle">{{ loc.type }}</UBadge>
            </div>
            <div v-if="locations.length === 0" class="text-sm text-gray-400 text-center py-8">
              No locations found.
            </div>
          </div>
          
          <!-- Nested Create Location Form -->
          <div v-if="isCreatingLocation" class="p-4 border rounded-lg bg-white">
            <h4 class="text-sm font-medium mb-3">New Location</h4>
            <form @submit.prevent="createLocation" class="space-y-3">
              <UFormGroup label="Name" required>
                <UInput v-model="locForm.name" placeholder="Location Name" size="sm" />
              </UFormGroup>
              <UFormGroup label="Code" required>
                <UInput v-model="locForm.code" placeholder="e.g. A-01" size="sm" />
              </UFormGroup>
              <UFormGroup label="Type">
                <USelect v-model="locForm.type" :options="['Receiving', 'Storage', 'Picking', 'Production', 'Quarantine']" size="sm" />
              </UFormGroup>
              <div class="flex justify-end gap-2">
                <UButton size="sm" color="gray" variant="ghost" @click="isCreatingLocation = false">Cancel</UButton>
                <UButton size="sm" type="submit" :loading="locSubmitting">Add Location</UButton>
              </div>
            </form>
          </div>
        </div>
      </div>
    </USlideover>
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
const isLocationsOpen = ref(false)
const isFloorManagerOpen = ref(false)
const isCreatingLocation = ref(false)
const loading = ref(false)
const submitting = ref(false)
const locSubmitting = ref(false)
const editMode = ref(false)
const mapLoaded = ref(false)
const mapContainer = ref<HTMLElement | null>(null)
let map: any = null

// Modals
const showAddFloorModal = ref(false)
const showAddRoomModal = ref(false)
const showQRModal = ref(false)

const warehouses = ref<any[]>([])
const locations = ref<any[]>([])
const selectedWarehouse = ref<any>(null)
const selectedFloor = ref<any>(null)
const selectedRoom = ref<any>(null)
const editingFloor = ref<any>(null)
const editingRoom = ref<any>(null)

const columns = [
  { key: 'name', label: 'Warehouse' },
  { key: 'address', label: 'Address' },
  { key: 'total_floors', label: 'Floors' },
  { key: 'rooms_count', label: 'Rooms' },
  { key: 'actions', label: '' }
]

const form = reactive({ 
  id: '', 
  code: '',
  name: '', 
  address: '',
  latitude: null as number | null,
  longitude: null as number | null,
  total_floors: 1
})

const floorsSetup = reactive<Array<{name: string, area_sqm: number}>>([
  { name: 'Lantai 1', area_sqm: 0 },
  { name: 'Lantai 2', area_sqm: 0 },
  { name: 'Lantai 3', area_sqm: 0 },
  { name: 'Lantai 4', area_sqm: 0 },
  { name: 'Lantai 5', area_sqm: 0 }
])

const floorForm = reactive({
  floor_number: 1,
  floor_name: '',
  area_sqm: 0
})

const roomForm = reactive({
  room_code: '',
  room_name: '',
  capacity: 0,
  area_sqm: 0
})

const locForm = reactive({ name: '', code: '', type: 'Storage' })

const isFormValid = computed(() => {
  return form.code.trim() !== '' && form.name.trim() !== ''
})

const countRooms = (warehouse: any) => {
  let count = 0
  warehouse.floors?.forEach((f: any) => {
    count += f.rooms?.length || 0
  })
  return count
}

const getFloorUsedArea = (floor: any) => {
  if (!floor?.rooms) return 0
  return floor.rooms.reduce((sum: number, r: any) => sum + (r.area_sqm || 0), 0)
}

const getAvailableFloorArea = () => {
  if (!selectedFloor.value) return 0
  const floor = selectedFloor.value
  const usedArea = getFloorUsedArea(floor)
  // When editing, exclude current room's area from used calculation
  const currentRoomArea = editingRoom.value?.area_sqm || 0
  return Math.max(0, (floor.area_sqm || 0) - usedArea + currentRoomArea)
}

const fetchWarehouses = async () => {
  loading.value = true
  try {
    const res: any = await $fetch('/api/inventory/warehouses', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    warehouses.value = res
  } catch (e) { console.error(e) } 
  finally { loading.value = false }
}

const openCreateModal = () => {
  Object.assign(form, { id: '', code: '', name: '', address: '', latitude: null, longitude: null, total_floors: 1 })
  floorsSetup.forEach((f, i) => { f.name = `Lantai ${i+1}`; f.area_sqm = 0 })
  editMode.value = false
  isOpen.value = true
}

const editWarehouse = (row: any) => {
  Object.assign(form, {
    id: row.id,
    code: row.code || '',
    name: row.name,
    address: row.address || '',
    latitude: row.latitude,
    longitude: row.longitude,
    total_floors: row.total_floors || 1
  })
  editMode.value = true
  isOpen.value = true
}

const saveWarehouse = async () => {
  submitting.value = true
  try {
    const payload: any = {
      code: form.code,
      name: form.name,
      address: form.address,
      latitude: form.latitude,
      longitude: form.longitude,
      total_floors: form.total_floors
    }
    
    // Include floors for new warehouse
    if (!editMode.value && form.total_floors > 0) {
      payload.floors = []
      for (let i = 0; i < Math.min(form.total_floors, 5); i++) {
        payload.floors.push({
          floor_number: i + 1,
          floor_name: floorsSetup[i].name || `Lantai ${i + 1}`,
          area_sqm: floorsSetup[i].area_sqm || 0
        })
      }
    }
    
    if (editMode.value) {
      await $fetch(`/api/inventory/warehouses/${form.id}`, {
        method: 'PUT',
        body: payload,
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      toast.add({ title: 'Warehouse updated!' })
    } else {
      await $fetch('/api/inventory/warehouses', {
        method: 'POST',
        body: payload,
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      toast.add({ title: 'Warehouse created!' })
    }
    isOpen.value = false
    fetchWarehouses()
  } catch (e: any) { 
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  }
  finally { submitting.value = false }
}

// Floor Management
const openFloorManager = (warehouse: any) => {
  selectedWarehouse.value = warehouse
  isFloorManagerOpen.value = true
}

const openAddFloor = () => {
  editingFloor.value = null
  const nextNumber = (selectedWarehouse.value?.floors?.length || 0) + 1
  Object.assign(floorForm, { floor_number: nextNumber, floor_name: `Lantai ${nextNumber}`, area_sqm: 0 })
  showAddFloorModal.value = true
}

const openEditFloor = (floor: any) => {
  editingFloor.value = floor
  Object.assign(floorForm, {
    floor_number: floor.floor_number,
    floor_name: floor.floor_name,
    area_sqm: floor.area_sqm || 0
  })
  showAddFloorModal.value = true
}

const saveFloor = async () => {
  submitting.value = true
  try {
    if (editingFloor.value) {
      // Update existing floor
      await $fetch(`/api/inventory/floors/${editingFloor.value.id}`, {
        method: 'PUT',
        body: floorForm,
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      toast.add({ title: 'Floor updated!' })
    } else {
      // Create new floor
      await $fetch(`/api/inventory/warehouses/${selectedWarehouse.value.id}/floors`, {
        method: 'POST',
        body: floorForm,
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      toast.add({ title: 'Floor added!' })
    }
    showAddFloorModal.value = false
    editingFloor.value = null
    await fetchWarehouses()
    selectedWarehouse.value = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || e.data?.detail || 'Failed', color: 'red' })
  } finally { submitting.value = false }
}

const deleteFloor = async (floor: any) => {
  if (!confirm(`Delete floor "${floor.floor_name}" and all its rooms?`)) return
  try {
    await $fetch(`/api/inventory/floors/${floor.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    toast.add({ title: 'Floor deleted!' })
    await fetchWarehouses()
    selectedWarehouse.value = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

// Room Management
const openAddRoom = (floor: any) => {
  editingRoom.value = null
  selectedFloor.value = floor
  Object.assign(roomForm, { room_code: '', room_name: '', capacity: 0, area_sqm: 0 })
  showAddRoomModal.value = true
}

const openEditRoom = (room: any, floor: any) => {
  editingRoom.value = room
  selectedFloor.value = floor
  Object.assign(roomForm, {
    room_code: room.room_code,
    room_name: room.room_name,
    capacity: room.capacity || 0,
    area_sqm: room.area_sqm || 0
  })
  showAddRoomModal.value = true
}

const saveRoom = async () => {
  submitting.value = true
  try {
    if (editingRoom.value) {
      // Update existing room
      await $fetch(`/api/inventory/rooms/${editingRoom.value.id}`, {
        method: 'PUT',
        body: roomForm,
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      toast.add({ title: 'Room updated!' })
    } else {
      // Create new room
      await $fetch(`/api/inventory/floors/${selectedFloor.value.id}/rooms`, {
        method: 'POST',
        body: roomForm,
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      toast.add({ title: 'Room added!' })
    }
    showAddRoomModal.value = false
    editingRoom.value = null
    await fetchWarehouses()
    selectedWarehouse.value = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || e.data?.detail || 'Failed', color: 'red' })
  } finally { submitting.value = false }
}

const deleteRoom = async (room: any) => {
  if (!confirm(`Delete room "${room.room_name}"?`)) return
  try {
    await $fetch(`/api/inventory/rooms/${room.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    toast.add({ title: 'Room deleted!' })
    await fetchWarehouses()
    selectedWarehouse.value = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const showRoomQR = (room: any) => {
  selectedRoom.value = room
  showQRModal.value = true
}

// Map functions (placeholder - would need Leaflet integration)
const searchAddress = async () => {
  if (!form.address) return
  try {
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(form.address)}`)
    const data = await response.json()
    if (data.length > 0) {
      form.latitude = parseFloat(data[0].lat)
      form.longitude = parseFloat(data[0].lon)
      toast.add({ title: 'Location found!', description: `${form.latitude.toFixed(4)}, ${form.longitude.toFixed(4)}` })
    } else {
      toast.add({ title: 'Location not found', color: 'yellow' })
    }
  } catch (e) {
    console.error('Geocoding failed:', e)
  }
}

// Legacy location functions
const viewLocations = async (warehouse: any) => {
  selectedWarehouse.value = warehouse
  locations.value = warehouse.locations || []
  isLocationsOpen.value = true
  isCreatingLocation.value = false
}

const openCreateLocation = () => {
  locForm.name = ''
  locForm.code = ''
  locForm.type = 'Storage'
  isCreatingLocation.value = true
}

const createLocation = async () => {
  if (!selectedWarehouse.value) return
  locSubmitting.value = true
  try {
    await $fetch('/api/inventory/locations', {
      method: 'POST',
      body: {
        warehouse_id: selectedWarehouse.value.id,
        ...locForm
      },
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    await fetchWarehouses()
    const updated = warehouses.value.find(w => w.id === selectedWarehouse.value.id)
    if (updated) locations.value = updated.locations || []
    isCreatingLocation.value = false
  } catch (e) { console.error('Failed:', e) }
  finally { locSubmitting.value = false }
}

onMounted(() => {
  fetchWarehouses()
})
</script>
