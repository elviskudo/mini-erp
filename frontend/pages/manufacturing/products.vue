<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Products & BOM</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">Create Product</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="products" :loading="loading">
         <template #type-data="{ row }">
            <UBadge :color="getTypeColor(row.type)" variant="subtle">{{ row.type }}</UBadge>
        </template>
      </UTable>
    </UCard>

    <!-- Create/Edit Modal -->
    <UModal v-model="isOpen" :ui="{ width: 'w-full sm:max-w-4xl' }"> <!-- Wide modal for BOM -->
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }">
        <template #header>
          <h3 class="text-base font-semibold leading-6 text-gray-900">
            Create Product
          </h3>
        </template>

        <form @submit.prevent="saveProduct" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <UFormGroup label="Name" name="name" required>
                    <UInput v-model="form.name" placeholder="Product Name" />
                </UFormGroup>
                
                <UFormGroup label="SKU" name="sku" required>
                    <UInput v-model="form.sku" placeholder="SKU-000" />
                </UFormGroup>
            </div>

            <div class="grid grid-cols-2 gap-4">
                 <UFormGroup label="Type" name="type" required>
                     <USelect v-model="form.type" :options="['Raw Material', 'Work in Progress', 'Finished Good']" />
                </UFormGroup>
                 <UFormGroup label="Unit" name="unit">
                    <UInput v-model="form.unit_of_measure" placeholder="e.g. PCS, KG" />
                </UFormGroup>
            </div>

            <!-- BOM Section (Only for Manufactured items) -->
            <div v-if="form.type !== 'Raw Material'" class="border-t border-gray-200 pt-4">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-gray-900">Bill of Materials</h4>
                    <UButton size="xs" icon="i-heroicons-plus" variant="soft" @click="addBomItem">Add Component</UButton>
                </div>
                
                <div v-if="form.bom_items.length === 0" class="text-sm text-gray-500 italic pb-2">
                    No components added.
                </div>

                <div v-else class="space-y-2 max-h-60 overflow-y-auto">
                    <div v-for="(item, index) in form.bom_items" :key="index" class="flex gap-2 items-end bg-gray-50 p-2 rounded">
                         <UFormGroup label="Component" class="flex-1">
                             <USelect v-model="item.component_id" :options="rawMaterials" option-attribute="name" value-attribute="id" placeholder="Select Material" />
                        </UFormGroup>
                         <UFormGroup label="Qty" class="w-24">
                            <UInput v-model="item.quantity" type="number" step="0.001" />
                        </UFormGroup>
                         <UFormGroup label="Waste %" class="w-24">
                            <UInput v-model="item.waste_percentage" type="number" step="0.1" />
                        </UFormGroup>
                        <UButton icon="i-heroicons-trash" color="red" variant="ghost" @click="removeBomItem(index)" />
                    </div>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Save Product</UButton>
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
const products = ref([])
const rawMaterials = ref([]) // For BOM dropdown

const columns = [
  { key: 'sku', label: 'SKU' },
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Type' },
  { key: 'unit_of_measure', label: 'Unit' },
]

const form = reactive({
    name: '',
    sku: '',
    type: 'Raw Material',
    unit_of_measure: 'PCS',
    bom_items: [] as any[]
})

const getTypeColor = (type: string) => {
    switch(type) {
        case 'Raw Material': return 'gray'
        case 'Work in Progress': return 'orange'
        case 'Finished Good': return 'green'
        default: return 'primary'
    }
}

const fetchProducts = async () => {
    loading.value = true
    try {
        const res = await $api.get('/manufacturing/products')
        products.value = res.data
        // Filter for raw materials for BOM
        rawMaterials.value = products.value.filter((p: any) => p.type === 'Raw Material' || p.type === 'Work in Progress')
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const openCreateModal = () => {
    // Reset form
    form.name = ''
    form.sku = ''
    form.type = 'Raw Material'
    form.unit_of_measure = 'PCS'
    form.bom_items = []
    isOpen.value = true
}

const addBomItem = () => {
    form.bom_items.push({
        component_id: '',
        quantity: 1,
        waste_percentage: 0
    })
}

const removeBomItem = (index: number) => {
    form.bom_items.splice(index, 1)
}

const saveProduct = async () => {
    submitting.value = true
    try {
        // 1. Create Product
        const productPayload = {
            name: form.name,
            sku: form.sku,
            type: form.type,
            unit_of_measure: form.unit_of_measure,
            description: ''
        }
        const prodRes = await $api.post('/manufacturing/products', productPayload)
        
        // 2. Create BOM if needed
        if (form.type !== 'Raw Material' && form.bom_items.length > 0) {
            const bomPayload = {
                product_id: prodRes.data.id,
                reference: `BOM-${form.sku}`,
                items: form.bom_items.map(i => ({
                    component_id: i.component_id,
                    quantity: Number(i.quantity),
                    waste_percentage: Number(i.waste_percentage)
                }))
            }
             await $api.post('/manufacturing/boms', bomPayload)
        }

        isOpen.value = false
        fetchProducts()
    } catch (e) {
        console.error(e)
        alert('Failed to save product')
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchProducts()
})
</script>
