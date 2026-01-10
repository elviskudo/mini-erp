<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Profit & Loss Statement</h1>
        <p class="text-xs text-gray-500">Income statement for the selected period</p>
      </div>
      <div class="flex gap-2 items-center">
        <DatePicker v-model="dateRange" mode="range" placeholder="Select period" class="w-52" />
        <UButton @click="fetchData" icon="i-heroicons-arrow-path" size="sm">Generate</UButton>
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
      </div>
    </div>

    <!-- Summary Cards with Chart -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard class="col-span-3">
        <div class="grid grid-cols-3 gap-4 text-center">
          <div class="p-3 bg-green-50 rounded-lg">
            <p class="text-xs text-gray-500">Total Revenue</p>
            <p class="text-lg font-bold text-green-600">{{ formatCurrencyCompact(totalRevenue) }}</p>
          </div>
          <div class="p-3 bg-red-50 rounded-lg">
            <p class="text-xs text-gray-500">Total Expenses</p>
            <p class="text-lg font-bold text-red-600">{{ formatCurrencyCompact(totalExpenses) }}</p>
          </div>
          <div :class="['p-3 rounded-lg', netIncome >= 0 ? 'bg-blue-50' : 'bg-orange-50']">
            <p class="text-xs text-gray-500">Net {{ netIncome >= 0 ? 'Profit' : 'Loss' }}</p>
            <p :class="['text-lg font-bold', netIncome >= 0 ? 'text-blue-600' : 'text-orange-600']">{{ formatCurrencyCompact(netIncome) }}</p>
          </div>
        </div>
      </UCard>
      <!-- Pie Chart -->
      <UCard :ui="{ body: { padding: 'p-2' } }">
        <div class="h-32">
          <canvas ref="pieChartRef"></canvas>
        </div>
      </UCard>
    </div>

    <!-- Bar Chart -->
    <UCard>
      <template #header>
        <h3 class="font-semibold text-sm">Revenue vs Expenses by Category</h3>
      </template>
      <div class="h-48">
        <canvas ref="barChartRef"></canvas>
      </div>
    </UCard>

    <!-- Detail Table -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Revenue -->
      <UCard>
        <template #header>
          <h3 class="font-semibold text-sm text-green-700">Revenue</h3>
        </template>
        <div class="space-y-1">
          <div v-for="item in revenueItems" :key="item.name" class="flex justify-between py-1.5 px-2 hover:bg-gray-50 text-xs">
            <span :style="{ paddingLeft: `${item.level * 12}px` }" :class="item.level === 0 ? 'font-semibold' : ''">{{ item.name }}</span>
            <span :class="item.level === 0 ? 'font-semibold' : ''">{{ formatCurrency(item.amount) }}</span>
          </div>
          <div class="flex justify-between py-2 px-2 bg-green-100 font-bold text-green-700 rounded text-sm mt-2">
            <span>Total Revenue</span>
            <span>{{ formatCurrency(totalRevenue) }}</span>
          </div>
        </div>
      </UCard>

      <!-- Expenses -->
      <UCard>
        <template #header>
          <h3 class="font-semibold text-sm text-red-700">Expenses</h3>
        </template>
        <div class="space-y-1">
          <div v-for="item in expenseItems" :key="item.name" class="flex justify-between py-1.5 px-2 hover:bg-gray-50 text-xs">
            <span :style="{ paddingLeft: `${item.level * 12}px` }" :class="item.level === 0 ? 'font-semibold' : ''">{{ item.name }}</span>
            <span :class="item.level === 0 ? 'font-semibold' : ''">{{ formatCurrency(item.amount) }}</span>
          </div>
          <div class="flex justify-between py-2 px-2 bg-red-100 font-bold text-red-700 rounded text-sm mt-2">
            <span>Total Expenses</span>
            <span>{{ formatCurrency(totalExpenses) }}</span>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Net Income -->
    <UCard :class="netIncome >= 0 ? 'bg-gradient-to-r from-green-50 to-blue-50' : 'bg-gradient-to-r from-red-50 to-orange-50'">
      <div :class="['flex justify-between items-center text-xl font-bold', netIncome >= 0 ? 'text-green-800' : 'text-red-800']">
        <span>Net {{ netIncome >= 0 ? 'Income' : 'Loss' }}</span>
        <span>{{ formatCurrency(netIncome) }}</span>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const { $api } = useNuxtApp()
