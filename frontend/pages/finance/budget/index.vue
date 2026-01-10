<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Budgets</h1>
        <p class="text-xs text-gray-500">Manage annual budgets by department and account</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Budget</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-32">
          <label class="block text-xs font-medium text-gray-600 mb-1">Year</label>
          <USelectMenu v-model="yearFilter" :options="yearOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="w-40">
          <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <USelectMenu v-model="statusFilter" :options="statusOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="Budget name..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
      </div>
    </UCard>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredBudgets" :loading="loading">
        <template #name-data="{ row }">
          <span class="font-medium text-primary-600 cursor-pointer hover:underline" @click="openForm(row)">{{ row.name }}</span>
        </template>
        <template #total_budget-data="{ row }">
          <span class="font-semibold text-xs">{{ formatCurrencyCompact(row.total_budget) }}</span>
        </template>
        <template #spent-data="{ row }">
          <span class="text-red-600 text-xs">{{ formatCurrencyCompact(row.spent) }}</span>
        </template>
        <template #remaining-data="{ row }">
          <span :class="['text-xs font-semibold', row.remaining >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ formatCurrencyCompact(row.remaining) }}
          </span>
        </template>
        <template #utilization-data="{ row }">
          <div class="flex items-center gap-2">
            <UProgress :value="row.utilization" :color="row.utilization > 90 ? 'red' : row.utilization > 70 ? 'yellow' : 'green'" size="sm" class="w-16" />
            <span class="text-xs">{{ row.utilization }}%</span>
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="soft" size="xs">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="2xs" variant="ghost" icon="i-heroicons-pencil" @click="openForm(row)" />
        </template>
      </UTable>
    </UCard>

    <FormSlideover v-model="showForm" :title="editing ? 'Edit Budget' : 'New Budget'" :loading="saving" @submit="saveForm">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Create budget allocations to track and control spending across departments.</p>
        
        <UFormGroup label="Budget Name" required hint="Descriptive name, e.g. 'Q1 2026 Operations'" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="Q1 2026 Operations" size="sm" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Fiscal Year" required hint="Year this budget applies to" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.fiscal_year" :options="yearOptions" option-attribute="label" value-attribute="value" size="sm" />
          </UFormGroup>
          <UFormGroup label="Period" hint="Annual or specific quarter/month" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.period" :options="periodOptions" option-attribute="label" value-attribute="value" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Cost Center" hint="Department or division for this budget" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.cost_center_id" :options="costCenterOptions" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Total Budget Amount" required hint="Total allocated amount for this budget" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.total_budget" type="number" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Notes about budget purpose or restrictions" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Status" hint="Draft budgets are not active for tracking" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.status" :options="statusOptions" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref(false)
const search = ref('')
const yearFilter = ref(2026)
const statusFilter = ref('')
const budgets = ref<any[]>([])
const costCenters = ref<any[]>([])

const columns = [
  { key: 'name', label: 'Budget Name' },
  { key: 'fiscal_year', label: 'Year' },
  { key: 'cost_center_name', label: 'Cost Center' },
  { key: 'total_budget', label: 'Budget' },
  { key: 'spent', label: 'Spent' },
  { key: 'remaining', label: 'Remaining' },
  { key: 'utilization', label: 'Used' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const yearOptions = [
  { label: '2024', value: 2024 }, { label: '2025', value: 2025 }, { label: '2026', value: 2026 }, { label: '2027', value: 2027 }
]

const statusOptions = [
  { label: 'All', value: '' }, { label: 'Draft', value: 'Draft' }, { label: 'Active', value: 'Active' }, { label: 'Closed', value: 'Closed' }
]

const periodOptions = [
  { label: 'Annual', value: 'annual' }, { label: 'Q1', value: 'q1' }, { label: 'Q2', value: 'q2' }, { label: 'Q3', value: 'q3' }, { label: 'Q4', value: 'q4' },
  ...Array.from({ length: 12 }, (_, i) => ({ label: `Month ${i + 1}`, value: `m${i + 1}` }))
]

const costCenterOptions = computed(() => [
  { label: 'All Departments', value: '' },
  ...costCenters.value.map(c => ({ label: `${c.code} - ${c.name}`, value: c.id }))
])

const form = reactive({ id: '', name: '', fiscal_year: 2026, period: 'annual', cost_center_id: '', total_budget: 0, description: '', status: 'Draft' })

const filteredBudgets = computed(() => {
  let result = budgets.value
  if (yearFilter.value) result = result.filter(b => b.fiscal_year === yearFilter.value)
  if (statusFilter.value) result = result.filter(b => b.status === statusFilter.value)
  if (search.value) result = result.filter(b => b.name?.toLowerCase().includes(search.value.toLowerCase()))
  return result
})

const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`
const getStatusColor = (status: string) => ({ Draft: 'gray', Active: 'green', Closed: 'blue' }[status] || 'gray')

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const fetchBudgets = async () => {
  loading.value = true
  try {
    const res = await $api.get('/finance/budgets')
    budgets.value = res.data
  } catch {
    budgets.value = [
      { id: '1', name: 'Q1 2026 Operations', fiscal_year: 2026, period: 'q1', cost_center_name: 'Operations', total_budget: 500000000, spent: 125000000, remaining: 375000000, utilization: 25, status: 'Active' },
      { id: '2', name: 'Marketing 2026', fiscal_year: 2026, period: 'annual', cost_center_name: 'Marketing', total_budget: 200000000, spent: 180000000, remaining: 20000000, utilization: 90, status: 'Active' },
      { id: '3', name: 'IT Infrastructure', fiscal_year: 2026, period: 'annual', cost_center_name: 'IT', total_budget: 300000000, spent: 50000000, remaining: 250000000, utilization: 17, status: 'Draft' }
    ]
  } finally { loading.value = false }
}

const fetchCostCenters = async () => {
  try { costCenters.value = (await $api.get('/finance/cost-centers')).data } catch {}
}

const openForm = (row?: any) => {
  if (row) {
    editing.value = true
    Object.assign(form, row)
  } else {
    editing.value = false
    Object.assign(form, { id: '', name: '', fiscal_year: 2026, period: 'annual', cost_center_id: '', total_budget: 0, description: '', status: 'Draft' })
  }
  showForm.value = true
}

const saveForm = async () => {
  if (!form.name || !form.total_budget) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try {
    if (editing.value) await $api.put(`/finance/budgets/${form.id}`, form)
    else await $api.post('/finance/budgets', form)
    toast.add({ title: 'Budget saved', color: 'green' })
    showForm.value = false
    await fetchBudgets()
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const doExport = (format: string) => {
  const cols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredBudgets.value, 'budgets', cols)
  else if (format === 'xlsx') exportToExcel(filteredBudgets.value, 'budgets', cols)
  else exportToPDF(filteredBudgets.value, 'budgets', cols, 'Budgets')
}

onMounted(() => { fetchBudgets(); fetchCostCenters() })
</script>
