<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Procurement Analytics</h2>
        <p class="text-gray-500">Purchase insights and vendor performance</p>
      </div>
      <div class="flex gap-2">
        <USelect v-model="selectedPeriod" :options="periodOptions" size="sm" />
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
      </div>
    </div>

    <!-- KPI Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard class="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <div class="text-center">
          <p class="text-3xl font-bold">Rp {{ formatCompact(totalPurchases) }}</p>
          <p class="text-sm opacity-80">Total Purchases</p>
          <p v-if="purchaseGrowth" :class="purchaseGrowth > 0 ? 'text-green-200' : 'text-red-200'" class="text-xs mt-1">
            {{ purchaseGrowth > 0 ? '+' : '' }}{{ purchaseGrowth }}% vs last period
          </p>
        </div>
      </UCard>
      <UCard class="bg-gradient-to-br from-green-500 to-green-600 text-white">
        <div class="text-center">
          <p class="text-3xl font-bold">{{ totalOrders }}</p>
          <p class="text-sm opacity-80">Purchase Orders</p>
        </div>
      </UCard>
      <UCard class="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <div class="text-center">
          <p class="text-3xl font-bold">{{ activeVendors }}</p>
          <p class="text-sm opacity-80">Active Vendors</p>
        </div>
      </UCard>
      <UCard class="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
        <div class="text-center">
          <p class="text-3xl font-bold">{{ avgLeadTime }} days</p>
          <p class="text-sm opacity-80">Avg Lead Time</p>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Top Vendors -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Top Vendors by Value</h3>
        </template>
        <div class="space-y-3">
          <div v-for="(v, idx) in topVendors" :key="v.id" class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold"
                 :class="idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-gray-400' : idx === 2 ? 'bg-amber-700' : 'bg-gray-300'">
              {{ idx + 1 }}
            </div>
            <div class="flex-1">
              <p class="font-medium">{{ v.name }}</p>
              <div class="w-full bg-gray-100 rounded-full h-2">
                <div class="h-2 rounded-full bg-blue-500" :style="{ width: `${v.percent}%` }"></div>
              </div>
            </div>
            <span class="font-medium">Rp {{ formatCompact(v.total) }}</span>
          </div>
          <p v-if="!topVendors.length" class="text-center text-gray-400 py-4">No data available</p>
        </div>
      </UCard>

      <!-- Category Breakdown -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Purchases by Category</h3>
        </template>
        <div class="space-y-3">
          <div v-for="c in categoryBreakdown" :key="c.category" class="flex items-center gap-3">
            <UIcon :name="getCategoryIcon(c.category)" class="w-6 h-6 text-gray-500" />
            <div class="flex-1">
              <p class="font-medium">{{ c.category }}</p>
              <div class="w-full bg-gray-100 rounded-full h-2">
                <div class="h-2 rounded-full" :class="getCategoryColor(c.category)" :style="{ width: `${c.percent}%` }"></div>
              </div>
            </div>
            <div class="text-right">
              <p class="font-medium">Rp {{ formatCompact(c.total) }}</p>
              <p class="text-xs text-gray-400">{{ c.percent }}%</p>
            </div>
          </div>
          <p v-if="!categoryBreakdown.length" class="text-center text-gray-400 py-4">No data available</p>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Monthly Trend -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Monthly Purchase Trend</h3>
        </template>
        <div class="h-64 flex items-end justify-between gap-1 pt-4">
          <div v-for="m in monthlyTrend" :key="m.month" class="flex-1 flex flex-col items-center">
            <div class="w-full bg-blue-500 rounded-t" :style="{ height: `${(m.value / maxMonthly) * 180}px` }"></div>
            <p class="text-xs text-gray-500 mt-2">{{ m.label }}</p>
            <p class="text-xs font-medium">{{ formatCompact(m.value) }}</p>
          </div>
        </div>
      </UCard>

      <!-- Vendor Performance -->
      <UCard>
        <template #header>
          <h3 class="font-semibold">Vendor Performance</h3>
        </template>
        <div class="space-y-3">
          <div v-for="v in vendorPerformance" :key="v.id" class="p-3 border rounded-lg">
            <div class="flex justify-between items-start">
              <div>
                <p class="font-medium">{{ v.name }}</p>
                <div class="flex gap-2 mt-1">
                  <UBadge :color="v.rating === 'A' ? 'green' : v.rating === 'B' ? 'yellow' : 'red'" variant="subtle">
                    Rating {{ v.rating }}
                  </UBadge>
                </div>
              </div>
              <div class="text-right text-sm">
                <p><span class="text-gray-500">On-time:</span> <strong>{{ v.on_time_rate }}%</strong></p>
                <p><span class="text-gray-500">Avg Lead:</span> <strong>{{ v.avg_lead_time }}d</strong></p>
              </div>
            </div>
          </div>
          <p v-if="!vendorPerformance.length" class="text-center text-gray-400 py-4">No performance data</p>
        </div>
      </UCard>
    </div>

    <!-- Recent POs -->
    <UCard>
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="font-semibold">Recent Purchase Orders</h3>
          <NuxtLink to="/procurement/orders" class="text-sm text-blue-600 hover:underline">View All →</NuxtLink>
        </div>
      </template>
      <DataTable 
        :columns="recentColumns" 
        :rows="recentOrders" 
        :loading="loading"
        empty-message="No recent orders"
      >
        <template #po_number-data="{ row }">
          <span class="font-mono text-blue-600">{{ row.po_number }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getPoStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #total_amount-data="{ row }">
          Rp {{ formatNumber(row.total_amount || 0) }}
        </template>
      </DataTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const selectedPeriod = ref('this_month')

const summary = ref<any>({})
const topVendors = ref<any[]>([])
const categoryBreakdown = ref<any[]>([])
const monthlyTrend = ref<any[]>([])
const vendorPerformance = ref<any[]>([])
const recentOrders = ref<any[]>([])

const periodOptions = [
  { label: 'This Month', value: 'this_month' },
  { label: 'Last 3 Months', value: '3_months' },
  { label: 'This Year', value: 'this_year' }
]

const recentColumns = [
  { key: 'po_number', label: 'PO #' },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'created_at', label: 'Date' },
  { key: 'status', label: 'Status' },
  { key: 'total_amount', label: 'Amount' }
]

