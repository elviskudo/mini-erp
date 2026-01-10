<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Cost Centers</h1>
        <p class="text-xs text-gray-500">Manage cost centers for expense allocation</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Cost Center</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="flattenedCenters" :loading="loading">
        <template #code-data="{ row }">
          <div :style="{ paddingLeft: `${row.level * 20}px` }">
            <span class="font-medium text-primary-600 cursor-pointer hover:underline" @click="openForm(row)">{{ row.code }}</span>
          </div>
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

    <FormSlideover v-model="showForm" :title="editing ? 'Edit Cost Center' : 'New Cost Center'" :loading="saving" @submit="saveForm">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Cost centers help track expenses by department, project, or business unit.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Code" required hint="Unique identifier, e.g. CC-PROD" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="CC-PROD" size="sm" />
          </UFormGroup>
          <UFormGroup label="Parent" hint="Select parent for hierarchy" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.parent_id" :options="parentOptions" option-attribute="label" value-attribute="value" placeholder="None (Top Level)" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Name" required hint="Descriptive name of the cost center" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="Production Department" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Manager" hint="Person responsible for this cost center" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.manager_id" :options="managerOptions" option-attribute="label" value-attribute="value" placeholder="Select manager" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Purpose and scope of this cost center" :ui="{ hint: 'text-xs text-gray-400' }">
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
const costCenters = ref<any[]>([])
const managers = ref<any[]>([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'manager_name', label: 'Manager' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const form = reactive({ id: '', code: '', name: '', parent_id: '', manager_id: '', description: '', is_active: true })

const flattenedCenters = computed(() => {
  const flatten = (items: any[], level = 0): any[] => {
    let result: any[] = []
    for (const item of items) {
      result.push({ ...item, level })
      if (item.children?.length) result = result.concat(flatten(item.children, level + 1))
    }
    return result
  }
  return flatten(costCenters.value)
})

const parentOptions = computed(() => [
  { label: 'None (Top Level)', value: '' },
  ...flattenedCenters.value.map(c => ({ label: `${c.code} - ${c.name}`, value: c.id }))
])

const managerOptions = computed(() => [
  { label: 'Select Manager', value: '' },
  ...managers.value.map(m => ({ label: m.name, value: m.id }))
])

const exportItems = [[
  { label: 'Export CSV', icon: 'i-heroicons-document-text', click: () => doExport('csv') },
  { label: 'Export Excel', icon: 'i-heroicons-table-cells', click: () => doExport('xlsx') },
  { label: 'Export PDF', icon: 'i-heroicons-document', click: () => doExport('pdf') }
]]

const fetchCostCenters = async () => {
  loading.value = true
  try {
    const res = await $api.get('/finance/cost-centers')
    costCenters.value = res.data
  } catch {
    costCenters.value = [
      { id: '1', code: 'CC-PROD', name: 'Production', manager_name: 'John Doe', is_active: true, children: [
        { id: '2', code: 'CC-PROD-A', name: 'Assembly Line A', manager_name: 'Jane Smith', is_active: true, children: [] },
        { id: '3', code: 'CC-PROD-B', name: 'Assembly Line B', manager_name: 'Bob Wilson', is_active: true, children: [] }
      ]},
      { id: '4', code: 'CC-ADMIN', name: 'Administration', manager_name: 'Alice Brown', is_active: true, children: [
        { id: '5', code: 'CC-HR', name: 'Human Resources', manager_name: 'Charlie Davis', is_active: true, children: [] },
        { id: '6', code: 'CC-FIN', name: 'Finance', manager_name: 'Diana Miller', is_active: true, children: [] }
      ]},
      { id: '7', code: 'CC-SALES', name: 'Sales & Marketing', manager_name: 'Eve Johnson', is_active: true, children: [] }
    ]
  } finally { loading.value = false }
}

const fetchManagers = async () => {
  try {
    const res = await $api.get('/hr/employees')
    managers.value = res.data.slice(0, 20)
  } catch {
    managers.value = [{ id: '1', name: 'John Doe' }, { id: '2', name: 'Jane Smith' }, { id: '3', name: 'Alice Brown' }]
  }
}

const openForm = (row?: any) => {
  if (row) {
    editing.value = true
    Object.assign(form, { id: row.id, code: row.code, name: row.name, parent_id: row.parent_id || '', manager_id: row.manager_id || '', description: row.description || '', is_active: row.is_active })
  } else {
    editing.value = false
    Object.assign(form, { id: '', code: '', name: '', parent_id: '', manager_id: '', description: '', is_active: true })
  }
  showForm.value = true
}

const saveForm = async () => {
  if (!form.code || !form.name) {
    toast.add({ title: 'Please fill required fields', color: 'red' })
    return
  }
  saving.value = true
  try {
    if (editing.value) await $api.put(`/finance/cost-centers/${form.id}`, form)
    else await $api.post('/finance/cost-centers', form)
    toast.add({ title: 'Cost center saved', color: 'green' })
    showForm.value = false
    await fetchCostCenters()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally { saving.value = false }
}

const doExport = (format: string) => {
  const cols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(flattenedCenters.value, 'cost_centers', cols)
  else if (format === 'xlsx') exportToExcel(flattenedCenters.value, 'cost_centers', cols)
  else exportToPDF(flattenedCenters.value, 'cost_centers', cols, 'Cost Centers')
}

onMounted(() => { fetchCostCenters(); fetchManagers() })
</script>
