<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Employee Leaderboards</h2>
        <p class="text-gray-500 text-sm">Track top performers based on attendance and KPIs</p>
      </div>
      <div class="flex gap-2">
        <USelect v-model="selectedPeriod" :options="periodOptions" class="w-40" />
        <UButton variant="ghost" icon="i-heroicons-arrow-path" @click="fetchLeaderboards" />
      </div>
    </div>

    <!-- Top 3 Podium -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <!-- 2nd Place -->
      <UCard v-if="topThree[1]" :ui="{ body: { padding: 'p-6' } }" class="order-2 md:order-1">
        <div class="text-center">
          <div class="relative inline-block">
            <img 
              v-if="topThree[1].profile_photo_url" 
              :src="topThree[1].profile_photo_url" 
              class="w-20 h-20 rounded-full object-cover mx-auto border-4 border-gray-300"
            />
            <div v-else class="w-20 h-20 rounded-full bg-gray-200 mx-auto flex items-center justify-center border-4 border-gray-300">
              <span class="text-2xl font-bold text-gray-500">{{ topThree[1].first_name?.[0] }}</span>
            </div>
            <div class="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-gray-300 text-gray-700 rounded-full w-8 h-8 flex items-center justify-center font-bold">
              2
            </div>
          </div>
          <h3 class="font-semibold mt-4">{{ topThree[1].first_name }} {{ topThree[1].last_name }}</h3>
          <p class="text-sm text-gray-500">{{ topThree[1].position_name }}</p>
          <p class="text-2xl font-bold text-gray-600 mt-2">{{ topThree[1].total_score }}</p>
          <p class="text-xs text-gray-500">points</p>
        </div>
      </UCard>

      <!-- 1st Place -->
      <UCard v-if="topThree[0]" :ui="{ body: { padding: 'p-6' } }" class="order-1 md:order-2 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20">
        <div class="text-center">
          <div class="relative inline-block">
            <img 
              v-if="topThree[0].profile_photo_url" 
              :src="topThree[0].profile_photo_url" 
              class="w-24 h-24 rounded-full object-cover mx-auto border-4 border-yellow-400"
            />
            <div v-else class="w-24 h-24 rounded-full bg-yellow-200 mx-auto flex items-center justify-center border-4 border-yellow-400">
              <span class="text-3xl font-bold text-yellow-700">{{ topThree[0].first_name?.[0] }}</span>
            </div>
            <div class="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-yellow-400 text-yellow-900 rounded-full w-10 h-10 flex items-center justify-center font-bold shadow-lg">
              <UIcon name="i-heroicons-trophy" class="w-5 h-5" />
            </div>
          </div>
          <h3 class="font-bold text-lg mt-4">{{ topThree[0].first_name }} {{ topThree[0].last_name }}</h3>
          <p class="text-sm text-gray-500">{{ topThree[0].position_name }}</p>
          <p class="text-3xl font-bold text-yellow-600 mt-2">{{ topThree[0].total_score }}</p>
          <p class="text-xs text-gray-500">points</p>
        </div>
      </UCard>

      <!-- 3rd Place -->
      <UCard v-if="topThree[2]" :ui="{ body: { padding: 'p-6' } }" class="order-3">
        <div class="text-center">
          <div class="relative inline-block">
            <img 
              v-if="topThree[2].profile_photo_url" 
              :src="topThree[2].profile_photo_url" 
              class="w-20 h-20 rounded-full object-cover mx-auto border-4 border-orange-300"
            />
            <div v-else class="w-20 h-20 rounded-full bg-orange-100 mx-auto flex items-center justify-center border-4 border-orange-300">
              <span class="text-2xl font-bold text-orange-600">{{ topThree[2].first_name?.[0] }}</span>
            </div>
            <div class="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-orange-400 text-orange-900 rounded-full w-8 h-8 flex items-center justify-center font-bold">
              3
            </div>
          </div>
          <h3 class="font-semibold mt-4">{{ topThree[2].first_name }} {{ topThree[2].last_name }}</h3>
          <p class="text-sm text-gray-500">{{ topThree[2].position_name }}</p>
          <p class="text-2xl font-bold text-orange-600 mt-2">{{ topThree[2].total_score }}</p>
          <p class="text-xs text-gray-500">points</p>
        </div>
      </UCard>
    </div>

    <!-- Tabs -->
    <UTabs :items="tabs" v-model="activeTab">
      <template #default="{ item, selected }">
        <span :class="selected ? 'text-primary-600' : 'text-gray-500'">{{ item.label }}</span>
      </template>
    </UTabs>

    <!-- Attendance Ranking -->
    <UCard v-if="activeTab === 0">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-clock" class="w-5 h-5 text-green-600" />
          <h3 class="font-semibold">Attendance Champions</h3>
        </div>
      </template>

      <UTable :columns="attendanceColumns" :rows="attendanceRanking" :loading="loading">
        <template #rank-data="{ row, index }">
          <div class="flex items-center gap-2">
            <span v-if="index < 3" class="font-bold text-lg" :class="{
              'text-yellow-500': index === 0,
              'text-gray-400': index === 1,
              'text-orange-400': index === 2
            }">
              {{ index + 1 }}
            </span>
            <span v-else class="text-gray-500">{{ index + 1 }}</span>
          </div>
        </template>

        <template #employee-data="{ row }">
          <div class="flex items-center gap-3">
            <img 
              v-if="row.profile_photo_url" 
              :src="row.profile_photo_url" 
              class="w-8 h-8 rounded-full object-cover"
            />
            <div v-else class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <span class="text-primary-600 text-sm font-medium">{{ row.first_name?.[0] }}</span>
            </div>
            <div>
              <p class="font-medium">{{ row.first_name }} {{ row.last_name }}</p>
              <p class="text-xs text-gray-500">{{ row.department_name }}</p>
            </div>
          </div>
        </template>

        <template #on_time_rate-data="{ row }">
          <div class="flex items-center gap-2">
            <UProgress :value="row.on_time_rate" size="sm" class="w-20" />
            <span class="text-sm">{{ row.on_time_rate }}%</span>
          </div>
        </template>

        <template #attendance_score-data="{ row }">
          <span class="font-semibold text-green-600">{{ row.attendance_score }}</span>
        </template>
      </UTable>
    </UCard>

    <!-- KPI Ranking -->
    <UCard v-if="activeTab === 1">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-chart-bar" class="w-5 h-5 text-blue-600" />
          <h3 class="font-semibold">KPI Leaders</h3>
        </div>
      </template>

      <UTable :columns="kpiColumns" :rows="kpiRanking" :loading="loading">
        <template #rank-data="{ row, index }">
          <div class="flex items-center gap-2">
            <span v-if="index < 3" class="font-bold text-lg" :class="{
              'text-yellow-500': index === 0,
              'text-gray-400': index === 1,
              'text-orange-400': index === 2
            }">
              {{ index + 1 }}
            </span>
            <span v-else class="text-gray-500">{{ index + 1 }}</span>
          </div>
        </template>

        <template #employee-data="{ row }">
          <div class="flex items-center gap-3">
            <img 
              v-if="row.profile_photo_url" 
              :src="row.profile_photo_url" 
              class="w-8 h-8 rounded-full object-cover"
            />
            <div v-else class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <span class="text-primary-600 text-sm font-medium">{{ row.first_name?.[0] }}</span>
            </div>
            <div>
              <p class="font-medium">{{ row.first_name }} {{ row.last_name }}</p>
              <p class="text-xs text-gray-500">{{ row.department_name }}</p>
            </div>
          </div>
        </template>

        <template #kpi_score-data="{ row }">
          <div class="flex items-center gap-2">
            <UProgress :value="row.kpi_score" size="sm" class="w-20" color="blue" />
            <span class="text-sm font-semibold text-blue-600">{{ row.kpi_score }}</span>
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Combined Ranking -->
    <UCard v-if="activeTab === 2">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-star" class="w-5 h-5 text-purple-600" />
          <h3 class="font-semibold">Overall Performance</h3>
        </div>
      </template>

      <UTable :columns="overallColumns" :rows="overallRanking" :loading="loading">
        <template #rank-data="{ row, index }">
          <div class="flex items-center gap-2">
            <span v-if="index < 3" class="font-bold text-lg" :class="{
              'text-yellow-500': index === 0,
              'text-gray-400': index === 1,
              'text-orange-400': index === 2
            }">
              {{ index + 1 }}
            </span>
            <span v-else class="text-gray-500">{{ index + 1 }}</span>
          </div>
        </template>

        <template #employee-data="{ row }">
          <div class="flex items-center gap-3">
            <img 
              v-if="row.profile_photo_url" 
              :src="row.profile_photo_url" 
              class="w-8 h-8 rounded-full object-cover"
            />
            <div v-else class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <span class="text-primary-600 text-sm font-medium">{{ row.first_name?.[0] }}</span>
            </div>
            <div>
              <p class="font-medium">{{ row.first_name }} {{ row.last_name }}</p>
              <p class="text-xs text-gray-500">{{ row.position_name }}</p>
            </div>
          </div>
        </template>

        <template #total_score-data="{ row }">
          <span class="font-bold text-purple-600 text-lg">{{ row.total_score }}</span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()

