<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Sales Contracts</h1>
        <p class="text-gray-500">Manage long-term sales contracts</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Contract</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="items" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #customer_id-data="{ row }">
          <div v-if="getCustomer(row.customer_id)">
            <div class="font-medium text-gray-900">{{ getCustomer(row.customer_id).name }}</div>
            <div class="text-xs text-gray-500">{{ getCustomer(row.customer_id).email }}</div>
            <div class="text-xs text-gray-500">{{ getCustomer(row.customer_id).phone }}</div>
          </div>
          <span v-else class="text-gray-400">Unknown Customer</span>
        </template>
        <template #total_value-data="{ row }">
          {{ formatCurrency(row.total_value) }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Contract' : 'New Contract'" :loading="saving" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Contract Number" required>
          <UInput v-model="form.contract_number" placeholder="CTR-2026-001" />
        </UFormGroup>
        <UFormGroup label="Customer" required>
          <USelectMenu v-model="form.customer_id" :options="customerOptions" value-attribute="value" option-attribute="label" searchable placeholder="Select Customer" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Start Date" required>
            <UInput type="date" v-model="form.start_date" />
          </UFormGroup>
          <UFormGroup label="End Date">
            <UInput type="date" v-model="form.end_date" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Total Value">
            <UInput v-model.number="form.total_value" type="number" placeholder="0" />
          </UFormGroup>
          <UFormGroup label="Status">
            <USelectMenu v-model="form.status" :options="['draft', 'active', 'expired', 'cancelled']" />
          </UFormGroup>
        </div>
        <UFormGroup label="Payment Terms">
          <UInput v-model="form.payment_terms" placeholder="Net 30" />
        </UFormGroup>
        <UFormGroup label="Terms & Conditions">
          <UTextarea v-model="form.terms" rows="3" />
        </UFormGroup>
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="2" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Renewal Date">
            <UInput type="date" v-model="form.renewal_date" />
          </UFormGroup>
          <UFormGroup>
            <UCheckbox v-model="form.auto_renew" label="Auto Renew" class="mt-6" />
          </UFormGroup>
        </div>
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
const customers = ref<any[]>([])
const pagination = ref(null)
const currentPage = ref(1)

const columns = [
    { key: 'contract_number', label: 'Contract #', sortable: true },
    { key: 'customer_id', label: 'Customer' },
    { key: 'start_date', label: 'Start' },
    { key: 'end_date', label: 'End' },
    { key: 'total_value', label: 'Value' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const customerOptions = computed(() => customers.value.map(c => ({ label: c.name, value: c.id })))
const getCustomer = (id: string) => customers.value.find(c => c.id === id)
const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const getStatusColor = (status: string) => ({ draft: 'gray', active: 'green', expired: 'orange', cancelled: 'red' }[status] || 'gray')

const form = reactive({
    id: '', contract_number: '', customer_id: '', start_date: '', end_date: '',
    status: 'draft', total_value: 0, payment_terms: '', terms: '', notes: '',
    renewal_date: '', auto_renew: false
})

const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/sales/contracts', { params: { page: currentPage.value } })
        items.value = res.data?.data || []
        pagination.value = res.data?.meta?.pagination
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
    loadCustomers()
}

const loadCustomers = async () => {
    try { customers.value = (await $api.get('/crm/customers', { params: { limit: 100 } })).data?.data || [] } catch(e) {}
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const openCreate = () => { resetForm(); form.contract_number = 'CTR-' + new Date().toISOString().slice(2,10).replace(/-/g, '') + '-' + Math.floor(Math.random() * 1000); editMode.value = false; isOpen.value = true }
const openEdit = (row: any) => { resetForm(); editMode.value = true; Object.assign(form, row); isOpen.value = true }
const resetForm = () => { Object.assign(form, { id: '', contract_number: '', customer_id: '', start_date: '', end_date: '', status: 'draft', total_value: 0, payment_terms: '', terms: '', notes: '', renewal_date: '', auto_renew: false }) }

const save = async () => {
    if (!form.contract_number || !form.customer_id || !form.start_date) return toast.add({ title: 'Error', description: 'Contract #, Customer, Start Date required', color: 'red' })
    saving.value = true
    try {
        if (editMode.value) await $api.put(`/sales/contracts/${form.id}`, form)
        else await $api.post('/sales/contracts', form)
        toast.add({ title: 'Saved', description: 'Contract saved.' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

onMounted(() => fetchData())
</script>
