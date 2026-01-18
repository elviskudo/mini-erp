<template>
  <div>
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between mb-4">
          <div class="p-3 bg-blue-50 rounded-xl">
            <UIcon name="i-heroicons-shopping-bag" class="w-6 h-6 text-blue-600" />
          </div>
          <span class="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-lg">Last 30 Days</span>
        </div>
        <div>
          <div class="text-3xl font-bold text-gray-900 mb-1">Rp 18,750.00</div>
          <div class="text-sm text-gray-500 mb-4">Total Sales</div>
          <div class="flex items-center text-xs">
            <span class="text-red-500 font-medium flex items-center gap-1">
              <UIcon name="i-heroicons-arrow-trending-down" class="w-3 h-3" />
              8.2%
            </span>
            <span class="text-gray-400 ml-2">vs last quarter</span>
          </div>
        </div>
      </div>

      <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between mb-4">
          <div class="p-3 bg-indigo-50 rounded-xl">
            <UIcon name="i-heroicons-chart-bar" class="w-6 h-6 text-indigo-600" />
          </div>
          <span class="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-lg">Last 30 Days</span>
        </div>
        <div>
          <div class="text-3xl font-bold text-gray-900 mb-1">Rp 11,420.00</div>
          <div class="text-sm text-gray-500 mb-4">Avg. Sales Value</div>
          <div class="flex items-center text-xs">
            <span class="text-green-500 font-medium flex items-center gap-1">
              <UIcon name="i-heroicons-arrow-trending-up" class="w-3 h-3" />
              7.4%
            </span>
            <span class="text-gray-400 ml-2">vs last quarter</span>
          </div>
        </div>
      </div>

      <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between mb-4">
          <div class="p-3 bg-purple-50 rounded-xl">
            <UIcon name="i-heroicons-user-group" class="w-6 h-6 text-purple-600" />
          </div>
          <span class="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-lg">Last 30 Days</span>
        </div>
        <div>
          <div class="text-3xl font-bold text-gray-900 mb-1">1,085</div>
          <div class="text-sm text-gray-500 mb-4">Total Deals</div>
          <div class="flex items-center text-xs">
            <span class="text-red-500 font-medium flex items-center gap-1">
              <UIcon name="i-heroicons-arrow-trending-down" class="w-3 h-3" />
              4.7%
            </span>
            <span class="text-gray-400 ml-2">vs last quarter</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Revenue Chart Section -->
    <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 class="text-lg font-bold text-gray-900">Revenue</h3>
          <p class="text-sm text-gray-500">Monitor your revenue growth and track financial performance in real-time.</p>
        </div>
        <div class="flex gap-2">
          <USelectMenu v-model="selectedProduct" :options="['All Products', 'Course A', 'Ebook B']" />
        </div>
      </div>

      <!-- Chart Controls -->
      <div class="flex items-center justify-between mb-8 overflow-x-auto">
        <div class="flex bg-gray-50 p-1 rounded-lg">
          <button 
            v-for="tab in ['Overview', 'Forecasting', 'Comparison', 'Trends']" 
            :key="tab"
            class="px-4 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="activeTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = tab"
          >
            {{ tab }}
          </button>
        </div>
        <div class="flex gap-2">
           <UButton color="gray" variant="ghost" icon="i-heroicons-chart-pie">Line Chart</UButton>
           <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-vertical" />
        </div>
      </div>

      <!-- Big Number -->
      <div class="flex items-baseline gap-3 mb-8">
        <span class="text-4xl font-bold text-gray-900">$28,672.54</span>
        <span class="text-sm font-medium text-green-500 flex items-center gap-1">
          <UIcon name="i-heroicons-arrow-trending-up" class="w-4 h-4" />
          +8.5%
        </span>
        <span class="text-sm text-gray-400">from last period</span>
      </div>

      <!-- Chart Placeholder (Mock) -->
      <div class="h-64 w-full bg-gradient-to-b from-transparent to-blue-50/50 relative overflow-hidden rounded-xl border border-dashed border-gray-200 flex items-end justify-between px-4 pb-0">
         <!-- Simple CSS Bar Chart Mockup -->
         <div v-for="h in [40, 65, 45, 80, 55, 90, 70, 85, 60, 75, 50, 65]" :key="h" class="w-full mx-1 bg-blue-500/10 hover:bg-blue-500/20 rounded-t-sm transition-all relative group" :style="{ height: h + '%' }">
            <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                Data: {{ h * 100 }}
            </div>
            <!-- Line graph simulation -->
            <div class="absolute top-0 left-0 right-0 h-1 bg-blue-500 rounded-full"></div>
         </div>
      </div>
      <div class="flex justify-between mt-4 text-xs text-gray-400 px-2">
        <span v-for="m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']" :key="m">{{ m }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'naikin',
  middleware: 'auth'
})

const activeTab = ref('Overview')
const selectedProduct = ref('All Products')
</script>
