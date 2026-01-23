<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Price Lists</h1>
        <p class="text-gray-500">Manage product pricing for different customers</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Price List</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable
        :columns="columns"
        :data="items"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
      >
        <template #is_default-data="{ row }">
          <UBadge v-if="row.is_default" color="yellow" variant="subtle">Default</UBadge>
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Price List' : 'New Price List'" :loading="saving" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Name" required>
          <UInput v-model="form.name" placeholder="Retail Price List" />
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="form.description" rows="2" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Valid From">
            <UInput type="date" v-model="form.valid_from" />
          </UFormGroup>
          <UFormGroup label="Valid To">
            <UInput type="date" v-model="form.valid_to" />
          </UFormGroup>
        </div>
        <UFormGroup label="Customer (Optional)">
          <USelectMenu v-model="form.customer_id" :options="customerOptions" value-attribute="value" option-attribute="label" searchable placeholder="All Customers" />
        </UFormGroup>
        <div class="flex gap-6">
          <UCheckbox v-model="form.is_default" label="Default Price List" />
          <UCheckbox v-model="form.is_active" label="Active" />
        </div>

        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium text-sm">Price Items</h4>
            <UButton size="xs" variant="ghost" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center">
            <USelectMenu v-model="item.product_id" :options="productOptions" value-attribute="value" option-attribute="label" searchable placeholder="Product" class="flex-[3]" size="sm" />
            <UInput v-model.number="item.min_quantity" type="number" placeholder="Min Qty" class="w-20" size="sm" />
            <UInput v-model.number="item.price" type="number" placeholder="Price" class="w-28" size="sm" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="form.items.splice(idx, 1)" />
          </div>
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
const products = ref<any[]>([])
const pagination = ref(null)
const currentPage = ref(1)

const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'currency', label: 'Currency' },
    { key: 'valid_from', label: 'Valid From' },
    { key: 'valid_to', label: 'Valid To' },
    { key: 'is_default', label: '' },
    { key: 'is_active', label: 'Status' },
    { key: 'actions', label: '' }
]

const customerOptions = computed(() => [{ label: 'All Customers', value: '' }, ...customers.value.map(c => ({ label: c.name, value: c.id }))])
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code || ''} - ${p.name}`, value: p.id })))

const form = reactive({
    id: '', name: '', description: '', currency: 'IDR', valid_from: '', valid_to: '',
    customer_id: '', is_default: false, is_active: true,
    items: [] as { product_id: string; min_quantity: number; price: number }[]
})

const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/sales/price-lists', { params: { page: currentPage.value } })
        items.value = res.data?.data || []
        pagination.value = res.data?.meta?.pagination
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
    loadAuxData()
}

const loadAuxData = async () => {
    try {
        const [cRes, pRes] = await Promise.all([
            $api.get('/crm/customers', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } })),
            $api.get('/inventory/products', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } }))
        ])
        customers.value = cRes.data?.data || []
        products.value = pRes.data?.data || []
    } catch(e) {}
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }

const openCreate = () => { resetForm(); editMode.value = false; isOpen.value = true }
const openEdit = (row: any) => { resetForm(); editMode.value = true; Object.assign(form, { ...row, items: row.items || [] }); isOpen.value = true }
const resetForm = () => { Object.assign(form, { id: '', name: '', description: '', currency: 'IDR', valid_from: '', valid_to: '', customer_id: '', is_default: false, is_active: true, items: [] }) }
const addItem = () => { form.items.push({ product_id: '', min_quantity: 1, price: 0 }) }

const save = async () => {
    if (!form.name) return toast.add({ title: 'Error', description: 'Name required', color: 'red' })
    saving.value = true
    try {
        if (editMode.value) await $api.put(`/sales/price-lists/${form.id}`, form)
        else await $api.post('/sales/price-lists', form)
        toast.add({ title: 'Saved', description: 'Price list saved.' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

onMounted(() => fetchData())
</script>
