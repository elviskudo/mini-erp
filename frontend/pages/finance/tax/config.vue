<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Tax Configuration</h1>
        <p class="text-xs text-gray-500">Manage tax codes and rates</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Tax Code</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="taxCodes" :loading="loading">
        <template #code-data="{ row }">
          <span class="font-medium text-primary-600 cursor-pointer hover:underline" @click="openForm(row)">{{ row.code }}</span>
        </template>
        <template #rate-data="{ row }">
          <span class="font-semibold">{{ row.rate }}%</span>
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="soft" size="xs">
            {{ row.is_active ? 'Active' : 'Inactive' }}
          </UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="2xs" variant="ghost" icon="i-heroicons-pencil" @click="openForm(row)" />
        </template>
      </UTable>
    </UCard>

    <FormSlideover v-model="showForm" :title="editing ? 'Edit Tax Code' : 'New Tax Code'" :loading="saving" @submit="saveForm">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Define tax codes for use in invoices, bills, and financial documents.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Tax Code" required hint="Unique identifier, e.g. PPN-11" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="PPN-11" size="sm" />
          </UFormGroup>
          <UFormGroup label="Tax Type" required hint="Category of tax" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.tax_type" :options="taxTypeOptions" option-attribute="label" value-attribute="value" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Tax Name" required hint="Display name for this tax" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="PPN 11%" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Rate (%)" required hint="Tax percentage rate" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.rate" type="number" step="0.01" placeholder="11" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Additional details about this tax code" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" size="sm" />
        </UFormGroup>
        
        <UCheckbox v-model="form.is_active" label="Active" />
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref(false)
const taxCodes = ref<any[]>([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'tax_type', label: 'Type' },
  { key: 'rate', label: 'Rate' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const taxTypeOptions = [
  { label: 'PPN (VAT)', value: 'PPN' },
  { label: 'PPh 21', value: 'PPH21' },
  { label: 'PPh 23', value: 'PPH23' },
  { label: 'PPh 26', value: 'PPH26' },
  { label: 'PPh 4(2)', value: 'PPH4_2' },
  { label: 'VAT', value: 'VAT' },
  { label: 'GST', value: 'GST' },
  { label: 'WHT', value: 'WHT' }
]

const form = reactive({ id: '', code: '', name: '', tax_type: 'PPN', rate: 0, description: '', is_active: true })

const exportItems = [[
  { label: 'Export CSV', icon: 'i-heroicons-document-text', click: () => doExport('csv') },
  { label: 'Export Excel', icon: 'i-heroicons-table-cells', click: () => doExport('xlsx') },
  { label: 'Export PDF', icon: 'i-heroicons-document', click: () => doExport('pdf') }
]]

const fetchTaxCodes = async () => {
  loading.value = true
  try {
    const res = await $api.get('/tax/codes')
    taxCodes.value = res.data
  } catch {
    taxCodes.value = [
      { id: '1', code: 'PPN-11', name: 'PPN 11%', tax_type: 'PPN', rate: 11, is_active: true },
      { id: '2', code: 'PPH21', name: 'PPh Pasal 21', tax_type: 'PPH21', rate: 5, is_active: true },
      { id: '3', code: 'PPH23', name: 'PPh Pasal 23 - Jasa', tax_type: 'PPH23', rate: 2, is_active: true },
      { id: '4', code: 'VAT-10', name: 'VAT 10%', tax_type: 'VAT', rate: 10, is_active: false }
    ]
  } finally { loading.value = false }
}

const openForm = (row?: any) => {
  if (row) {
    editing.value = true
    Object.assign(form, row)
  } else {
    editing.value = false
    Object.assign(form, { id: '', code: '', name: '', tax_type: 'PPN', rate: 0, description: '', is_active: true })
  }
  showForm.value = true
}

const saveForm = async () => {
  if (!form.code || !form.name || form.rate === undefined) {
    toast.add({ title: 'Please fill required fields', color: 'red' })
    return
  }
  saving.value = true
  try {
    if (editing.value) await $api.put(`/tax/codes/${form.id}`, form)
    else await $api.post('/tax/codes', form)
    toast.add({ title: 'Tax code saved', color: 'green' })
    showForm.value = false
    await fetchTaxCodes()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally { saving.value = false }
}

const doExport = (format: string) => {
  const cols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(taxCodes.value, 'tax_codes', cols)
  else if (format === 'xlsx') exportToExcel(taxCodes.value, 'tax_codes', cols)
  else exportToPDF(taxCodes.value, 'tax_codes', cols, 'Tax Codes')
}

onMounted(() => fetchTaxCodes())
</script>
