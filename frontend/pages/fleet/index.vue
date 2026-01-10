<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Fleet Dashboard</h2>
        <p class="text-gray-500 text-small">Overview of fleet operations and live vehicle tracking</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="refreshAll">Refresh</UButton>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ stats.total_vehicles }}</p>
          <p class="text-small text-gray-500">Total Vehicles</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.available_vehicles }}</p>
          <p class="text-small text-gray-500">Available</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ stats.in_use_vehicles }}</p>
          <p class="text-small text-gray-500">In Use</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ stats.maintenance_vehicles }}</p>
          <p class="text-small text-gray-500">Maintenance</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ stats.broken_vehicles }}</p>
          <p class="text-small text-gray-500">Broken</p>
        </div>
      </UCard>
    </div>

    <!-- Second Row Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
            <UIcon name="i-heroicons-calendar" class="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <p class="text-xl font-bold">{{ stats.active_bookings }}</p>
            <p class="text-small text-gray-500">Active Bookings</p>
          </div>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
            <UIcon name="i-heroicons-bell-alert" class="w-6 h-6 text-yellow-600" />
          </div>
          <div>
            <p class="text-xl font-bold">{{ stats.pending_reminders }}</p>
            <p class="text-small text-gray-500">Pending Reminders</p>
          </div>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
            <UIcon name="i-heroicons-banknotes" class="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p class="text-xl font-bold">{{ formatCurrency(stats.total_fuel_cost_month) }}</p>
            <p class="text-small text-gray-500">Fuel This Month</p>
          </div>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <UIcon name="i-heroicons-wrench" class="w-6 h-6 text-gray-600" />
          </div>
          <div>
            <p class="text-xl font-bold">{{ formatCurrency(stats.total_maintenance_cost_month) }}</p>
            <p class="text-small text-gray-500">Maintenance This Month</p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <NuxtLink to="/fleet/vehicles">
        <UCard :ui="{ body: { padding: 'p-4' } }" class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition">
          <div class="flex items-center gap-3">
            <UIcon name="i-heroicons-truck" class="w-8 h-8 text-primary-500" />
            <div>
              <p class="font-medium">Vehicles</p>
              <p class="text-xs text-gray-500">Manage fleet</p>
            </div>
          </div>
        </UCard>
      </NuxtLink>
      <NuxtLink to="/fleet/bookings">
        <UCard :ui="{ body: { padding: 'p-4' } }" class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition">
          <div class="flex items-center gap-3">
            <UIcon name="i-heroicons-calendar-days" class="w-8 h-8 text-blue-500" />
            <div>
              <p class="font-medium">Bookings</p>
              <p class="text-xs text-gray-500">Schedule usage</p>
            </div>
          </div>
        </UCard>
      </NuxtLink>
      <NuxtLink to="/fleet/fuel">
        <UCard :ui="{ body: { padding: 'p-4' } }" class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition">
          <div class="flex items-center gap-3">
            <UIcon name="i-heroicons-fire" class="w-8 h-8 text-orange-500" />
            <div>
              <p class="font-medium">Fuel Logs</p>
              <p class="text-xs text-gray-500">Track consumption</p>
            </div>
          </div>
        </UCard>
      </NuxtLink>
      <NuxtLink to="/fleet/reminders">
        <UCard :ui="{ body: { padding: 'p-4' } }" class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition">
          <div class="flex items-center gap-3">
            <UIcon name="i-heroicons-bell" class="w-8 h-8 text-yellow-500" />
            <div>
              <p class="font-medium">Reminders</p>
              <p class="text-xs text-gray-500">Document alerts</p>
            </div>
          </div>
        </UCard>
      </NuxtLink>
    </div>

    <!-- Vehicles Table + Live Map (Side by Side) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- All Vehicles Table -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-truck" class="w-5 h-5 text-primary-600" />
              <h3 class="font-semibold">All Vehicles</h3>
            </div>
            <NuxtLink to="/fleet/vehicles">
              <UButton size="xs" variant="ghost">View All →</UButton>
            </NuxtLink>
          </div>
        </template>
        <div class="max-h-96 overflow-y-auto">
          <UTable :columns="vehicleColumns" :rows="vehicles" :loading="loadingVehicles">
            <template #plate_number-data="{ row }">
              <p class="font-medium font-mono text-xs">{{ row.plate_number }}</p>
            </template>
            <template #brand-data="{ row }">
              <p class="text-xs">{{ row.brand }} {{ row.model }}</p>
            </template>
            <template #vehicle_type-data="{ row }">
              <p class="text-xs text-gray-500">{{ row.vehicle_type || '-' }}</p>
            </template>
            <template #status-data="{ row }">
              <UBadge :color="getStatusColor(row.status)" variant="subtle" size="xs">{{ formatStatus(row.status) }}</UBadge>
            </template>
            <template #current_odometer-data="{ row }">
              <p class="text-xs">{{ row.current_odometer?.toLocaleString() || 0 }} km</p>
            </template>
          </UTable>
        </div>
      </UCard>

      <!-- Live Tracking Map -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-map" class="w-5 h-5 text-green-600" />
              <h3 class="font-semibold">Live Vehicle Tracking</h3>
              <UBadge v-if="liveLocations.length > 0" color="green" size="xs">{{ liveLocations.length }} Active</UBadge>
              <UBadge v-if="isPolling" color="blue" size="xs" variant="subtle">Live</UBadge>
            </div>
            <div class="flex items-center gap-2">
              <UButton size="xs" variant="soft" color="primary" icon="i-heroicons-plus" @click="seedJourneyData" :loading="seeding">
                Seed 3 Vehicles
              </UButton>
              <UButton size="xs" variant="soft" color="green" icon="i-heroicons-play" @click="simulateAllJourneys" :loading="simulating">
                Simulate
              </UButton>
              <UButton size="xs" variant="ghost" icon="i-heroicons-arrow-path" @click="fetchLiveLocations" />
            </div>
          </div>
        </template>
        <div id="map" class="h-96 rounded-lg bg-gray-100 dark:bg-gray-800"></div>
        <div v-if="liveLocations.length === 0" class="absolute inset-0 flex items-center justify-center bg-gray-100/80 dark:bg-gray-800/80 rounded-lg pointer-events-none" style="position: relative; margin-top: -384px; height: 384px;">
          <div class="text-center">
            <UIcon name="i-heroicons-truck" class="w-12 h-12 text-gray-400 mx-auto" />
            <p class="text-gray-500 mt-2">No vehicles currently in journey</p>
            <p class="text-xs text-gray-400 mt-1">Click "Seed 3 Vehicles" to create sample data</p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Active Journeys List (Below Map) -->
    <UCard v-if="liveLocations.length > 0">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-arrow-trending-up" class="w-5 h-5 text-blue-600" />
          <h3 class="font-semibold">Active Journeys ({{ liveLocations.length }})</h3>
        </div>
      </template>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div 
          v-for="loc in liveLocations" 
          :key="loc.vehicle_id" 
          class="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition"
          @click="focusVehicleOnMap(loc)"
        >
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
              <UIcon name="i-heroicons-truck" class="w-6 h-6 text-primary-600" />
            </div>
            <div class="flex-1">
              <p class="font-mono font-semibold text-sm">{{ loc.vehicle_plate }}</p>
              <p class="text-xs text-gray-500">{{ loc.vehicle_brand }} {{ loc.vehicle_model }}</p>
            </div>
            <UBadge color="green" size="xs">{{ loc.speed || 0 }} km/h</UBadge>
          </div>
          <div class="mt-2 space-y-1 text-xs">
            <div class="flex items-center gap-1 text-gray-600">
              <UIcon name="i-heroicons-map-pin" class="w-3 h-3" />
              <span class="truncate">{{ loc.destination || 'Unknown' }}</span>
            </div>
            <div v-if="loc.driver_name" class="flex items-center gap-1 text-gray-600">
              <UIcon name="i-heroicons-user" class="w-3 h-3" />
              <span>{{ loc.driver_name }}</span>
            </div>
            <div v-if="loc.purpose" class="flex items-center gap-1 text-gray-600">
              <UIcon name="i-heroicons-clipboard-document" class="w-3 h-3" />
              <span>{{ formatPurpose(loc.purpose) }}</span>
            </div>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()

