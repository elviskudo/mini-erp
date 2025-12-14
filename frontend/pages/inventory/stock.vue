<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Stock Status</h2>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchStock">Refresh</UButton>
    </div>

    <UCard>
      <!-- Need an endpoint to get all batches or aggregated stock. 
           Task 2.5 has /issuance/available_batches/{product_id}, but we want ALL.
           I'll assume I need to add a general stock list endpoint to Inventory Router.
           GET /inventory/stock
      -->
      <UTable :columns="columns" :rows="stockItems" :loading="loading">
         <template #expiry-data="{ row }">
            <span :class="{'text-red-500 font-bold': isExpired(row.expiration_date)}">
                {{ row.expiration_date ? new Date(row.expiration_date).toLocaleDateString() : 'N/A' }}
            </span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const loading = ref(false)
const stockItems = ref([])

const columns = [
  { key: 'product.name', label: 'Product' },
  { key: 'batch_number', label: 'Batch' },
  { key: 'quantity_on_hand', label: 'Qty' },
  { key: 'location.name', label: 'Location' },
  { key: 'expiry', label: 'Expires' }
]

const fetchStock = async () => {
    loading.value = true
    try {
        // I will add this endpoint to inventory router next
        const res = await $api.get('/inventory/stock')
        stockItems.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const isExpired = (dateString: string) => {
    if (!dateString) return false
    return new Date(dateString) < new Date()
}

onMounted(() => {
    fetchStock()
})
</script>
