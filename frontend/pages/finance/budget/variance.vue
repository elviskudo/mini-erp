<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Budget vs Actual</h1>
        <p class="text-xs text-gray-500">Compare budgeted amounts with actual spending</p>
      </div>
      <div class="flex gap-2">
        <USelectMenu v-model="selectedBudget" :options="budgetOptions" option-attribute="label" value-attribute="value" class="w-56" size="sm" />
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">Total Budgeted</p>
          <p class="text-lg font-bold text-gray-900">{{ formatCurrencyCompact(totalBudgeted) }}</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">Total Actual</p>
          <p class="text-lg font-bold text-primary-600">{{ formatCurrencyCompact(totalActual) }}</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">Variance</p>
          <p :class="['text-lg font-bold', totalVariance >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ formatCurrencyCompact(totalVariance) }}
          </p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-xs text-gray-500">Variance %</p>
          <p :class="['text-lg font-bold', variancePercent >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ variancePercent.toFixed(1) }}%
          </p>
        </div>
      </UCard>
    </div>

    <!-- Chart -->
    <UCard>
      <template #header>
        <h3 class="font-semibold text-sm">Budget vs Actual by Category</h3>
      </template>
      <div class="h-52">
        <canvas ref="chartRef"></canvas>
      </div>
    </UCard>

    <!-- Variance Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <h3 class="font-semibold text-sm">By Account</h3>
      </template>
      <UTable :columns="columns" :rows="varianceData" :loading="loading">
        <template #account-data="{ row }">
          <div :style="{ paddingLeft: `${row.level * 16}px` }">
            <span :class="row.level === 0 ? 'font-bold text-sm' : 'text-xs'">{{ row.account }}</span>
          </div>
        </template>
        <template #budgeted-data="{ row }">
          <span class="text-xs">{{ formatCurrency(row.budgeted) }}</span>
        </template>
        <template #actual-data="{ row }">
          <span class="text-xs">{{ formatCurrency(row.actual) }}</span>
        </template>
        <template #variance-data="{ row }">
          <span :class="['text-xs font-semibold', row.variance >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ formatCurrency(row.variance) }}
          </span>
        </template>
        <template #variance_percent-data="{ row }">
          <div class="flex items-center gap-2">
            <UProgress :value="Math.min(Math.abs(row.variance_percent), 100)" :color="row.variance >= 0 ? 'green' : 'red'" size="sm" class="w-12" />
            <span :class="['text-xs', row.variance >= 0 ? 'text-green-600' : 'text-red-600']">
              {{ row.variance_percent.toFixed(1) }}%
            </span>
          </div>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const { $api } = useNuxtApp()
const loading = ref(false)
const selectedBudget = ref('1')
const chartRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const budgetOptions = [
  { label: 'Annual Budget 2026', value: '1' },
  { label: 'Annual Budget 2025', value: '2' }
]

const columns = [
  { key: 'account', label: 'Account' },
  { key: 'budgeted', label: 'Budgeted' },
  { key: 'actual', label: 'Actual' },
  { key: 'variance', label: 'Variance' },
  { key: 'variance_percent', label: '% Var' }
]

const varianceData = ref([
  { account: 'Revenue', budgeted: 1500000000, actual: 1350000000, variance: -150000000, variance_percent: -10, level: 0 },
  { account: 'Sales Revenue', budgeted: 1400000000, actual: 1280000000, variance: -120000000, variance_percent: -8.6, level: 1 },
  { account: 'Service Revenue', budgeted: 100000000, actual: 70000000, variance: -30000000, variance_percent: -30, level: 1 },
  { account: 'Expenses', budgeted: 1200000000, actual: 1100000000, variance: 100000000, variance_percent: 8.3, level: 0 },
  { account: 'Operating Expenses', budgeted: 800000000, actual: 750000000, variance: 50000000, variance_percent: 6.3, level: 1 },
  { account: 'Administrative', budgeted: 400000000, actual: 350000000, variance: 50000000, variance_percent: 12.5, level: 1 }
])

const totalBudgeted = computed(() => varianceData.value.filter(v => v.level === 0).reduce((sum, v) => sum + v.budgeted, 0))
const totalActual = computed(() => varianceData.value.filter(v => v.level === 0).reduce((sum, v) => sum + v.actual, 0))
const totalVariance = computed(() => totalBudgeted.value - totalActual.value)
const variancePercent = computed(() => totalBudgeted.value ? (totalVariance.value / totalBudgeted.value) * 100 : 0)
const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const drawChart = () => {
  if (!chartRef.value) return
  if (chart) chart.destroy()
  
  const categories = varianceData.value.filter(v => v.level === 0)
  chart = new Chart(chartRef.value, {
    type: 'bar',
    data: {
      labels: categories.map(c => c.account),
      datasets: [
        { label: 'Budgeted', data: categories.map(c => c.budgeted), backgroundColor: 'rgba(59, 130, 246, 0.7)' },
        { label: 'Actual', data: categories.map(c => c.actual), backgroundColor: 'rgba(16, 185, 129, 0.7)' }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { font: { size: 10 } } } },
      scales: { y: { ticks: { callback: (v) => `${Number(v) / 1000000000}B` } } }
    }
  })
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get(`/finance/budgets/${selectedBudget.value}/variance`)
    if (res.data) varianceData.value = res.data
  } catch { /* use mock */ }
  finally { loading.value = false }
  drawChart()
}

const doExport = (format: string) => {
  const cols = columns.map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(varianceData.value, 'budget_variance', cols)
  else if (format === 'xlsx') exportToExcel(varianceData.value, 'budget_variance', cols)
  else exportToPDF(varianceData.value, 'budget_variance', cols, 'Budget vs Actual')
}

watch(selectedBudget, () => fetchData())
onMounted(() => drawChart())
</script>