definePageMeta({ layout: 'default' })

const stats = ref({
  total_vehicles: 0,
  available_vehicles: 0,
  in_use_vehicles: 0,
  maintenance_vehicles: 0,
  broken_vehicles: 0,
  active_bookings: 0,
  pending_reminders: 0,
  total_fuel_cost_month: 0,
  total_maintenance_cost_month: 0,
  total_expense_month: 0
})

const vehiclesInJourney = ref<any[]>([])
const vehicles = ref<any[]>([])
const loadingVehicles = ref(true)
const map = ref<any>(null)
const markers = ref<any[]>([])

// Live tracking state
const liveLocations = ref<any[]>([])
const isPolling = ref(false)
const seeding = ref(false)
const simulating = ref(false)
let pollingInterval: any = null

const vehicleColumns = [
  { key: 'plate_number', label: 'Plate Number' },
  { key: 'brand', label: 'Vehicle' },
  { key: 'vehicle_type', label: 'Type' },
  { key: 'status', label: 'Status' },
  { key: 'current_odometer', label: 'Odometer' }
]

const fetchStats = async () => {
  try {
    const res = await $api.get('/fleet/stats')
    stats.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchVehicles = async () => {
  loadingVehicles.value = true
  try {
    const res = await $api.get('/fleet/vehicles')
    vehicles.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loadingVehicles.value = false
  }
}

const fetchVehiclesInJourney = async () => {
  try {
    const res = await $api.get('/fleet/vehicles-in-journey')
    vehiclesInJourney.value = res.data.vehicles || []
    if (map.value && vehiclesInJourney.value.length > 0) {
      updateMapMarkers()
    }
  } catch (e) {
    console.error(e)
  }
}

// Fetch live locations from MongoDB
const fetchLiveLocations = async () => {
  try {
    const res = await $api.get('/fleet/vehicle-locations')
    liveLocations.value = res.data.locations || []
    if (map.value) {
      updateLiveMapMarkers()
    }
  } catch (e) {
    console.error(e)
  }
}

// Seed 3 sample vehicles with journey data
const seedJourneyData = async () => {
  seeding.value = true
  try {
    await $api.post('/fleet/seed-journey-data')
    await fetchLiveLocations()
    await fetchStats()
    await fetchVehicles()
  } catch (e) {
    console.error(e)
  } finally {
    seeding.value = false
  }
}

// Simulate all vehicle movements
const simulateAllJourneys = async () => {
  simulating.value = true
  try {
    await $api.post('/fleet/simulate-all-journeys')
    await fetchLiveLocations()
  } catch (e) {
    console.error(e)
  } finally {
    simulating.value = false
  }
}

// Start polling for live updates
const startPolling = () => {
  if (pollingInterval) return
  isPolling.value = true
  pollingInterval = setInterval(async () => {
    await fetchLiveLocations()
  }, 5000) // Poll every 5 seconds
}

// Stop polling
const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  isPolling.value = false
}

// Focus on vehicle in map
const focusVehicleOnMap = (loc: any) => {
  if (!map.value || !loc.lat || !loc.lng) return
  map.value.setView([loc.lat, loc.lng], 14)
  
  // Find and open marker popup
  const marker = markers.value.find(m => m.getLatLng && 
    Math.abs(m.getLatLng().lat - loc.lat) < 0.001 &&
    Math.abs(m.getLatLng().lng - loc.lng) < 0.001
  )
  if (marker) marker.openPopup()
}

const refreshAll = () => {
  fetchStats()
  fetchVehicles()
  fetchLiveLocations()
}

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(val)
}

