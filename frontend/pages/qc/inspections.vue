<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Quality Inspections</h2>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchInspections">Refresh</UButton>
    </div>

    <!-- For demo, adding a button to manually trigger a dummy inspection if list is empty 
         Normally this comes from GR or Production -->
    <div v-if="inspections.length === 0 && !loading" class="text-center p-4">
        <p class="text-gray-500 mb-2">No pending inspections.</p>
        <UButton size="xs" variant="soft" @click="createDummyInspection">Create Mock Inspection</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="inspections" :loading="loading">
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #product-data="{ row }">
            {{ row.product?.name || 'Unknown' }} ({{ row.batch_number }})
        </template>
        <template #actions-data="{ row }">
             <UButton v-if="row.status === 'Pending'" size="xs" color="blue" variant="soft" @click="openInspectModal(row)">Inspect</UButton>
        </template>
      </UTable>
    </UCard>

    <!-- Inspect Modal -->
    <UModal v-model="isOpen">
      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Perform Inspection</h3>
          <p class="text-sm text-gray-500">{{ selectedInspection?.product?.name }} - {{ selectedInspection?.batch_number }}</p>
        </template>

        <form @submit.prevent="submitInspection" class="space-y-4">
             <UFormGroup label="Result">
                <div class="flex gap-4">
                    <URadio v-model="form.status" value="Pass" label="Pass" />
                    <URadio v-model="form.status" value="Fail" label="Fail" />
                </div>
            </UFormGroup>
            
            <UFormGroup label="Measured Values (JSON)">
                <UTextarea v-model="form.notes" placeholder='{"ph": 7.0, "viscosity": 100}' />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Submit Result</UButton>
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
const inspections = ref([])
const selectedInspection = ref(null)

const columns = [
  { key: 'created_at', label: 'Date' },
  { key: 'product', label: 'Item' },
  { key: 'quantity', label: 'Qty' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const form = reactive({
    status: 'Pass',
    notes: ''
})

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Pending': return 'orange'
        case 'Pass': return 'green'
        case 'Fail': return 'red'
        default: return 'gray'
    }
}

const fetchInspections = async () => {
    loading.value = true
    try {
        const res = await $api.get('/qc/inspections')
        inspections.value = res.data
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const createDummyInspection = async () => {
    // Helper to create data if empty
    try {
         // Need a product ID. Fetch first product.
         const pRes = await $api.get('/manufacturing/products')
         if(pRes.data.length > 0) {
             await $api.post('/qc/trigger', {
                 product_id: pRes.data[0].id,
                 quantity: 100,
                 batch_number: 'BATCH-TEST-QC',
                 reference_id: 'MANUAL',
                 source: 'Manual'
             })
             fetchInspections()
         } else {
             alert('Create a product first')
         }
    } catch (e) { alert('Failed') }
}

const openInspectModal = (row: any) => {
    selectedInspection.value = row
    form.status = 'Pass'
    form.notes = ''
    isOpen.value = true
}

const submitInspection = async () => {
    if (!selectedInspection.value) return
    submitting.value = true
    try {
        const payload = {
            inspection_id: selectedInspection.value.id,
            result: form.status,
            notes: form.notes
        }
        await $api.post('/qc/inspect', payload)
        isOpen.value = false
        fetchInspections()
    } catch (e) { alert('Failed') }
    finally { submitting.value = false }
}

onMounted(() => {
    fetchInspections()
})
</script>
