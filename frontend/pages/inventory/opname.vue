<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Stock Opname (Stock Take)</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="openCreateModal">New Opname</UButton>
    </div>

    <!-- Opname List -->
    <UCard v-if="!activeOpname">
      <template #header>History</template>
      <UTable :columns="columns" :rows="opnames" :loading="loading">
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
         <template #actions-data="{ row }">
             <UButton size="xs" color="primary" variant="soft" @click="viewOpname(row.id)">View Details</UButton>
        </template>
      </UTable>
    </UCard>

    <!-- Active Opname Detail View -->
    <div v-else class="space-y-4">
        <UCard>
            <div class="flex justify-between items-center mb-4">
                <div>
                     <h3 class="text-lg font-bold">Opname #{{ activeOpname.opname_number }}</h3>
                     <p class="text-gray-500">{{ activeOpname.warehouse?.name }}</p>
                </div>
                <div class="flex gap-2">
                     <UButton color="gray" variant="ghost" @click="activeOpname = null">Back to List</UButton>
                     <UButton v-if="activeOpname.status === 'Draft'" color="green" :loading="posting" @click="postOpname">Finalize & Post</UButton>
                </div>
            </div>

            <UTable :columns="detailColumns" :rows="activeOpname.details">
                 <template #product-data="{ row }">
                    {{ row.product?.name }} ({{ row.batch_number }})
                </template>
                <template #system-data="{ row }">
                    {{ row.system_qty }}
                </template>
                 <template #count-data="{ row }">
                     <div v-if="activeOpname.status === 'Draft'" class="flex items-center gap-2">
                        <UInput v-model="row.counted_qty" type="number" size="xs" class="w-24" @change="updateCount(row)" />
                        <UIcon v-if="savingMatches[row.id]" name="i-heroicons-arrow-path" class="animate-spin text-gray-400" />
                     </div>
                     <span v-else>{{ row.counted_qty }}</span>
                </template>
                <template #diff-data="{ row }">
                    <span :class="{'text-red-600 font-bold': row.counted_qty !== row.system_qty}">
                        {{ Number(row.counted_qty) - Number(row.system_qty) }}
                    </span>
                </template>
            </UTable>
        </UCard>
    </div>

    <!-- Create Modal -->
    <UModal v-model="isOpen">
      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Start Stock Take</h3>
        </template>

        <form @submit.prevent="createOpname" class="space-y-4">
             <UFormGroup label="Warehouse" required>
                 <USelect v-model="form.warehouse_id" :options="warehouses" option-attribute="name" value-attribute="id" />
            </UFormGroup>
            
            <p class="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                This will take a snapshot of current stock in the selected warehouse.
            </p>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Start</UButton>
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
const posting = ref(false)

const opnames = ref([])
const warehouses = ref([])
const activeOpname = ref(null)
const savingMatches = reactive({}) // Track saving status per row

const columns = [
  { key: 'created_at', label: 'Date' },
  { key: 'opname_number', label: 'Number' },
  { key: 'warehouse.name', label: 'Warehouse' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const detailColumns = [
    { key: 'product', label: 'Item' },
    { key: 'location_id', label: 'Loc' }, // Ideally show Name
    { key: 'system', label: 'System Qty' },
    { key: 'count', label: 'Counted Qty' },
    { key: 'diff', label: 'Difference' }
]

const form = reactive({ warehouse_id: '' })

const getStatusColor = (status: string) => {
    return status === 'Draft' ? 'orange' : 'green'
}

const fetchOpnames = async () => {
    loading.value = true
    try {
        const res = await $api.get('/opname/list')
        opnames.value = res.data
        
        const wRes = await $api.get('/inventory/warehouses')
        warehouses.value = wRes.data
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const openCreateModal = () => {
    form.warehouse_id = ''
    isOpen.value = true
}

const createOpname = async () => {
    submitting.value = true
    try {
        const res = await $api.post('/opname/create', { warehouse_id: form.warehouse_id })
        isOpen.value = false
        // Open details immediately
        await viewOpname(res.data.id)
    } catch (e) { alert('Failed') }
    finally { submitting.value = false }
}

const viewOpname = async (id: string) => {
    loading.value = true
    try {
        const res = await $api.get(`/opname/${id}`)
        activeOpname.value = res.data
        // Initialize activeOpname.details needs product expansion from backend
    } catch (e) { alert('Failed to load') }
    finally { loading.value = false }
}

const updateCount = async (row: any) => {
    savingMatches[row.id] = true
    try {
        await $api.post('/opname/update_count', {
            detail_id: row.id,
            counted_qty: Number(row.counted_qty)
        })
    } catch (e) {
        console.error(e)
    } finally {
        savingMatches[row.id] = false
    }
}

const postOpname = async () => {
    if(!confirm('Finalize stock adjustments? This cannot be undone.')) return
    posting.value = true
    try {
        await $api.post('/opname/post', { opname_id: activeOpname.value.id })
        alert('Stock Adjusted!')
        activeOpname.value = null
        fetchOpnames()
    } catch (e) { alert('Failed to post') }
    finally { posting.value = false }
}

onMounted(() => {
    fetchOpnames()
})
</script>