const formatPurpose = (p: string) => {
  const labels: Record<string, string> = {
    BUSINESS_TRIP: 'Business Trip', DELIVERY: 'Delivery', CLIENT_VISIT: 'Client Visit',
    SITE_INSPECTION: 'Site Inspection', PICKUP: 'Pickup', EVENT: 'Event', TRAINING: 'Training', OTHER: 'Other'
  }
  return labels[p] || p
}

const getStatusColor = (s: string) => {
  const colors: Record<string, string> = {
    AVAILABLE: 'green', IN_USE: 'blue', MAINTENANCE: 'yellow', BROKEN: 'red', SOLD: 'gray'
  }
  return colors[s] || 'gray'
}

const formatStatus = (s: string) => {
  const labels: Record<string, string> = {
    AVAILABLE: 'Available', IN_USE: 'In Use', MAINTENANCE: 'Maintenance', BROKEN: 'Broken', SOLD: 'Sold'
  }
  return labels[s] || s
}

const initMap = () => {
  if (typeof window === 'undefined' || !window.L) return
  
  const L = window.L
  map.value = L.map('map').setView([-6.2088, 106.8456], 11)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value)
  
  // Check for live locations first, then fall back to vehicles in journey
  if (liveLocations.value.length > 0) {
    updateLiveMapMarkers()
  } else if (vehiclesInJourney.value.length > 0) {
    updateMapMarkers()
  }
}