definePageMeta({ layout: 'default' })

const tabs = [
  { label: 'Attendance', key: 'attendance' },
  { label: 'KPI', key: 'kpi' },
  { label: 'Overall', key: 'overall' }
]
const activeTab = ref(0)

const periodOptions = [
  { label: 'This Month', value: 'month' },
  { label: 'This Quarter', value: 'quarter' },
  { label: 'This Year', value: 'year' }
]
const selectedPeriod = ref('month')

const loading = ref(false)
const attendanceRanking = ref<any[]>([])
const kpiRanking = ref<any[]>([])
const overallRanking = ref<any[]>([])

const topThree = computed(() => overallRanking.value.slice(0, 3))

const attendanceColumns = [
  { key: 'rank', label: '#' },
  { key: 'employee', label: 'Employee' },
  { key: 'days_present', label: 'Days Present' },
  { key: 'on_time_rate', label: 'On Time Rate' },
  { key: 'attendance_score', label: 'Score' }
]

const kpiColumns = [
  { key: 'rank', label: '#' },
  { key: 'employee', label: 'Employee' },
  { key: 'completed_tasks', label: 'Tasks Completed' },
  { key: 'kpi_score', label: 'KPI Score' }
]

const overallColumns = [
  { key: 'rank', label: '#' },
  { key: 'employee', label: 'Employee' },
  { key: 'attendance_score', label: 'Attendance' },
  { key: 'kpi_score', label: 'KPI' },
  { key: 'total_score', label: 'Total' }
]

