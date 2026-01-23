<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Sales Commission</h1>
        <p class="text-gray-500">Track and manage salesperson commissions</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Record Commission</UButton>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ formatCurrency(stats.pending) }}</div>
          <div class="text-sm text-gray-500">Pending</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-yellow-600">{{ formatCurrency(stats.approved) }}</div>
          <div class="text-sm text-gray-500">Approved</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ formatCurrency(stats.paid) }}</div>
          <div class="text-sm text-gray-500">Paid</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-600">{{ formatCurrency(stats.total) }}</div>
          <div class="text-sm text-gray-500">Total</div>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="items" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #order_amount-data="{ row }">
          {{ formatCurrency(row.order_amount) }}
        </template>
        <template #rate-data="{ row }">
          {{ row.rate }}%
        </template>
        <template #amount-data="{ row }">
          <span class="font-semibold text-green-600">{{ formatCurrency(row.amount) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UDropdown :items="getActions(row)">
            <UButton icon="i-heroicons-ellipsis-vertical" color="gray" variant="ghost" size="xs" />
          </UDropdown>
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" title="Record Commission" :loading="saving" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Salesperson" required>
          <USelectMenu v-model="form.salesperson_id" :options="userOptions" value-attribute="value" option-attribute="label" searchable placeholder="Select Salesperson" />
        </UFormGroup>
        <UFormGroup label="Related Order">
          <USelectMenu v-model="form.order_id" :options="orderOptions" value-attribute="value" option-attribute="label" searchable placeholder="Select Order" @change="onOrderSelect" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Order Amount">
            <UInput v-model.number="form.order_amount" type="number" />
          </UFormGroup>
          <UFormGroup label="Commission Rate (%)">
            <UInput v-model.number="form.rate" type="number" step="0.1" />
          </UFormGroup>
        </div>
        <UFormGroup label="Commission Amount">
          <UInput v-model.number="form.amount" type="number" class="font-bold" />
        </UFormGroup>
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="2" />
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

const items = ref([])
const users = ref<any[]>([])
const orders = ref<any[]>([])
const pagination = ref(null)
const currentPage = ref(1)

const stats = computed(() => {
    const pending = items.value.filter((i: any) => i.status === 'pending').reduce((s: number, i: any) => s + (i.amount || 0), 0)
    const approved = items.value.filter((i: any) => i.status === 'approved').reduce((s: number, i: any) => s + (i.amount || 0), 0)
    const paid = items.value.filter((i: any) => i.status === 'paid').reduce((s: number, i: any) => s + (i.amount || 0), 0)
    return { pending, approved, paid, total: pending + approved + paid }
})

const columns = [
    { key: 'salesperson_id', label: 'Salesperson' },
    { key: 'order_amount', label: 'Order Amount' },
    { key: 'rate', label: 'Rate' },
    { key: 'amount', label: 'Commission' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const userOptions = computed(() => users.value.map(u => ({ label: u.name || u.email, value: u.id })))
const orderOptions = computed(() => orders.value.map(o => ({ label: o.order_number || o.id, value: o.id, raw: o })))
const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const getStatusColor = (status: string) => ({ pending: 'yellow', approved: 'blue', paid: 'green', cancelled: 'red' }[status] || 'gray')

const getActions = (row: any) => [[
    { label: 'Approve', icon: 'i-heroicons-check', click: () => updateStatus(row.id, 'approved'), disabled: row.status !== 'pending' },
    { label: 'Mark Paid', icon: 'i-heroicons-banknotes', click: () => updateStatus(row.id, 'paid'), disabled: row.status !== 'approved' },
    { label: 'Cancel', icon: 'i-heroicons-x-mark', click: () => updateStatus(row.id, 'cancelled') }
]]

const form = reactive({ salesperson_id: '', order_id: '', invoice_id: '', order_amount: 0, rate: 5, amount: 0, notes: '' })

const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/sales/commission', { params: { page: currentPage.value } })
        items.value = res.data?.data || []
        pagination.value = res.data?.meta?.pagination
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
    loadAuxData()
}

const loadAuxData = async () => {
    try {
        const [uRes, oRes] = await Promise.all([
            $api.get('/auth/users', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } })),
            $api.get('/sales/orders', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } }))
        ])
        users.value = uRes.data?.data || []
        orders.value = oRes.data?.data || []
    } catch(e) {}
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const openCreate = () => { resetForm(); isOpen.value = true }
const resetForm = () => { Object.assign(form, { salesperson_id: '', order_id: '', invoice_id: '', order_amount: 0, rate: 5, amount: 0, notes: '' }) }

const onOrderSelect = (val: any) => {
    const order = orderOptions.value.find(o => o.value === val)
    if (order?.raw) {
        form.order_amount = order.raw.total_amount || 0
        form.amount = form.order_amount * form.rate / 100
    }
}

watch(() => [form.order_amount, form.rate], () => {
    form.amount = form.order_amount * form.rate / 100
})

const save = async () => {
    if (!form.salesperson_id) return toast.add({ title: 'Error', description: 'Salesperson required', color: 'red' })
    saving.value = true
    try {
        await $api.post('/sales/commission', form)
        toast.add({ title: 'Saved', description: 'Commission recorded.' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const updateStatus = async (id: string, status: string) => {
    try {
        await $api.put(`/sales/commission/${id}/status`, { status })
        toast.add({ title: 'Updated', description: `Status updated to ${status}` })
        fetchData()
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to update', color: 'red' }) }
}

onMounted(() => fetchData())
</script>
