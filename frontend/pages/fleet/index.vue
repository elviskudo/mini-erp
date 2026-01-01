<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Fleet Dashboard</h2>
        <p class="text-gray-500">Overview of fleet operations</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchStats">Refresh</UButton>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ stats.total_vehicles }}</p>
          <p class="text-sm text-gray-500">Total Vehicles</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.available_vehicles }}</p>
          <p class="text-sm text-gray-500">Available</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ stats.in_use_vehicles }}</p>
          <p class="text-sm text-gray-500">In Use</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ stats.maintenance_vehicles }}</p>
          <p class="text-sm text-gray-500">Maintenance</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ stats.broken_vehicles }}</p>
          <p class="text-sm text-gray-500">Broken</p>
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
            <p class="text-sm text-gray-500">Active Bookings</p>
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
            <p class="text-sm text-gray-500">Pending Reminders</p>
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
            <p class="text-sm text-gray-500">Fuel This Month</p>
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
            <p class="text-sm text-gray-500">Maintenance This Month</p>
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

const fetchStats = async () => {
  try {
    const res = await $api.get('/fleet/stats')
    stats.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(val)
}

onMounted(() => {
  fetchStats()
})
</script>
