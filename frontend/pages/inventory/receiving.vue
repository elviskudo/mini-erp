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
                <UButton size="lg" color="primary" icon="i-heroicons-check-circle" @click="openReceiptModal">Process Receipt</UButton>
            </div>
        </div>
    </UCard>

    <!-- Process Receipt Confirmation Modal -->
    <UModal v-model="showReceiptModal">
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-inbox-arrow-down" class="text-green-500" />
            <h3 class="text-lg font-semibold">Confirm Goods Receipt</h3>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="bg-green-50 border border-green-200 rounded-lg p-4">
            <p class="text-sm text-gray-600">You're about to receive goods for:</p>
            <p class="font-bold text-lg">{{ selectedPo?.po_number || selectedPo?.label }}</p>
            <p class="text-sm text-gray-500">{{ selectedPo?.vendor?.name || 'Vendor' }}</p>
            <p class="text-sm mt-2">Items: {{ receiptItems.length }} product(s)</p>
          </div>
          
          <UFormGroup label="Notes" hint="Optional notes for this receipt">
            <UTextarea v-model="receiptNotes" rows="3" placeholder="Add any notes about this receipt (condition, remarks, etc.)" />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showReceiptModal = false">Cancel</UButton>
            <UButton color="green" icon="i-heroicons-check-circle" :loading="submitting" @click="confirmReceipt">
              Confirm Receipt
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const loading = ref(false)
const submitting = ref(false)

const pendingPos = ref([])
const warehouses = ref([])
const selectedPoId = ref(null)
const selectedPo = ref(null)
const selectedWarehouseId = ref(null)
const availableLocations = ref([])

const receiptItems = ref([])
const showReceiptModal = ref(false)
const receiptNotes = ref('')

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
            .filter(p => p.status === 'OPEN' || p.status === 'PARTIAL_RECEIVE')
            .map(p => ({
                id: p.id,
                label: `${p.po_number || 'PO-' + p.id.substring(0,8)} - ${p.vendor?.name || 'Unknown Vendor'}`,
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

const openReceiptModal = () => {
    if (receiptItems.value.length === 0) {
        toast.add({ title: 'Error', description: 'No items to receive', color: 'red' })
        return
    }
    receiptNotes.value = ''
    showReceiptModal.value = true
}

const confirmReceipt = async () => {
    submitting.value = true
    try {
        const payload = {
            po_id: selectedPoId.value,
            warehouse_id: selectedWarehouseId.value,
            notes: receiptNotes.value,
            items: receiptItems.value.map(i => ({
                product_id: i.productId,
                quantity: Number(i.receiveQty),
                batch_number: i.batchNumber,
                expiration_date: i.expiryDate ? new Date(i.expiryDate).toISOString() : null,
                location_id: i.locationId
            }))
        }
        const response = await $api.post('/receiving/receive', payload)
        const result = response.data
        
        // Show success toast with progress info
        const progressMsg = result.progress ? `Progress: ${result.progress.toFixed(1)}%` : ''
        const statusMsg = result.status ? `Status: ${result.status}` : ''
        toast.add({ 
            title: '✅ Goods Received Successfully!', 
            description: `${result.batches_created} batch(es) created. ${progressMsg} ${statusMsg}`.trim(), 
            color: 'green',
            timeout: 5000
        })
        
        showReceiptModal.value = false
        // Reset
        selectedPoId.value = null
        selectedPo.value = null
        receiptItems.value = []
        receiptNotes.value = ''
        fetchPos()
    } catch (e: any) {
        toast.add({ title: 'Error', description: 'Failed to receive goods', color: 'red' })
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
