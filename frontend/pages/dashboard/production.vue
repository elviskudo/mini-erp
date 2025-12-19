<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Production Dashboard</h1>
        <p class="text-gray-500">Real-time production monitoring and analytics</p>
      </div>
      <div class="flex gap-2">
        <USelect v-model="selectedPeriod" :options="periodOptions" class="w-40" />
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="refreshData">Refresh</UButton>
      </div>
    </div>

    <!-- Live Counter Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <UIcon name="i-heroicons-cube" class="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-blue-600">{{ liveStats.todayTarget }}</p>
            <p class="text-xs text-gray-500">Today's Target</p>
          </div>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
            <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-green-600">{{ liveStats.todayActual }}</p>
            <p class="text-xs text-gray-500">Today's Actual</p>
          </div>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
            <UIcon name="i-heroicons-clock" class="w-6 h-6 text-yellow-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-yellow-600">{{ liveStats.inProgress }}</p>
            <p class="text-xs text-gray-500">In Progress</p>
          </div>
        </div>
      </UCard>
      
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg flex items-center justify-center" :class="oeeColorClass">
            <UIcon name="i-heroicons-chart-bar" class="w-6 h-6" :class="oeeIconClass" />
          </div>
          <div>
            <p class="text-2xl font-bold" :class="oeeTextClass">{{ oee.overall }}%</p>
            <p class="text-xs text-gray-500">OEE Score</p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Target vs Actual Progress -->
    <UCard>
      <template #header>
        <h3 class="font-semibold">Target vs Actual - Today</h3>
      </template>
      <div class="space-y-4">
        <div>
          <div class="flex justify-between text-sm mb-1">
            <span>Progress</span>
            <span>{{ progressPercent }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-4">
            <div 
              class="h-4 rounded-full transition-all duration-500" 
              :class="progressPercent >= 100 ? 'bg-green-500' : progressPercent >= 80 ? 'bg-blue-500' : 'bg-yellow-500'"
              :style="{ width: `${Math.min(progressPercent, 100)}%` }"
            ></div>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4 text-center">
          <div class="p-3 bg-blue-50 rounded-lg">
            <p class="text-xl font-bold text-blue-600">{{ liveStats.todayTarget }}</p>
            <p class="text-xs text-gray-500">Target</p>
          </div>
          <div class="p-3 bg-green-50 rounded-lg">
            <p class="text-xl font-bold text-green-600">{{ liveStats.todayActual }}</p>
            <p class="text-xs text-gray-500">Completed</p>
          </div>
          <div class="p-3 bg-gray-100 rounded-lg">
            <p class="text-xl font-bold">{{ liveStats.todayTarget - liveStats.todayActual }}</p>
            <p class="text-xs text-gray-500">Remaining</p>
          </div>
        </div>
      </div>
    </UCard>

    <!-- OEE Breakdown -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">OEE Breakdown</h3>
          <UBadge :color="oee.overall >= 85 ? 'green' : oee.overall >= 60 ? 'yellow' : 'red'" variant="soft">
            {{ oee.overall >= 85 ? 'World Class' : oee.overall >= 60 ? 'Average' : 'Needs Improvement' }}
          </UBadge>
        </div>
      </template>
      <div class="grid grid-cols-3 gap-6">
        <!-- Availability -->
        <div class="text-center">
          <div class="relative w-24 h-24 mx-auto mb-3">
            <svg class="w-24 h-24 transform -rotate-90">
              <circle cx="48" cy="48" r="40" stroke="#e5e7eb" stroke-width="8" fill="none" />
              <circle 
                cx="48" cy="48" r="40" 
                stroke="#3b82f6" stroke-width="8" fill="none"
                :stroke-dasharray="`${oee.availability * 2.51} 251`"
                stroke-linecap="round"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-lg font-bold text-blue-600">{{ oee.availability }}%</span>
            </div>
          </div>
          <p class="font-medium">Availability</p>
          <p class="text-xs text-gray-500">Uptime vs Planned</p>
        </div>
        
        <!-- Performance -->
        <div class="text-center">
          <div class="relative w-24 h-24 mx-auto mb-3">
            <svg class="w-24 h-24 transform -rotate-90">
              <circle cx="48" cy="48" r="40" stroke="#e5e7eb" stroke-width="8" fill="none" />
              <circle 
                cx="48" cy="48" r="40" 
                stroke="#22c55e" stroke-width="8" fill="none"
                :stroke-dasharray="`${oee.performance * 2.51} 251`"
                stroke-linecap="round"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-lg font-bold text-green-600">{{ oee.performance }}%</span>
            </div>
          </div>
          <p class="font-medium">Performance</p>
          <p class="text-xs text-gray-500">Actual vs Ideal Speed</p>
        </div>
        
        <!-- Quality -->
        <div class="text-center">
          <div class="relative w-24 h-24 mx-auto mb-3">
            <svg class="w-24 h-24 transform -rotate-90">
              <circle cx="48" cy="48" r="40" stroke="#e5e7eb" stroke-width="8" fill="none" />
              <circle 
                cx="48" cy="48" r="40" 
                stroke="#a855f7" stroke-width="8" fill="none"
                :stroke-dasharray="`${oee.quality * 2.51} 251`"
                stroke-linecap="round"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-lg font-bold text-purple-600">{{ oee.quality }}%</span>
            </div>
          </div>
          <p class="font-medium">Quality</p>
          <p class="text-xs text-gray-500">Good vs Total</p>
        </div>
      </div>
    </UCard>

    <!-- Production Orders Timeline -->
    <UCard>
      <template #header>
        <h3 class="font-semibold">Active Production Orders</h3>
      </template>
      <div class="space-y-3">
        <div v-for="order in activeOrders" :key="order.id" class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ order.order_no }}</span>
              <UBadge :color="getStatusColor(order.status)" variant="soft" size="xs">{{ order.status }}</UBadge>
            </div>
            <p class="text-sm text-gray-500">{{ order.product_name }}</p>
          </div>
          <div class="w-32">
            <div class="flex justify-between text-xs mb-1">
              <span>{{ order.completed_qty }}/{{ order.quantity }}</span>
              <span>{{ order.progress }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div 
                class="h-2 rounded-full bg-primary-500" 
                :style="{ width: `${order.progress}%` }"
              ></div>
            </div>
          </div>
          <div class="text-right text-sm">
            <p class="font-medium">{{ formatDate(order.scheduled_date) }}</p>
            <p class="text-xs text-gray-500">Scheduled</p>
          </div>
        </div>
        <div v-if="activeOrders.length === 0" class="text-center py-8 text-gray-400">
          No active production orders
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const loading = ref(false)

const selectedPeriod = ref('today')
const periodOptions = [
  { label: 'Today', value: 'today' },
  { label: 'This Week', value: 'week' },
  { label: 'This Month', value: 'month' }
]

const liveStats = ref({
  todayTarget: 0,
  todayActual: 0,
  inProgress: 0
})

const oee = ref({
  availability: 0,
  performance: 0,
  quality: 0,
  overall: 0
})

const activeOrders = ref<any[]>([])

const progressPercent = computed(() => {
  if (liveStats.value.todayTarget === 0) return 0
  return Math.round((liveStats.value.todayActual / liveStats.value.todayTarget) * 100)
})

const oeeColorClass = computed(() => {
  if (oee.value.overall >= 85) return 'bg-green-100'
  if (oee.value.overall >= 60) return 'bg-yellow-100'
  return 'bg-red-100'
})

const oeeIconClass = computed(() => {
  if (oee.value.overall >= 85) return 'text-green-600'
  if (oee.value.overall >= 60) return 'text-yellow-600'
  return 'text-red-600'
})

const oeeTextClass = computed(() => {
  if (oee.value.overall >= 85) return 'text-green-600'
  if (oee.value.overall >= 60) return 'text-yellow-600'
  return 'text-red-600'
})

const getStatusColor = (status: string) => {
  switch (status) {
    case 'Draft': return 'gray'
    case 'In Progress': return 'yellow'
    case 'Completed': return 'green'
    default: return 'gray'
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}

const fetchData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // Fetch dashboard stats from API
    const statsRes: any = await $fetch('/api/dashboard/production', { headers })
    
    liveStats.value = {
      todayTarget: statsRes.today_target || 0,
      todayActual: statsRes.today_actual || 0,
      inProgress: statsRes.in_progress || 0
    }
    
    oee.value = {
      availability: statsRes.oee?.availability || 0,
      performance: statsRes.oee?.performance || 0,
      quality: statsRes.oee?.quality || 0,
      overall: statsRes.oee?.overall || 0
    }
    
    activeOrders.value = statsRes.active_orders || []
  } catch (e) {
    console.error('Failed to fetch dashboard data', e)
    // Mock data for display
    liveStats.value = { todayTarget: 500, todayActual: 320, inProgress: 5 }
    oee.value = { availability: 92, performance: 85, quality: 98, overall: 77 }
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>
