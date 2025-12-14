<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Fixed Assets</h2>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchAssets">Refresh</UButton>
    </div>

    <UCard>
       <UTable :columns="columns" :rows="assets" :loading="loading">
            <template #status-data="{ row }">
                <UBadge :color="row.status === 'Active' ? 'green' : 'gray'" variant="soft">{{ row.status }}</UBadge>
            </template>
             <template #actions-data="{ row }">
                <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-calculator" @click="handleDepreciate(row.id)">Depreciate</UButton>
            </template>
       </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const loading = ref(false)
const assets = ref([])

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'purchase_date', label: 'Purchased' },
  { key: 'cost', label: 'Cost' },
  { key: 'useful_life_years', label: 'Life (Yrs)' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const fetchAssets = async () => {
    loading.value = true
    try {
        const res = await $api.get('/finance/assets')
        assets.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const handleDepreciate = async (id: string) => {
    try {
        await $api.post(`/finance/assets/${id}/depreciate`)
        toast.add({ title: 'Success', description: 'Depreciation posted successfully.' })
        fetchAssets()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to post depreciation.', color: 'red' })
    }
}

onMounted(() => {
    fetchAssets()
})
</script>
