<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Delivery Orders (Logistics)</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">Create DO</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="orders" :loading="loading">
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
         <template #items-data="{ row }">
            {{ row.items?.length || 0 }} items
        </template>
        <template #actions-data="{ row }">
             <UButton v-if="row.status === 'Draft'" size="xs" color="blue" variant="soft" :loading="shippingId === row.id" @click="shipOrder(row.id)">Ship Order</UButton>
        </template>
      </UTable>
    </UCard>

    <!-- Create DO Modal -->
    <UModal v-model="isOpen" :ui="{ width: 'w-full sm:max-w-2xl' }">
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }">
        <template #header>
          <h3 class="text-base font-semibold leading-6 text-gray-900">New Delivery Order</h3>
        </template>

        <form @submit.prevent="createDo" class="space-y-4">
             <UFormGroup label="Sales Order Reference" name="so_id" required hint="Link to original sales order" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="form.so_id" placeholder="e.g. SO-1001" />
            </UFormGroup>

            <div class="border-t pt-2">
                <div class="flex justify-between mb-2">
                    <span class="font-medium">Items to Ship</span>
                    <UButton size="xs" icon="i-heroicons-plus" variant="soft" @click="addItem">Add Item</UButton>
                </div>
                
                 <div class="space-y-2 max-h-60 overflow-y-auto">
                    <div v-for="(item, index) in form.items" :key="index" class="p-2 border rounded bg-gray-50 space-y-2">
                        <div class="flex gap-2">
                             <UFormGroup label="Product" required hint="Select product" :ui="{ hint: 'text-xs text-gray-400' }" class="flex-1">
                                <USelect v-model="item.product_id" :options="products" option-attribute="name" value-attribute="id" placeholder="Select Product" />
                            </UFormGroup>
                            <UFormGroup label="Qty" required hint="Quantity" :ui="{ hint: 'text-xs text-gray-400' }" class="w-24">
                                <UInput v-model="item.quantity" type="number" step="1" min="1" />
                            </UFormGroup>
                             <UButton icon="i-heroicons-trash" color="red" variant="ghost" class="mt-6" @click="removeItem(index)" />
                        </div>
                         <UFormGroup label="Batch to Pick From" required hint="Select stock batch" :ui="{ hint: 'text-xs text-gray-400' }">
                             <USelect v-model="item.batch_id" :options="getBatchesForProduct(item.product_id)" option-attribute="label" value-attribute="id" placeholder="Select Batch..." />
                        </UFormGroup>
                    </div>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting" :disabled="!form.so_id || form.items.length === 0">Create DO</UButton>
            </div>
        </form>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const shippingId = ref<string | null>(null)

const orders = ref([])
const products = ref([])
const stock = ref([]) // To map batches

const columns = [
  { key: 'so_id', label: 'SO Ref' },
  { key: 'status', label: 'Status' },
  { key: 'items', label: 'Items' },
  { key: 'actions', label: 'Actions' }
]

const form = reactive({
    so_id: '',
    items: [] as any[]
})

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Draft': return 'gray'
        case 'Shipped': return 'green'
        default: return 'primary'
    }
}

const fetchData = async () => {
    loading.value = true
    try {
        const [doRes, prodRes, stockRes] = await Promise.all([
            $api.get('/delivery/orders'),
            $api.get('/manufacturing/products'),
            $api.get('/inventory/stock')
        ])
        orders.value = doRes.data
        products.value = prodRes.data
        stock.value = stockRes.data
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

// Filter batches for dropdown
const getBatchesForProduct = (productId: string) => {
    if (!productId) return []
    return stock.value
        .filter((b: any) => b.product_id === productId)
        .map((b: any) => ({
            id: b.id,
            label: `${b.batch_number} (Qty: ${b.quantity_on_hand})`
        }))
}

const openCreateModal = () => {
    form.so_id = ''
    form.items = [{ product_id: '', quantity: 1, batch_id: '' }]
    isOpen.value = true
}

const addItem = () => form.items.push({ product_id: '', quantity: 1, batch_id: '' })
const removeItem = (idx: number) => form.items.splice(idx, 1)

const createDo = async () => {
    submitting.value = true
    try {
        await $api.post('/delivery/create', form)
        isOpen.value = false
        fetchData()
    } catch (e) { alert('Failed') }
    finally { submitting.value = false }
}

const shipOrder = async (id: string) => {
    if(!confirm('Ship this order? Stock will be deducted.')) return
    shippingId.value = id
    try {
        await $api.post(`/delivery/${id}/ship`)
        fetchData()
    } catch (e) { alert('Failed to ship (Check stock availability)') }
    finally { shippingId.value = null }
}

onMounted(() => {
    fetchData()
})
</script>