// Update map with live locations from MongoDB
const updateLiveMapMarkers = () => {
  if (!map.value || typeof window === 'undefined' || !window.L) return
  
  const L = window.L
  
  // Clear existing markers
  markers.value.forEach(m => map.value.removeLayer(m))
  markers.value = []
  
  // Custom truck icon
  const truckIcon = L.divIcon({
    html: `<div class="flex items-center justify-center w-10 h-10 bg-green-600 rounded-full shadow-lg border-2 border-white animate-pulse">
      <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
        <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
      </svg>
    </div>`,
    className: 'truck-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
  })
  
  const bounds: any[] = []
  
  liveLocations.value.forEach(loc => {
    if (!loc.lat || !loc.lng) return
    
    bounds.push([loc.lat, loc.lng])
    
    // Create popup content
    const popupContent = `
      <div class="p-2 min-w-[220px]">
        <h4 class="font-bold text-lg">${loc.vehicle_plate || 'Unknown'}</h4>
        <p class="text-gray-600">${loc.vehicle_brand || ''} ${loc.vehicle_model || ''}</p>
        <p class="text-sm text-gray-500">${loc.vehicle_type || 'Vehicle'}</p>
        <hr class="my-2">
        <p><strong>Speed:</strong> ${loc.speed || 0} km/h</p>
        <p><strong>Driver:</strong> ${loc.driver_name || 'N/A'}</p>
        <p><strong>Destination:</strong> ${loc.destination || 'N/A'}</p>
        <p><strong>Purpose:</strong> ${loc.purpose || 'N/A'}</p>
        <p class="text-xs text-gray-400 mt-2">Last update: ${loc.timestamp ? new Date(loc.timestamp).toLocaleTimeString() : 'N/A'}</p>
      </div>
    `
    
    const marker = L.marker([loc.lat, loc.lng], { icon: truckIcon })
      .addTo(map.value)
      .bindPopup(popupContent, { maxWidth: 300 })
    
    markers.value.push(marker)
    
    // Draw route line if we have origin and destination
    if (loc.origin_lat && loc.origin_lng && loc.destination_lat && loc.destination_lng) {
      // Origin marker (green dot)
      const originMarker = L.marker([loc.origin_lat, loc.origin_lng], {
        icon: L.divIcon({
          html: '<div class="w-4 h-4 bg-green-600 rounded-full border-2 border-white shadow"></div>',
          className: 'origin-marker',
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        })
      }).addTo(map.value).bindPopup(`<strong>Origin:</strong> Start point`)
      markers.value.push(originMarker)
      
      // Route line from origin to current position (solid)
      const traveledLine = L.polyline([
        [loc.origin_lat, loc.origin_lng],
        [loc.lat, loc.lng]
      ], { color: '#22c55e', weight: 4, opacity: 0.8 }).addTo(map.value)
      markers.value.push(traveledLine)
      
      // Route line from current position to destination (dashed)
      const remainingLine = L.polyline([
        [loc.lat, loc.lng],
        [loc.destination_lat, loc.destination_lng]
      ], { color: '#3b82f6', weight: 3, dashArray: '10, 10', opacity: 0.6 }).addTo(map.value)
      markers.value.push(remainingLine)
      
      // Destination marker (red dot)
      const destMarker = L.marker([loc.destination_lat, loc.destination_lng], {
        icon: L.divIcon({
          html: '<div class="w-4 h-4 bg-red-600 rounded-full border-2 border-white shadow"></div>',
          className: 'dest-marker',
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        })
      }).addTo(map.value).bindPopup(`<strong>Destination:</strong> ${loc.destination || 'End point'}`)
      markers.value.push(destMarker)
    }
  })
  
  // Fit bounds
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

const updateMapMarkers = () => {
  if (!map.value || typeof window === 'undefined' || !window.L) return
  
  const L = window.L
  
  // Clear existing markers
  markers.value.forEach(m => map.value.removeLayer(m))
  markers.value = []
  
  // Custom truck icon
  const truckIcon = L.divIcon({
    html: `<div class="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-full shadow-lg border-2 border-white">
      <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
        <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
      </svg>
    </div>`,
    className: 'truck-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
  })
  
  const bounds: any[] = []
  
  vehiclesInJourney.value.forEach(item => {
    const pos = item.current_position
    if (!pos?.lat || !pos?.lng) return
    
    bounds.push([pos.lat, pos.lng])
    
    // Create popup content
    const popupContent = `
      <div class="p-2 min-w-[250px]">
        <h4 class="font-bold text-lg">${item.vehicle.plate_number}</h4>
        <p class="text-gray-600">${item.vehicle.brand} ${item.vehicle.model} (${item.vehicle.year || 'N/A'})</p>
        <p class="text-sm text-gray-500">${item.vehicle.vehicle_type || 'Vehicle'}</p>
        <hr class="my-2">
        <p><strong>Booking:</strong> ${item.booking.code}</p>
        <p><strong>Department:</strong> ${item.booking.department_name || 'N/A'}</p>
        <p><strong>Driver:</strong> ${item.driver?.name || 'N/A'}</p>
        <p><strong>Destination:</strong> ${item.booking.destination}</p>
        <hr class="my-2">
        <p><strong>Last Fuel:</strong> ${item.last_fuel?.date || 'N/A'}</p>
        <p><strong>Last Maintenance:</strong> ${item.last_maintenance?.date || 'N/A'} - ${item.last_maintenance?.service_type || ''}</p>
        <p><strong>Next Reminder:</strong> ${item.next_reminder?.title || 'None'} (${item.next_reminder?.due_date || ''})</p>
        <p><strong>Total Expense:</strong> ${formatCurrency(item.total_expense)}</p>
      </div>
    `
    
    const marker = L.marker([pos.lat, pos.lng], { icon: truckIcon })
      .addTo(map.value)
      .bindPopup(popupContent, { maxWidth: 300 })
    
    markers.value.push(marker)
    
    // Draw route if we have origin and destination
    if (item.booking.origin_lat && item.booking.origin_lng && item.booking.destination_lat && item.booking.destination_lng) {
      const routeLine = L.polyline([
        [item.booking.origin_lat, item.booking.origin_lng],
        [pos.lat, pos.lng],
        [item.booking.destination_lat, item.booking.destination_lng]
      ], { color: '#3b82f6', weight: 3, dashArray: '10, 10' }).addTo(map.value)
      markers.value.push(routeLine)
      
      // Destination marker
      const destMarker = L.marker([item.booking.destination_lat, item.booking.destination_lng], {
        icon: L.divIcon({
          html: '<div class="w-4 h-4 bg-red-600 rounded-full border-2 border-white shadow"></div>',
          className: 'dest-marker',
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        })
      }).addTo(map.value).bindPopup(`<strong>Destination:</strong> ${item.booking.destination}`)
      markers.value.push(destMarker)
    }
  })
  
  // Fit bounds
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

const focusVehicle = (item: any) => {
  if (!map.value || !item.current_position) return
  map.value.setView([item.current_position.lat, item.current_position.lng], 14)
  
  // Find and open marker popup
  const marker = markers.value.find(m => m.getLatLng && 
    Math.abs(m.getLatLng().lat - item.current_position.lat) < 0.0001 &&
    Math.abs(m.getLatLng().lng - item.current_position.lng) < 0.0001
  )
  if (marker) marker.openPopup()
}

onMounted(() => {
  fetchStats()
  fetchVehicles()
  fetchLiveLocations() // Fetch from MongoDB
  
  // Load Leaflet CSS and JS
  if (typeof window !== 'undefined' && !window.L) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
    
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = () => {
      setTimeout(() => {
        initMap()
        startPolling() // Start live updates
      }, 100)
    }
    document.head.appendChild(script)
  } else if (window.L) {
    setTimeout(() => {
      initMap()
      startPolling() // Start live updates
    }, 100)
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style>
.truck-marker {
  background: transparent !important;
  border: none !important;
}
.dest-marker {
  background: transparent !important;
  border: none !important;
}
.origin-marker {
  background: transparent !important;
  border: none !important;
}
</style>
