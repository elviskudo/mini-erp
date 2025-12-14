<template>
  <div class="space-y-4">
    <h2 class="text-xl font-semibold text-gray-900">Goods Receipt</h2>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 1. Select PO -->
        <UCard>
            <template #header>1. Select Purchase Order</template>
            <div class="space-y-4">
                <UFormGroup label="Purchase Order (Sent Status)">
                    <USelect v-model="selectedPoId" :options="pendingPos" option-attribute="label" value-attribute="id" placeholder="Select PO..." @change="onPoSelect" />
                </UFormGroup>
                <div v-if="selectedPo" class="text-sm bg-gray-50 p-2 rounded">
                    <p><strong>Vendor:</strong> {{ selectedPo.vendor?.name }}</p>
                    <p><strong>Date:</strong> {{ new Date(selectedPo.created_at).toLocaleDateString() }}</p>
                </div>
            </div>
        </UCard>

        <!-- 2. Select Warehouse -->
        <UCard>
             <template #header>2. Target Warehouse</template>
             <UFormGroup label="Warehouse">
                 <USelect v-model="selectedWarehouseId" :options="warehouses" option-attribute="name" value-attribute="id" placeholder="Select Warehouse..." @change="onWarehouseSelect" />
             </UFormGroup>
             <div v-if="selectedWarehouseId" class="mt-2">
                 <p class="text-xs text-gray-500">Default generic location (Receiving) will be used if specific location not set.</p>
             </div>
        </UCard>
    </div>

    <!-- 3. Receive Items -->
    <UCard v-if="selectedPo && selectedWarehouseId">
        <template #header>3. Receive Items</template>
        
        <div class="space-y-4">
            <div v-for="(item, index) in receiptItems" :key="index" class="border p-4 rounded-lg bg-gray-50">
                 <div class="flex justify-between mb-2">
                    <h4 class="font-bold">{{ item.productName }}</h4>
                    <span class="text-sm text-gray-500">Ordered: {{ item.orderedQty }}</span>
                 </div>
                 
                 <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <UFormGroup label="Receive Qty">
                         <UInput v-model="item.receiveQty" type="number" />
                    </UFormGroup>
                    <UFormGroup label="Batch #">
                         <UInput v-model="item.batchNumber" placeholder="e.g. B-2023-001" />
                    </UFormGroup>
                     <UFormGroup label="Expiry">
                         <UInput v-model="item.expiryDate" type="date" />
                    </UFormGroup>
                     <UFormGroup label="Location">
                         <!-- Select Location from selected Warehouse -->
                         <USelect v-model="item.locationId" :options="availableLocations" option-attribute="name" value-attribute="id" />
                    </UFormGroup>
                 </div>
            </div>

            <div class="flex justify-end">
                <UButton size="lg" :loading="submitting" @click="submitReceipt">Process Receipt</UButton>
            </div>
        </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const loading = ref(false)
const submitting = ref(false)

const pendingPos = ref([])
const warehouses = ref([])
const selectedPoId = ref(null)
const selectedPo = ref(null)
const selectedWarehouseId = ref(null)
const availableLocations = ref([])

const receiptItems = ref([])

const fetchInitialData = async () => {
    // Fetch POs with status SENT (or DRAFT for dev)
    // We need an endpoint for this. backend/routers/procurement.py doesn't have a "list GET" yet?
    // Wait, let's check view_file of procurement.py in previous turn (Step 513).
    // It ONLY has POST create, POST approve, POST create_from_pr.
    // IT DOES NOT HAVE A GET /procurement/po LIST ENDPOINT! 
    // CRITICAL MISSING FEATURE. I cannot list POs to receive if I can't fetch them.
    // I need to add GET /procurement/po endpoint to backend first?
    // Or mock it? The prompt says "requires mocked PO or simple entry".
    // I should probably quickly add the endpoint since I have the tool.
    
    // Also fetch warehouses
    const wRes = await $api.get('/inventory/warehouses')
    warehouses.value = wRes.data
}

// NOTE: Since I missed the list endpoint in backend, I will implement a quick one or assumes it exists.
// I'll add it to the backend in a moment. For now, let's assume it returns a list.
// If I can't add it now, I'll mock the data in frontend.

/*
Mock Data for Pending POs for now until backend updated
*/
// pendingPos.value = [{id: 'uuid', label: 'PO-1001 (Acme Corp)'}] 

// REAL LOGIC (assuming endpoint exists shortly)
const fetchPos = async () => {
    try {
        const res = await $api.get('/procurement/orders') // Need to implement this!
        pendingPos.value = res.data
            .filter(p => p.status === 'Sent' || p.status === 'Draft')
            .map(p => ({
                id: p.id,
                label: `PO-${p.id.substring(0,8)} (${p.vendor?.name || 'Unknown'})`,
                ...p
            }))
    } catch (e) {
        console.error('Failed to fetch POs', e)
    }
}

const onPoSelect = () => {
    selectedPo.value = pendingPos.value.find(p => p.id === selectedPoId.value)
    if (selectedPo.value) {
        // Map items
        receiptItems.value = selectedPo.value.items.map(i => ({
            productId: i.product_id,
            productName: i.product?.name || 'Product', // Need product expand
            orderedQty: i.quantity,
            receiveQty: i.quantity,
            batchNumber: `BATCH-${Date.now()}`,
            expiryDate: '',
            locationId: null
        }))
    }
}

const onWarehouseSelect = () => {
    const wh = warehouses.value.find(w => w.id === selectedWarehouseId.value)
    if (wh) {
        availableLocations.value = wh.locations
        // Auto select first location for items
        if (wh.locations.length > 0) {
            receiptItems.value.forEach(i => i.locationId = wh.locations[0].id)
        }
    }
}

const submitReceipt = async () => {
    if (!confirm('Confirm goods receipt?')) return
    submitting.value = true
    try {
        const payload = {
            po_id: selectedPoId.value,
            warehouse_id: selectedWarehouseId.value,
            items: receiptItems.value.map(i => ({
                product_id: i.productId,
                quantity: Number(i.receiveQty),
                batch_number: i.batchNumber,
                expiration_date: i.expiryDate ? new Date(i.expiryDate).toISOString() : null,
                location_id: i.locationId
            }))
        }
        await $api.post('/receiving/receive', payload)
        alert('Goods Received Successfully!')
        // Reset
        selectedPoId.value = null
        selectedPo.value = null
        receiptItems.value = []
        fetchPos()
    } catch (e) {
        alert('Failed to receive goods')
        console.error(e)
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchInitialData()
    fetchPos()
})
</script>
