<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Withholding Tax</h1>
        <p class="text-xs text-gray-500">PPh 21, 23, 26 withholding records</p>
      </div>
      <div class="flex gap-2">
        <USelectMenu v-model="selectedPeriod" :options="periodOptions" option-attribute="label" value-attribute="value" class="w-32" size="sm" />
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Record</UButton>
      </div>
    </div>

    <!-- Summary by Type -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
      <UCard v-for="summary in summaries" :key="summary.type" :ui="{ body: { padding: 'p-3' } }">
        <div class="text-center">
          <p class="text-xs text-gray-500">{{ summary.type }}</p>
          <p class="text-lg font-bold text-gray-900">{{ formatCurrencyCompact(summary.amount) }}</p>
          <p class="text-xs text-gray-400">{{ summary.count }} transactions</p>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="p-3 flex justify-between items-center">
          <h3 class="font-semibold text-sm">Withholding Records</h3>
          <UInput v-model="search" placeholder="Search..." icon="i-heroicons-magnifying-glass" size="sm" class="w-48" />
        </div>
      </template>
      <UTable :columns="columns" :rows="filteredRecords" :loading="loading">
        <template #date-data="{ row }"><span class="text-xs">{{ formatDateShort(row.date) }}</span></template>
        <template #gross_amount-data="{ row }"><span class="text-xs">{{ formatCurrency(row.gross_amount) }}</span></template>
        <template #tax_amount-data="{ row }">
          <span class="font-semibold text-xs text-primary-600">{{ formatCurrency(row.tax_amount) }}</span>
        </template>
        <template #is_reported-data="{ row }">
          <UBadge :color="row.is_reported ? 'green' : 'yellow'" variant="soft" size="xs">
            {{ row.is_reported ? 'Reported' : 'Pending' }}
          </UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="2xs" variant="ghost" icon="i-heroicons-pencil" @click="openForm(row)" />
        </template>
      </UTable>
    </UCard>

    <FormSlideover v-model="showForm" :title="editing ? 'Edit Withholding' : 'New Withholding Record'" :loading="saving" @submit="saveRecord">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Record withholding tax (PPh 21, 23, 26, 4(2)) for income tax reporting and e-Bupot generation.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Date" required hint="Date of withholding" :ui="{ hint: 'text-xs text-gray-400' }">
            <DatePicker v-model="form.date" />
          </UFormGroup>
          <UFormGroup label="Tax Type" required hint="PPh article/type" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.tax_type" :options="taxTypes" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Bukti Potong Number" required hint="Tax withholding slip number" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.bukti_potong_number" placeholder="BP-001" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Withheld From" required hint="Person/company from whom tax is withheld" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.withheld_from" placeholder="PT Jasa Konsultan" size="sm" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Gross Amount" required hint="Total payment before tax" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.gross_amount" type="number" size="sm" />
          </UFormGroup>
          <UFormGroup label="Tax Amount" required hint="Amount of tax withheld" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.tax_amount" type="number" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Description" hint="Additional notes about this withholding" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" size="sm" />
        </UFormGroup>
        
        <UCheckbox v-model="form.is_reported" label="Already Reported" />
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatCompact, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref(false)
const selectedPeriod = ref('2026-01')
const search = ref('')
const records = ref<any[]>([])

const periodOptions = [
  { label: 'Jan 2026', value: '2026-01' }, { label: 'Dec 2025', value: '2025-12' }, { label: 'Nov 2025', value: '2025-11' }
]
const taxTypes = ['PPh 21', 'PPh 23', 'PPh 26', 'PPh 4(2)']

const columns = [
  { key: 'date', label: 'Date' },
  { key: 'bukti_potong_number', label: 'Bukti Potong #' },
  { key: 'tax_type', label: 'Type' },
  { key: 'withheld_from', label: 'Withheld From' },
  { key: 'gross_amount', label: 'Gross' },
  { key: 'tax_amount', label: 'Tax Withheld' },
  { key: 'is_reported', label: 'Status' },
  { key: 'actions', label: '' }
]

const form = reactive({ date: '', bukti_potong_number: '', tax_type: 'PPh 23', withheld_from: '', gross_amount: 0, tax_amount: 0, description: '', is_reported: false })

const summaries = computed(() => {
  const byType: Record<string, { amount: number; count: number }> = {}
  for (const r of records.value) {
    if (!byType[r.tax_type]) byType[r.tax_type] = { amount: 0, count: 0 }
    byType[r.tax_type].amount += r.tax_amount || 0
    byType[r.tax_type].count++
  }
  return Object.entries(byType).map(([type, data]) => ({ type, ...data }))
})

const filteredRecords = computed(() => {
  if (!search.value) return records.value
  const s = search.value.toLowerCase()
  return records.value.filter(r => r.withheld_from?.toLowerCase().includes(s) || r.bukti_potong_number?.toLowerCase().includes(s))
})

const exportItems = [[
  { label: 'Export CSV', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export e-Bupot', click: () => doExport('ebupot') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`

const fetchRecords = async () => {
  loading.value = true
  try {
    records.value = (await $api.get('/tax/withholding', { params: { period: selectedPeriod.value } })).data
  } catch {
    records.value = [
      { id: '1', date: '2026-01-05', bukti_potong_number: 'BP-001', tax_type: 'PPh 23', withheld_from: 'PT Jasa Konsultan', gross_amount: 50000000, tax_amount: 1000000, is_reported: true },
      { id: '2', date: '2026-01-03', bukti_potong_number: 'BP-002', tax_type: 'PPh 21', withheld_from: 'John Doe (Employee)', gross_amount: 10000000, tax_amount: 500000, is_reported: false }
    ]
  } finally { loading.value = false }
}

const openForm = (row?: any) => {
  if (row) {
    editing.value = true
    Object.assign(form, row)
  } else {
    editing.value = false
    Object.assign(form, { date: new Date().toISOString().split('T')[0], bukti_potong_number: '', tax_type: 'PPh 23', withheld_from: '', gross_amount: 0, tax_amount: 0, description: '', is_reported: false })
  }
  showForm.value = true
}

const saveRecord = async () => {
  if (!form.date || !form.bukti_potong_number || !form.withheld_from) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try {
    if (editing.value) await $api.put(`/tax/withholding/${form.id}`, form)
    else await $api.post('/tax/withholding', form)
    toast.add({ title: 'Record saved', color: 'green' })
    showForm.value = false
    await fetchRecords()
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const doExport = (format: string) => {
  const cols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredRecords.value, 'withholding_tax', cols)
  else if (format === 'xlsx') exportToExcel(filteredRecords.value, 'withholding_tax', cols)
  else if (format === 'ebupot') exportToCSV(filteredRecords.value, 'ebupot_export', cols)
  else exportToPDF(filteredRecords.value, 'withholding_tax', cols, 'Withholding Tax Records')
}

watch(selectedPeriod, () => fetchRecords())
onMounted(() => fetchRecords())
</script>
