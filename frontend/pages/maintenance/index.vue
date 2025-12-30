<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Maintenance Dashboard</h2>
        <p class="text-gray-500">Overview of asset maintenance and work orders</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchStats">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="navigateTo('/maintenance/work-orders')">New Work Order</UButton>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ stats.total_assets }}</p>
          <p class="text-sm text-gray-500">Total Assets</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.operational_assets }}</p>
          <p class="text-sm text-gray-500">Operational</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ stats.under_maintenance }}</p>
          <p class="text-sm text-gray-500">Under Maintenance</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ stats.broken_assets }}</p>
          <p class="text-sm text-gray-500">Broken</p>
        </div>
      </UCard>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Work Order Stats -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Work Orders</h3>
        </template>
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-blue-600">{{ stats.pending_work_orders }}</p>
            <p class="text-sm text-gray-500">Pending</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-yellow-600">{{ stats.in_progress_work_orders }}</p>
            <p class="text-sm text-gray-500">In Progress</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-green-600">{{ stats.completed_this_month }}</p>
            <p class="text-sm text-gray-500">Completed (This Month)</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-purple-600">{{ formatCurrency(stats.total_costs_this_month) }}</p>
            <p class="text-sm text-gray-500">Costs (This Month)</p>
          </div>
        </div>
      </UCard>

      <!-- Schedule Stats -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Maintenance Schedules</h3>
        </template>
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center p-4 bg-red-50 rounded-lg">
            <p class="text-2xl font-bold text-red-600">{{ stats.overdue_schedules }}</p>
            <p class="text-sm text-gray-500">Overdue</p>
          </div>
          <div class="text-center p-4 bg-blue-50 rounded-lg">
            <p class="text-2xl font-bold text-blue-600">{{ stats.upcoming_schedules }}</p>
            <p class="text-sm text-gray-500">Upcoming</p>
          </div>
        </div>
        <div class="mt-4 flex gap-2">
          <UButton block color="gray" variant="outline" @click="navigateTo('/maintenance/schedules')">View Schedules</UButton>
        </div>
      </UCard>
    </div>

    <!-- Recent Work Orders -->
    <UCard>
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="font-semibold">Recent Work Orders</h3>
          <UButton size="xs" variant="ghost" @click="navigateTo('/maintenance/work-orders')">View All</UButton>
        </div>
      </template>
      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin" />
      </div>
      <div v-else-if="recentWorkOrders.length === 0" class="text-center py-8 text-gray-500">
        No work orders yet
      </div>
      <div v-else class="space-y-3">
        <div v-for="wo in recentWorkOrders" :key="wo.id" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer" @click="navigateTo(`/maintenance/work-orders?id=${wo.id}`)">
          <div class="flex items-center gap-3">
            <UBadge :color="getStatusColor(wo.status)" variant="subtle" size="sm">{{ wo.status }}</UBadge>
            <div>
              <p class="font-medium">{{ wo.title }}</p>
              <p class="text-sm text-gray-500">{{ wo.code }} • {{ wo.asset_name }}</p>
            </div>
          </div>
          <div class="text-right">
            <UBadge :color="getPriorityColor(wo.priority)" variant="outline" size="xs">{{ wo.priority }}</UBadge>
            <p class="text-xs text-gray-400 mt-1">{{ formatDate(wo.created_at) }}</p>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const stats = ref<any>({
  total_assets: 0,
  operational_assets: 0,
  under_maintenance: 0,
  broken_assets: 0,
  total_work_orders: 0,
  pending_work_orders: 0,
  in_progress_work_orders: 0,
  completed_this_month: 0,
  overdue_schedules: 0,
  upcoming_schedules: 0,
  total_costs_this_month: 0
})
const recentWorkOrders = ref<any[]>([])

const fetchStats = async () => {
  loading.value = true
  try {
    const [statsRes, woRes] = await Promise.all([
      $api.get('/maintenance/stats'),
      $api.get('/maintenance/work-orders')
    ])
    stats.value = statsRes.data
    recentWorkOrders.value = woRes.data.slice(0, 5)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value: number) => {
  if (!value) return 'Rp 0'
  if (value >= 1000000) return `Rp ${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `Rp ${(value / 1000).toFixed(0)}k`
  return `Rp ${value}`
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    DRAFT: 'gray', SCHEDULED: 'blue', IN_PROGRESS: 'yellow', COMPLETED: 'green', CANCELLED: 'red'
  }
  return colors[status] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    LOW: 'gray', MEDIUM: 'blue', HIGH: 'orange', URGENT: 'red'
  }
  return colors[priority] || 'gray'
}

onMounted(() => {
  fetchStats()
})
</script>
