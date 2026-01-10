<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">e-Faktur Management</h1>
        <p class="text-xs text-gray-500">Indonesia electronic tax invoice management</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-up-tray" variant="outline" size="sm" @click="showImportModal = true">Import NSFP</UButton>
        <UDropdown :items="exportItems">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New e-Faktur</UButton>
      </div>
    </div>

    <!-- NSFP Summary -->
    <UCard>
      <div class="grid grid-cols-4 gap-4 text-center">
        <div>
          <p class="text-xs text-gray-500">Total NSFP</p>
          <p class="text-lg font-bold">{{ nsfpSummary.total }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Used</p>
          <p class="text-lg font-bold text-blue-600">{{ nsfpSummary.used }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Available</p>
          <p class="text-lg font-bold text-green-600">{{ nsfpSummary.available }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Current Range</p>
          <p class="text-sm font-mono">{{ nsfpSummary.range }}</p>
        </div>
      </div>
    </UCard>

    <!-- Filters -->
    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="w-36">
          <label class="block text-xs font-medium text-gray-600 mb-1">Period</label>
          <USelectMenu v-model="periodFilter" :options="periodOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="w-32">
          <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <USelectMenu v-model="statusFilter" :options="statusOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <UInput v-model="search" placeholder="NSFP or customer..." icon="i-heroicons-magnifying-glass" size="sm" />
        </div>
      </div>
    </UCard>

    <!-- e-Faktur Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <UTable :columns="columns" :rows="filteredEfaktur" :loading="loading">
        <template #nsfp-data="{ row }">
          <span class="font-mono text-xs text-primary-600 cursor-pointer hover:underline" @click="openForm(row)">{{ row.nsfp }}</span>
        </template>
        <template #date-data="{ row }">
          <span class="text-xs">{{ row.date }}</span>
        </template>
        <template #dpp-data="{ row }">
          <span class="text-xs">{{ formatCurrency(row.dpp) }}</span>
        </template>
        <template #ppn-data="{ row }">
          <span class="text-xs font-semibold">{{ formatCurrency(row.ppn) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="soft" size="xs">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="2xs" variant="ghost" icon="i-heroicons-pencil" @click="openForm(row)" />
            <UButton size="2xs" variant="ghost" icon="i-heroicons-paper-airplane" @click="submitEfaktur(row)" title="Submit to DJP" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Import NSFP Modal -->
    <UModal v-model="showImportModal">
      <UCard>
        <template #header><h3 class="font-semibold">Import NSFP Range</h3></template>
        <form @submit.prevent="importNsfp" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Start Number <span class="text-red-500">*</span></label>
              <UInput v-model="nsfpImport.start" placeholder="010.001-26.00000001" size="sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">End Number <span class="text-red-500">*</span></label>
              <UInput v-model="nsfpImport.end" placeholder="010.001-26.00000500" size="sm" />
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showImportModal = false">Cancel</UButton>
            <UButton type="submit" :loading="importing">Import</UButton>
          </div>
        </form>
      </UCard>
    </UModal>

    <!-- e-Faktur Form -->
    <FormSlideover v-model="showForm" :title="editing ? 'Edit e-Faktur' : 'New e-Faktur'" :loading="saving" @submit="saveForm">
      <form class="space-y-4" @submit.prevent="saveForm">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">NSFP <span class="text-red-500">*</span></label>
          <UInput v-model="form.nsfp" size="sm" :disabled="editing" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Customer <span class="text-red-500">*</span></label>
          <USelectMenu v-model="form.customer_id" :options="customerOptions" option-attribute="label" value-attribute="value" size="sm" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Date <span class="text-red-500">*</span></label>
            <DatePicker v-model="form.date" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Invoice #</label>
            <UInput v-model="form.invoice_number" size="sm" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">DPP <span class="text-red-500">*</span></label>
            <UInput v-model.number="form.dpp" type="number" size="sm" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">PPN (11%)</label>
            <UInput :value="Math.round(form.dpp * 0.11)" disabled size="sm" />
          </div>
        </div>
      </form>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, exportToCSV, exportToExcel, exportToPDF } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const showForm = ref(false)
const showImportModal = ref(false)
const editing = ref(false)
const search = ref('')
const periodFilter = ref('2026-01')
const statusFilter = ref('')

const efakturs = ref<any[]>([])
const customers = ref<any[]>([])

const nsfpSummary = ref({ total: 500, used: 125, available: 375, range: '010.001-26.00000001 - 010.001-26.00000500' })
const nsfpImport = reactive({ start: '', end: '' })

const periodOptions = [
  { label: 'January 2026', value: '2026-01' },
  { label: 'December 2025', value: '2025-12' },
  { label: 'November 2025', value: '2025-11' }
]

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Draft', value: 'Draft' },
  { label: 'Approved', value: 'Approved' },
  { label: 'Submitted', value: 'Submitted' },
  { label: 'Rejected', value: 'Rejected' }
]

const customerOptions = computed(() => customers.value.map(c => ({ label: c.name, value: c.id })))

const columns = [
  { key: 'nsfp', label: 'NSFP' },
  { key: 'date', label: 'Date' },
  { key: 'customer_name', label: 'Customer' },
  { key: 'invoice_number', label: 'Invoice #' },
  { key: 'dpp', label: 'DPP' },
  { key: 'ppn', label: 'PPN' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const form = reactive({ id: '', nsfp: '', customer_id: '', date: '', invoice_number: '', dpp: 0 })

const filteredEfaktur = computed(() => {
  let result = efakturs.value
  if (statusFilter.value) result = result.filter(e => e.status === statusFilter.value)
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter(e => e.nsfp?.includes(s) || e.customer_name?.toLowerCase().includes(s))
  }
  return result
})

const getStatusColor = (status: string) => ({ Draft: 'gray', Approved: 'blue', Submitted: 'green', Rejected: 'red' }[status] || 'gray')

const exportItems = [[
  { label: 'Export CSV (DJP Format)', click: () => doExport('csv') },
  { label: 'Export Excel', click: () => doExport('xlsx') },
  { label: 'Export PDF', click: () => doExport('pdf') }
]]

const fetchEfakturs = async () => {
  loading.value = true
  try {
    efakturs.value = (await $api.get('/tax/efaktur')).data
  } catch {
    efakturs.value = [
      { id: '1', nsfp: '010.001-26.00000001', date: '2026-01-05', customer_name: 'PT Customer Satu', invoice_number: 'INV-001', dpp: 25000000, ppn: 2750000, status: 'Submitted' },
      { id: '2', nsfp: '010.001-26.00000002', date: '2026-01-06', customer_name: 'CV Pelanggan Dua', invoice_number: 'INV-002', dpp: 50000000, ppn: 5500000, status: 'Draft' }
    ]
  } finally { loading.value = false }
}

const fetchCustomers = async () => {
  try { customers.value = (await $api.get('/crm/customers')).data } 
  catch { customers.value = [{ id: '1', name: 'PT Customer Satu' }, { id: '2', name: 'CV Pelanggan Dua' }] }
}

const openForm = (row?: any) => {
  if (row) { editing.value = true; Object.assign(form, row) }
  else { editing.value = false; Object.assign(form, { id: '', nsfp: '', customer_id: '', date: new Date().toISOString().split('T')[0], invoice_number: '', dpp: 0 }) }
  showForm.value = true
}

const saveForm = async () => {
  if (!form.nsfp || !form.customer_id || !form.dpp) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try {
    await $api.post('/tax/efaktur', form)
    toast.add({ title: 'e-Faktur saved', color: 'green' })
    showForm.value = false
    await fetchEfakturs()
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

const importNsfp = async () => {
  if (!nsfpImport.start || !nsfpImport.end) { toast.add({ title: 'Enter NSFP range', color: 'red' }); return }
  importing.value = true
  try {
    await $api.post('/tax/nsfp/import', nsfpImport)
    toast.add({ title: 'NSFP imported', color: 'green' })
    showImportModal.value = false
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { importing.value = false }
}

const submitEfaktur = async (row: any) => {
  try {
    await $api.post(`/tax/efaktur/${row.id}/submit`)
    toast.add({ title: 'e-Faktur submitted', color: 'green' })
    await fetchEfakturs()
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
}

const doExport = (format: string) => {
  const cols = columns.filter(c => c.key !== 'actions').map(c => ({ key: c.key, label: c.label }))
  if (format === 'csv') exportToCSV(filteredEfaktur.value, 'efaktur', cols)
  else if (format === 'xlsx') exportToExcel(filteredEfaktur.value, 'efaktur', cols)
  else exportToPDF(filteredEfaktur.value, 'efaktur', cols, 'e-Faktur Report')
}

onMounted(() => { fetchEfakturs(); fetchCustomers() })
</script>
