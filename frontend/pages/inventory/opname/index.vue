<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Stock Opname Dashboard</h2>
        <p class="text-gray-500">Manage stock take operations</p>
      </div>
      <UButton icon="i-heroicons-plus" color="primary" @click="$router.push('/inventory/opname/schedule')">
        New Schedule
      </UButton>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-primary-600">{{ stats.scheduled }}</p>
          <p class="text-sm text-gray-500">Scheduled</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-yellow-600">{{ stats.inProgress }}</p>
          <p class="text-sm text-gray-500">In Progress</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-orange-600">{{ stats.pendingReview }}</p>
          <p class="text-sm text-gray-500">Pending Review</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-3xl font-bold text-green-600">{{ stats.completed }}</p>
          <p class="text-sm text-gray-500">Completed (30d)</p>
        </div>
      </UCard>
    </div>

    <!-- Navigation Tabs -->
    <UCard>
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <NuxtLink to="/inventory/opname/schedule" class="block p-4 rounded-lg border-2 border-dashed border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition text-center">
          <UIcon name="i-heroicons-calendar" class="w-8 h-8 mx-auto text-primary-500" />
          <p class="mt-2 font-medium">Schedule</p>
          <p class="text-xs text-gray-500">Plan opname</p>
        </NuxtLink>
        
        <NuxtLink to="/inventory/opname/counting" class="block p-4 rounded-lg border-2 border-dashed border-gray-200 hover:border-yellow-300 hover:bg-yellow-50 transition text-center">
          <UIcon name="i-heroicons-calculator" class="w-8 h-8 mx-auto text-yellow-500" />
          <p class="mt-2 font-medium">Counting</p>
          <p class="text-xs text-gray-500">Physical count</p>
        </NuxtLink>
        
        <NuxtLink to="/inventory/opname/matching" class="block p-4 rounded-lg border-2 border-dashed border-gray-200 hover:border-orange-300 hover:bg-orange-50 transition text-center">
          <UIcon name="i-heroicons-scale" class="w-8 h-8 mx-auto text-orange-500" />
          <p class="mt-2 font-medium">Matching</p>
          <p class="text-xs text-gray-500">Variance analysis</p>
        </NuxtLink>
        
        <NuxtLink to="/inventory/opname/adjustment" class="block p-4 rounded-lg border-2 border-dashed border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition text-center">
          <UIcon name="i-heroicons-pencil-square" class="w-8 h-8 mx-auto text-blue-500" />
          <p class="mt-2 font-medium">Adjustment</p>
          <p class="text-xs text-gray-500">Review & approve</p>
        </NuxtLink>
        
        <NuxtLink to="/inventory/opname/reports" class="block p-4 rounded-lg border-2 border-dashed border-gray-200 hover:border-green-300 hover:bg-green-50 transition text-center">
          <UIcon name="i-heroicons-chart-bar" class="w-8 h-8 mx-auto text-green-500" />
          <p class="mt-2 font-medium">Reports</p>
          <p class="text-xs text-gray-500">Evaluation</p>
        </NuxtLink>
      </div>
    </UCard>

    <!-- Recent Opnames -->
    <UCard>
      <template #header>
        <div class="flex justify-between items-center">
          <span class="font-semibold">Recent Stock Opnames</span>
          <UButton size="xs" variant="ghost" to="/inventory/opname/counting">View All</UButton>
        </div>
      </template>
      
      <UTable :columns="columns" :rows="recentOpnames" :loading="loading">
        <template #opname_number-data="{ row }">
          <span class="font-mono text-sm">{{ row.opname_number || row.id?.substring(0, 8) }}</span>
        </template>
        <template #date-data="{ row }">
          {{ formatDate(row.date) }}
        </template>
        <template #warehouse-data="{ row }">
          {{ row.warehouse?.name || '-' }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #progress-data="{ row }">
          <div class="flex items-center gap-2">
            <UProgress :value="getProgress(row)" size="sm" class="w-20" />
            <span class="text-xs text-gray-500">{{ row.counted_items || 0 }}/{{ row.total_items || 0 }}</span>
          </div>
        </template>
        <template #variance-data="{ row }">
          <span :class="row.total_variance_value < 0 ? 'text-red-600' : row.total_variance_value > 0 ? 'text-green-600' : ''">
            {{ formatCurrency(row.total_variance_value || 0) }}
          </span>
        </template>
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewOpname(row)" />
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const router = useRouter()

const loading = ref(false)
const recentOpnames = ref<any[]>([])
const stats = ref({
  scheduled: 0,
  inProgress: 0,
  pendingReview: 0,
  completed: 0
})

const columns = [
  { key: 'opname_number', label: 'Number' },
  { key: 'date', label: 'Date' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'variance', label: 'Variance' },
  { key: 'actions', label: '' }
]

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Scheduled': 'blue',
    'In Progress': 'yellow',
    'Counting Done': 'orange',
    'Reviewed': 'purple',
    'Approved': 'teal',
    'Posted': 'green',
    'Cancelled': 'red'
  }
  return colors[status] || 'gray'
}

const getProgress = (row: any) => {
  if (!row.total_items) return 0
  return Math.round((row.counted_items / row.total_items) * 100)
}

const viewOpname = (row: any) => {
  router.push(`/inventory/opname/counting?id=${row.id}`)
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/opname/list', { baseURL: '/api' })
    recentOpnames.value = (res.data.data || []).slice(0, 10)
    
    // Calculate stats
    stats.value = {
      scheduled: res.data?.data.filter((o: any) => o.status === 'Scheduled').length || 0,
      inProgress: res.data?.data.filter((o: any) => o.status === 'In Progress').length || 0,
      pendingReview: res.data?.data.filter((o: any) => ['Counting Done', 'Reviewed'].includes(o.status)).length || 0,
      completed: res.data?.data.filter((o: any) => o.status === 'Posted').length || 0
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
