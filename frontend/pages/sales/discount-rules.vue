<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Discount Rules</h1>
        <p class="text-gray-500">Configure automatic discount rules</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Rule</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="items" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #type-data="{ row }">
          <UBadge :color="row.type === 'PERCENTAGE' ? 'blue' : 'green'" variant="subtle">{{ row.type }}</UBadge>
        </template>
        <template #value-data="{ row }">
          {{ row.type === 'PERCENTAGE' ? row.value + '%' : formatCurrency(row.value) }}
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Rule' : 'New Rule'" :loading="saving" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Name" required>
          <UInput v-model="form.name" placeholder="Weekend Sale 20%" />
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="form.description" rows="2" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Type" required>
            <USelectMenu v-model="form.type" :options="['PERCENTAGE', 'FIXED_AMOUNT', 'BUY_X_GET_Y']" />
          </UFormGroup>
          <UFormGroup label="Value" required>
            <UInput v-model.number="form.value" type="number" :placeholder="form.type === 'PERCENTAGE' ? '20' : '50000'" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Min Quantity">
            <UInput v-model.number="form.min_quantity" type="number" placeholder="e.g. 10" />
          </UFormGroup>
          <UFormGroup label="Min Amount">
            <UInput v-model.number="form.min_amount" type="number" placeholder="e.g. 100000" />
          </UFormGroup>
        </div>
        <UFormGroup label="Max Discount (Cap)">
          <UInput v-model.number="form.max_discount" type="number" placeholder="e.g. 500000" />
        </UFormGroup>
        <UFormGroup label="Applies To">
          <USelectMenu v-model="form.applies_to" :options="['ALL', 'PRODUCT', 'CATEGORY', 'CUSTOMER']" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Valid From">
            <UInput type="date" v-model="form.valid_from" />
          </UFormGroup>
          <UFormGroup label="Valid To">
            <UInput type="date" v-model="form.valid_to" />
          </UFormGroup>
        </div>
        <UFormGroup label="Promo Code (Optional)">
          <UInput v-model="form.promo_code" placeholder="SALE20" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Priority">
            <UInput v-model.number="form.priority" type="number" placeholder="0" />
          </UFormGroup>
          <UFormGroup label="Usage Limit">
            <UInput v-model.number="form.usage_limit" type="number" placeholder="Unlimited" />
          </UFormGroup>
        </div>
        <UCheckbox v-model="form.is_active" label="Active" />
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

const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'type', label: 'Type' },
    { key: 'value', label: 'Value' },
    { key: 'applies_to', label: 'Applies To' },
    { key: 'priority', label: 'Priority' },
    { key: 'is_active', label: 'Status' },
    { key: 'actions', label: '' }
]

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)

const form = reactive({
    id: '', name: '', description: '', type: 'PERCENTAGE', value: 0,
    min_quantity: null as number | null, min_amount: null as number | null, max_discount: null as number | null,
    applies_to: 'ALL', product_id: '', category_id: '', customer_id: '',
    valid_from: '', valid_to: '', promo_code: '', priority: 0, usage_limit: null as number | null, is_active: true
})

const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/sales/discount-rules', { params: { page: currentPage.value } })
        items.value = res.data?.data || []
        pagination.value = res.data?.meta?.pagination
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }

const openCreate = () => { resetForm(); editMode.value = false; isOpen.value = true }
const openEdit = (row: any) => { resetForm(); editMode.value = true; Object.assign(form, row); isOpen.value = true }
const resetForm = () => { Object.assign(form, { id: '', name: '', description: '', type: 'PERCENTAGE', value: 0, min_quantity: null, min_amount: null, max_discount: null, applies_to: 'ALL', product_id: '', category_id: '', customer_id: '', valid_from: '', valid_to: '', promo_code: '', priority: 0, usage_limit: null, is_active: true }) }

const save = async () => {
    if (!form.name || !form.type) return toast.add({ title: 'Error', description: 'Name and type required', color: 'red' })
    saving.value = true
    try {
        if (editMode.value) await $api.put(`/sales/discount-rules/${form.id}`, form)
        else await $api.post('/sales/discount-rules', form)
        toast.add({ title: 'Saved', description: 'Discount rule saved.' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

onMounted(() => fetchData())
</script>
