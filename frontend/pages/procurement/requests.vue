<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Purchase Requests</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">Create Request</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="prs" :loading="loading">
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
         <template #actions-data="{ row }">
             <div class="flex gap-2">
                 <UButton v-if="row.status === 'Draft'" size="xs" color="green" variant="soft" @click="approvePr(row.id)">Approve</UButton>
                 <UButton v-if="row.status === 'Approved'" size="xs" color="blue" variant="soft" @click="openConvertModal(row)">Convert to PO</UButton>
             </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create PR Modal -->
    <UModal v-model="isCreateOpen" :ui="{ width: 'w-full sm:max-w-3xl' }">
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }">
        <template #header>
          <h3 class="text-base font-semibold leading-6 text-gray-900">New Purchase Request</h3>
        </template>

        <form @submit.prevent="createPr" class="space-y-4">
             <div class="space-y-2 max-h-60 overflow-y-auto">
                <div v-for="(item, index) in form.items" :key="index" class="flex gap-2 items-end bg-gray-50 p-2 rounded">
                        <UFormGroup label="Product" class="flex-1">
                            <USelect v-model="item.product_id" :options="products" option-attribute="name" value-attribute="id" placeholder="Select Product" />
                    </UFormGroup>
                        <UFormGroup label="Qty" class="w-32">
                        <UInput v-model="item.quantity" type="number" step="1" />
                    </UFormGroup>
                    <UButton icon="i-heroicons-trash" color="red" variant="ghost" @click="removeitem(index)" />
                </div>
            </div>
             <UButton size="xs" icon="i-heroicons-plus" variant="soft" @click="addItem">Add Item</UButton>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isCreateOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Submit Request</UButton>
            </div>
        </form>
      </UCard>
    </UModal>

    <!-- Convert to PO Modal -->
    <UModal v-model="isConvertOpen">
        <UCard>
            <template #header>
                <h3 class="font-semibold">Convert PR to PO</h3>
            </template>
            <form @submit.prevent="convertToPo" class="space-y-4">
                 <UFormGroup label="Select Vendor" required>
                    <USelect v-model="convertForm.vendor_id" :options="vendors" option-attribute="name" value-attribute="id" />
                </UFormGroup>
                
                <div v-if="selectedPr" class="border-t pt-2">
                    <p class="text-sm font-medium mb-2">Set Prices</p>
                    <div v-for="item in selectedPr.items" :key="item.id" class="flex justify-between items-center mb-2 text-sm">
                        <span>{{ item.product?.name }} (x{{ item.quantity }})</span>
                        <UInput v-model="convertForm.price_map[item.product_id]" type="number" placeholder="Unit Price" class="w-32" size="sm" />
                    </div>
                </div>

                 <div class="flex justify-end gap-2 mt-4">
                    <UButton color="gray" variant="ghost" @click="isConvertOpen = false">Cancel</UButton>
                    <UButton type="submit" :loading="submitting">Generato PO</UButton>
                </div>
            </form>
        </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const isCreateOpen = ref(false)
const isConvertOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)

const prs = ref([])
const products = ref([])
const vendors = ref([])

const selectedPr = ref(null)

const columns = [
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'id', label: 'ID' },
  { key: 'actions', label: 'Actions' }
]

const form = reactive({
    items: [] as any[]
})

const convertForm = reactive({
    vendor_id: '',
    price_map: {} as Record<string, number>
})

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Draft': return 'gray'
        case 'Approved': return 'blue'
        case 'Converted': return 'green'
        case 'Rejected': return 'red'
        default: return 'primary'
    }
}

const fetchData = async () => {
    loading.value = true
    try {
        const [prRes, prodRes, vendRes] = await Promise.all([
            $api.get('/procurement/pr'),
            $api.get('/manufacturing/products'),
            $api.get('/procurement/vendors')
        ])
        prs.value = prRes.data
        products.value = prodRes.data
        vendors.value = vendRes.data
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const openCreateModal = () => {
    form.items = [{ product_id: '', quantity: 1 }]
    isCreateOpen.value = true
}

const addItem = () => form.items.push({ product_id: '', quantity: 1 })
const removeitem = (idx: number) => form.items.splice(idx, 1)

const createPr = async () => {
    submitting.value = true
    try {
        await $api.post('/procurement/pr', form)
        isCreateOpen.value = false
        fetchData()
    } catch (e) { alert('Failed') }
    finally { submitting.value = false }
}

const approvePr = async (id: string) => {
    if(!confirm('Approve this request?')) return
    try {
        await $api.post(`/procurement/pr/${id}/approve`)
        fetchData()
    } catch (e) { alert('Failed') }
}

const openConvertModal = (pr: any) => {
    selectedPr.value = pr
    convertForm.vendor_id = ''
    convertForm.price_map = {}
    isConvertOpen.value = true
}

const convertToPo = async () => {
    if (!selectedPr.value) return
    submitting.value = true
    try {
        const payload = {
            pr_id: selectedPr.value.id,
            vendor_id: convertForm.vendor_id,
            price_map: convertForm.price_map
        }
        await $api.post('/procurement/po/create_from_pr', payload)
        alert('PO Created!')
        isConvertOpen.value = false
        fetchData()
        navigateTo('/procurement/orders')
    } catch (e) { alert('Failed to convert') }
    finally { submitting.value = false }
}

onMounted(() => {
    fetchData()
})
</script>
