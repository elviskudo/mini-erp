<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Marketing Campaigns</h1>
        <p class="text-gray-500">Track and manage marketing campaigns</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Campaign</UButton>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ stats.active }}</div>
          <div class="text-sm text-gray-500">Active</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ stats.leads }}</div>
          <div class="text-sm text-gray-500">Leads Generated</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-purple-600">{{ stats.conversions }}</div>
          <div class="text-sm text-gray-500">Conversions</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-600">{{ formatCurrency(stats.spent) }}</div>
          <div class="text-sm text-gray-500">Total Spent</div>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="items" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #type-data="{ row }">
          <UBadge :color="getTypeColor(row.type)" variant="subtle">{{ row.type }}</UBadge>
        </template>
        <template #budget-data="{ row }">
          {{ formatCurrency(row.budget) }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="confirmDelete(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Campaign' : 'New Campaign'" :loading="saving" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Name" required>
          <UInput v-model="form.name" placeholder="Summer Sale 2026" />
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="form.description" rows="2" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Type">
            <USelectMenu v-model="form.type" :options="['EMAIL', 'SOCIAL', 'EVENT', 'PAID_ADS', 'CONTENT']" />
          </UFormGroup>
          <UFormGroup label="Status">
            <USelectMenu v-model="form.status" :options="['draft', 'active', 'paused', 'completed']" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Start Date">
            <UInput type="date" v-model="form.start_date" />
          </UFormGroup>
          <UFormGroup label="End Date">
            <UInput type="date" v-model="form.end_date" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Budget">
            <UInput v-model.number="form.budget" type="number" placeholder="10000000" />
          </UFormGroup>
          <UFormGroup label="Spent Amount">
            <UInput v-model.number="form.spent_amount" type="number" placeholder="0" />
          </UFormGroup>
        </div>
        <UFormGroup label="Target Audience">
          <UTextarea v-model="form.target_audience" rows="2" placeholder="Age 25-45, Jakarta..." />
        </UFormGroup>
        <UFormGroup label="Goals">
          <UTextarea v-model="form.goals" rows="2" placeholder="Generate 500 leads, 50 conversions..." />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const editMode = ref(false)

const items = ref([])
const pagination = ref(null)
const currentPage = ref(1)

const stats = computed(() => ({
    active: items.value.filter((i: any) => i.status === 'active').length,
    leads: items.value.reduce((s: number, i: any) => s + (i.leads_generated || 0), 0),
    conversions: items.value.reduce((s: number, i: any) => s + (i.conversions || 0), 0),
    spent: items.value.reduce((s: number, i: any) => s + (i.spent_amount || 0), 0)
}))

const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'type', label: 'Type' },
    { key: 'budget', label: 'Budget' },
    { key: 'leads_generated', label: 'Leads' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const getTypeColor = (type: string) => ({ EMAIL: 'blue', SOCIAL: 'purple', EVENT: 'green', PAID_ADS: 'orange', CONTENT: 'gray' }[type] || 'gray')
const getStatusColor = (status: string) => ({ draft: 'gray', active: 'green', paused: 'yellow', completed: 'blue' }[status] || 'gray')

const form = reactive({
    id: '', name: '', description: '', type: 'EMAIL', status: 'draft',
    start_date: '', end_date: '', budget: 0, spent_amount: 0,
    target_audience: '', goals: ''
})

const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/crm/campaigns', { params: { page: currentPage.value } })
        items.value = res.data?.data || []
        pagination.value = res.data?.meta?.pagination
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const openCreate = () => { resetForm(); editMode.value = false; isOpen.value = true }
const openEdit = (row: any) => { resetForm(); editMode.value = true; Object.assign(form, row); isOpen.value = true }
const resetForm = () => { Object.assign(form, { id: '', name: '', description: '', type: 'EMAIL', status: 'draft', start_date: '', end_date: '', budget: 0, spent_amount: 0, target_audience: '', goals: '' }) }

const save = async () => {
    if (!form.name) return toast.add({ title: 'Error', description: 'Name required', color: 'red' })
    saving.value = true
    try {
        if (editMode.value) await $api.put(`/crm/campaigns/${form.id}`, form)
        else await $api.post('/crm/campaigns', form)
        toast.add({ title: 'Saved', description: 'Campaign saved.' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const confirmDelete = async (row: any) => {
    if (!confirm(`Delete campaign "${row.name}"?`)) return
    try {
        await $api.delete(`/crm/campaigns/${row.id}`)
        toast.add({ title: 'Deleted', description: 'Campaign deleted.' })
        fetchData()
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' }) }
}

onMounted(() => fetchData())
</script>
