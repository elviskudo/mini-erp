<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Maintenance & Calibration (CMMS)</h2>
      <UButton icon="i-heroicons-plus" color="black" @click="isOpen = true">New Order</UButton>
    </div>

    <div v-if="loading" class="text-center py-4">Loading orders...</div>
    <UCard v-else>
         <UTable :columns="columns" :rows="orders">
            <template #status-data="{ row }">
                <UBadge :color="getStatusColor(row.status)" variant="soft">{{ row.status }}</UBadge>
            </template>
            <template #type-data="{ row }">
                <UBadge :color="row.type === 'CALIBRATION' ? 'purple' : 'blue'" variant="outline">{{ row.type }}</UBadge>
            </template>
            <template #scheduled_date-data="{ row }">
                {{ new Date(row.scheduled_date).toLocaleDateString() }}
            </template>
             <template #actions-data="{ row }">
                <UButton v-if="row.status !== 'COMPLETED'" size="xs" color="green" variant="ghost" icon="i-heroicons-check" @click="openCompleteModal(row)">Complete</UButton>
            </template>
       </UTable>
    </UCard>

    <!-- Create Order Modal -->
    <UModal v-model="isOpen">
      <div class="p-4">
        <h3 class="text-lg font-bold mb-4">Schedule Maintenance</h3>
        <UForm :state="form" class="space-y-4" @submit="onSubmit">
            <UFormGroup label="Asset" name="asset_id" required>
                 <USelectMenu v-model="form.asset_id" 
                              :options="assets" 
                              option-attribute="name"
                              value-attribute="id"
                              placeholder="Select Asset"
                              searchable />
            </UFormGroup>
             <UFormGroup label="Type" name="type" required>
                <USelect v-model="form.type" :options="['PREVENTIVE', 'CALIBRATION', 'CORRECTIVE']" />
            </UFormGroup>
            <UFormGroup label="Scheduled Date" name="scheduled_date" required>
                 <UInput v-model="form.scheduled_date" type="date" />
            </UFormGroup>
            <UFormGroup label="Description" name="description">
                <UTextarea v-model="form.description" />
            </UFormGroup>
             <UFormGroup label="Technician" name="technician">
                <UInput v-model="form.technician" placeholder="Name or ID" />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" color="black" :loading="saving">Create Order</UButton>
            </div>
        </UForm>
      </div>
    </UModal>

    <!-- Complete Order Modal -->
    <UModal v-model="isCompleteOpen">
        <div class="p-4">
             <h3 class="text-lg font-bold mb-4">Complete Order</h3>
             <UForm :state="completeForm" class="space-y-4" @submit="submitCompletion">
                <UFormGroup label="Notes / Findings" name="notes">
                    <UTextarea v-model="completeForm.notes" />
                </UFormGroup>
                
                <div v-if="selectedOrder?.type === 'CALIBRATION'" class="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm mb-4">
                     <span class="font-bold">Calibration Check:</span> Completing this order will update the Asset status to <span class="text-green-600 font-bold">VALID</span>.
                </div>

                <UFormGroup v-if="selectedOrder?.type === 'CALIBRATION'" label="Next Calibration Date" name="next_calibration_date" required>
                     <UInput v-model="completeForm.next_calibration_date" type="date" />
                </UFormGroup>

                <div class="flex justify-end gap-2 mt-6">
                    <UButton color="gray" variant="ghost" @click="isCompleteOpen = false">Cancel</UButton>
                    <UButton type="submit" color="green" :loading="saving">Complete & Certify</UButton>
                </div>
             </UForm>
        </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const isCompleteOpen = ref(false)
const orders = ref([])
const assets = ref([])
const selectedOrder = ref(null)

const columns = [
  { key: 'scheduled_date', label: 'Date' },
  { key: 'asset_id', label: 'Asset ID' }, // Ideally fetch Name
  { key: 'type', label: 'Type' },
  { key: 'description', label: 'Description' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const form = reactive({
    asset_id: null,
    type: 'PREVENTIVE',
    scheduled_date: '',
    description: '',
    technician: ''
})

const completeForm = reactive({
    notes: '',
    next_calibration_date: ''
})

const fetchOrders = async () => {
    loading.value = true
    try {
        const res = await $api.get('/maintenance/orders')
        orders.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const fetchAssets = async () => {
    try {
        const res = await $api.get('/finance/assets')
        assets.value = res.data
    } catch (e) {
        console.error(e)
    }
}

const onSubmit = async () => {
    saving.value = true
    try {
        await $api.post('/maintenance/orders', form)
        toast.add({ title: 'Success', description: 'Maintenance scheduled.' })
        isOpen.value = false
        fetchOrders()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to create order.' })
    } finally {
        saving.value = false
    }
}

const openCompleteModal = (order) => {
    selectedOrder.value = order
    completeForm.notes = ''
    completeForm.next_calibration_date = ''
    isCompleteOpen.value = true
}

const submitCompletion = async () => {
    if (!selectedOrder.value) return
    saving.value = true
    try {
        await $api.post(`/maintenance/orders/${selectedOrder.value.id}/complete`, completeForm)
        toast.add({ title: 'Success', description: 'Order completed.' })
        isCompleteOpen.value = false
        fetchOrders()
    } catch (e) {
         toast.add({ title: 'Error', description: 'Failed to complete order.' })
    } finally {
        saving.value = false
    }
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'OPEN': return 'gray'
        case 'IN_PROGRESS': return 'orange'
        case 'COMPLETED': return 'green'
        case 'CANCELLED': return 'red'
        default: return 'gray'
    }
}

onMounted(() => {
    fetchOrders()
    fetchAssets()
})
</script>
