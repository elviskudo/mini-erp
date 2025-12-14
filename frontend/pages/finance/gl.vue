<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">General Ledger</h2>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchEntries">Refresh</UButton>
    </div>

    <div v-if="loading" class="text-center py-4">Loading entries...</div>
    <div v-else class="space-y-4">
        <UCard v-for="entry in entries" :key="entry.id">
            <template #header>
                <div class="flex justify-between items-center">
                    <div>
                        <span class="font-bold text-lg text-gray-800">{{ new Date(entry.date).toLocaleDateString() }}</span>
                        <span class="ml-4 text-gray-600">{{ entry.description }}</span>
                    </div>
                    <span class="text-xs text-gray-400 font-mono">{{ entry.id.slice(0, 8) }}</span>
                </div>
            </template>
            
            <table class="w-full text-sm">
                <thead>
                    <tr class="text-left text-gray-500">
                        <th class="font-normal w-1/4">Account</th>
                        <th class="font-normal text-right w-1/4">Debit</th>
                        <th class="font-normal text-right w-1/4">Credit</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(detail, idx) in entry.details" :key="idx" class="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                        <td class="py-1">
                            <span class="font-mono text-gray-500 mr-2">{{ detail.account_code }}</span>
                            {{ detail.account_name }}
                        </td>
                        <td class="text-right py-1 font-mono">{{ detail.debit > 0 ? detail.debit.toLocaleString() : '-' }}</td>
                        <td class="text-right py-1 font-mono">{{ detail.credit > 0 ? detail.credit.toLocaleString() : '-' }}</td>
                    </tr>
                </tbody>
            </table>
        </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const loading = ref(false)
const entries = ref([])

const fetchEntries = async () => {
    loading.value = true
    try {
        const res = await $api.get('/finance/gl/entries')
        entries.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchEntries()
})
</script>