const dateRange = ref<string[]>(['2026-01-01', '2026-01-31'])
const pieChartRef = ref<HTMLCanvasElement | null>(null)
const barChartRef = ref<HTMLCanvasElement | null>(null)
let pieChart: Chart | null = null
let barChart: Chart | null = null

const revenueItems = ref([
  { name: 'Sales Revenue', amount: 180000000, level: 0 },
  { name: 'Product Sales', amount: 150000000, level: 1 },
  { name: 'Service Revenue', amount: 30000000, level: 1 },
  { name: 'Other Income', amount: 20000000, level: 0 },
  { name: 'Interest Income', amount: 5000000, level: 1 },
  { name: 'Miscellaneous', amount: 15000000, level: 1 }
])

const expenseItems = ref([
  { name: 'Cost of Goods Sold', amount: 50000000, level: 0 },
  { name: 'Operating Expenses', amount: 72500000, level: 0 },
  { name: 'Salaries & Wages', amount: 45000000, level: 1 },
  { name: 'Rent', amount: 10000000, level: 1 },
  { name: 'Utilities', amount: 5000000, level: 1 },
  { name: 'Marketing', amount: 8000000, level: 1 },
  { name: 'Office Supplies', amount: 2500000, level: 1 },
  { name: 'Depreciation', amount: 2000000, level: 1 }
])

const totalRevenue = computed(() => revenueItems.value.filter(i => i.level === 0).reduce((sum, i) => sum + i.amount, 0))
const totalExpenses = computed(() => expenseItems.value.filter(i => i.level === 0).reduce((sum, i) => sum + i.amount, 0))
const netIncome = computed(() => totalRevenue.value - totalExpenses.value)
const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const drawCharts = () => {
  // Pie Chart
  if (pieChartRef.value) {
    if (pieChart) pieChart.destroy()
    pieChart = new Chart(pieChartRef.value, {
      type: 'doughnut',
      data: {
        labels: ['Revenue', 'Expenses'],
        datasets: [{ data: [totalRevenue.value, totalExpenses.value], backgroundColor: ['#22c55e', '#ef4444'] }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { font: { size: 10 } } } } }
    })
  }

  // Bar Chart
  if (barChartRef.value) {
    if (barChart) barChart.destroy()
    const revenueByCategory = revenueItems.value.filter(i => i.level === 0)
    const expenseByCategory = expenseItems.value.filter(i => i.level === 0)
    barChart = new Chart(barChartRef.value, {
      type: 'bar',
      data: {
        labels: [...revenueByCategory.map(r => r.name), ...expenseByCategory.map(e => e.name)],
        datasets: [{
          label: 'Amount',
          data: [...revenueByCategory.map(r => r.amount), ...expenseByCategory.map(e => e.amount)],
          backgroundColor: [...revenueByCategory.map(() => '#22c55e'), ...expenseByCategory.map(() => '#ef4444')]
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: (v) => `${Number(v) / 1000000}M` } } } }
    })
  }
}

const fetchData = async () => {
  try {
    const res = await $api.get('/finance/reports/pl', { params: { date_from: dateRange.value[0], date_to: dateRange.value[1] } })
    if (res.data) {
      revenueItems.value = res.data.revenue || revenueItems.value
      expenseItems.value = res.data.expenses || expenseItems.value
    }
  } catch { /* use mock data */ }
  drawCharts()
}

const doExport = (format: string) => {
  const allItems = [...revenueItems.value.map(r => ({ ...r, type: 'Revenue' })), ...expenseItems.value.map(e => ({ ...e, type: 'Expense' }))]
  const cols = [{ key: 'type', label: 'Type' }, { key: 'name', label: 'Account' }, { key: 'amount', label: 'Amount' }]
  if (format === 'csv') exportToCSV(allItems, 'profit_loss', cols)
  else if (format === 'xlsx') exportToExcel(allItems, 'profit_loss', cols)
  else exportToPDF(allItems, 'profit_loss', cols, 'Profit & Loss Statement')
}

onMounted(() => { drawCharts() })
</script>
