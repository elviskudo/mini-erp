<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Purchase Orders</h2>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchPos">Refresh</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="orders" :loading="loading">
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #vendor-data="{ row }">
            {{ row.vendor?.name || 'Unknown' }}
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const loading = ref(false)
const orders = ref([])

const columns = [
  { key: 'created_at', label: 'Date' },
  { key: 'id', label: 'PO Number' },
  { key: 'vendor', label: 'Vendor' },
  { key: 'status', label: 'Status' }
]

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Draft': return 'gray'
        case 'Sent': return 'blue'
        case 'Completed': return 'green'
        default: return 'primary'
    }
}

const fetchPos = async () => {
    loading.value = true
    try {
        const res = await $api.get('/procurement/orders')
        orders.value = res.data
    } catch (e) {
        console.error(e)
        // If error (e.g. endpoint mock issue), set empty
        orders.value = []
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchPos()
})
</script>