const fetchLeaderboards = async () => {
  loading.value = true
  try {
    // Fetch employees as base data
    const empRes = await $api.get('/hr/employees')
    const employees = empRes.data
    
    // Generate mock leaderboard data based on employees
    // In production, this would come from actual attendance and KPI data
    attendanceRanking.value = employees.map((e: any) => ({
      ...e,
      days_present: Math.floor(Math.random() * 10) + 15,
      on_time_rate: Math.floor(Math.random() * 30) + 70,
      attendance_score: Math.floor(Math.random() * 30) + 70
    })).sort((a: any, b: any) => b.attendance_score - a.attendance_score)
    
    kpiRanking.value = employees.map((e: any) => ({
      ...e,
      completed_tasks: Math.floor(Math.random() * 20) + 5,
      kpi_score: Math.floor(Math.random() * 40) + 60
    })).sort((a: any, b: any) => b.kpi_score - a.kpi_score)
    
    overallRanking.value = employees.map((e: any) => {
      const attScore = Math.floor(Math.random() * 30) + 70
      const kpiScore = Math.floor(Math.random() * 40) + 60
      return {
        ...e,
        attendance_score: attScore,
        kpi_score: kpiScore,
        total_score: Math.round((attScore + kpiScore) / 2)
      }
    }).sort((a: any, b: any) => b.total_score - a.total_score)
    
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

watch(selectedPeriod, fetchLeaderboards)

onMounted(() => {
  fetchLeaderboards()
})
</script>