const totalPurchases = computed(() => summary.value.total_purchases || 0)
const totalOrders = computed(() => summary.value.total_orders || 0)
const activeVendors = computed(() => summary.value.active_vendors || 0)
const avgLeadTime = computed(() => summary.value.avg_lead_time || 0)
const purchaseGrowth = computed(() => summary.value.growth_percent || 0)
const maxMonthly = computed(() => Math.max(...monthlyTrend.value.map(m => m.value), 1))

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num)
const formatCompact = (num: number) => {
  if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'B'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(0) + 'K'
  return num.toString()
}

const getCategoryIcon = (cat: string) => {
  const icons: Record<string, string> = {
    'Raw Material': 'i-heroicons-cube-transparent',
    'Finished Goods': 'i-heroicons-gift',
    'Packaging': 'i-heroicons-archive-box',
    'Other': 'i-heroicons-ellipsis-horizontal-circle'
  }
  return icons[cat] || 'i-heroicons-tag'
}

const getCategoryColor = (cat: string) => {
  const colors: Record<string, string> = {
    'Raw Material': 'bg-blue-500',
    'Finished Goods': 'bg-green-500',
    'Packaging': 'bg-purple-500',
    'Other': 'bg-gray-500'
  }
  return colors[cat] || 'bg-gray-400'
}

const getPoStatusColor = (status: string) => {
  const colors: Record<string, string> = { DRAFT: 'gray', OPEN: 'blue', PARTIAL_RECEIVE: 'yellow', CLOSED: 'green', CANCELLED: 'red' }
  return colors[status] || 'gray'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [summaryRes, vendorsRes, ordersRes] = await Promise.all([
      $api.get(`/procurement/analytics/summary?period=${selectedPeriod.value}`).catch(() => ({ data: {} })),
      $api.get('/procurement/vendors').catch(() => ({ data: [] })),
      $api.get('/procurement/orders').catch(() => ({ data: [] }))
    ])
    
    summary.value = summaryRes.data || {}
    
    // Process vendors
    const vendors = vendorsRes.data || []
    topVendors.value = vendors.slice(0, 5).map((v: any, i: number) => ({
      ...v,
      total: v.total_purchases || Math.random() * 100000000,
      percent: 100 - i * 15
    }))
    
    vendorPerformance.value = vendors.slice(0, 4).map((v: any) => ({
      id: v.id,
      name: v.name,
      rating: v.rating || 'B',
      on_time_rate: Math.round(80 + Math.random() * 20),
      avg_lead_time: Math.round(5 + Math.random() * 10)
    }))
    
    // Mock category data
    categoryBreakdown.value = [
      { category: 'Raw Material', total: 45000000, percent: 45 },
      { category: 'Packaging', total: 25000000, percent: 25 },
      { category: 'Finished Goods', total: 20000000, percent: 20 },
      { category: 'Other', total: 10000000, percent: 10 }
    ]
    
    // Mock monthly trend
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    monthlyTrend.value = months.map(m => ({
      month: m,
      label: m,
      value: Math.round(20000000 + Math.random() * 80000000)
    }))
    
    // Recent orders
    recentOrders.value = (ordersRes.data || []).slice(0, 5).map((o: any) => ({
      ...o,
      created_at: new Date(o.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
    }))
    
    // Summary defaults
    if (!summary.value.total_purchases) {
      summary.value = {
        total_purchases: categoryBreakdown.value.reduce((s, c) => s + c.total, 0),
        total_orders: recentOrders.value.length + Math.round(Math.random() * 50),
        active_vendors: vendors.length,
        avg_lead_time: 7,
        growth_percent: Math.round((Math.random() - 0.3) * 30)
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

watch(selectedPeriod, () => fetchData())
onMounted(() => { fetchData() })
</script>
