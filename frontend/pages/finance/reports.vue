<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Financial Reports</h2>
    </div>

    <UTabs :items="tabs" class="w-full" @change="onTabChange">
        <template #item="{ item }">
            <UCard class="mt-4">
                <div v-if="loading" class="text-center py-8">Generating Report...</div>
                <div v-else class="min-h-[300px]">
                    <div v-if="item.key === 'balance_sheet'" class="grid grid-cols-2 gap-6">
                        <!-- Assets -->
                        <div>
                            <h3 class="text-xl font-bold mb-4 text-emerald-600">Assets</h3>
                            <table class="w-full">
                                <tbody>
                                    <tr v-for="(val, name) in reportData.assets" :key="name" class="border-b">
                                        <td class="py-2">{{ name }}</td>
                                        <td class="text-right font-mono">{{ val.toLocaleString() }}</td>
                                    </tr>
                                    <tr class="border-t-2 border-black font-bold">
                                        <td class="py-2">Total Assets</td>
                                        <td class="text-right font-mono">{{ reportData.total_assets?.toLocaleString() }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <!-- Liab & Equity -->
                        <div>
                            <h3 class="text-xl font-bold mb-4 text-red-600">Liabilities & Equity</h3>
                             <table class="w-full mb-6">
                                <tbody>
                                    <tr v-for="(val, name) in reportData.liabilities" :key="name" class="border-b">
                                        <td class="py-2">{{ name }}</td>
                                        <td class="text-right font-mono">{{ val.toLocaleString() }}</td>
                                    </tr>
                                    <tr class="font-bold">
                                        <td class="py-2">Total Liabilities</td>
                                        <td class="text-right font-mono">{{ reportData.total_liabilities?.toLocaleString() }}</td>
                                    </tr>
                                </tbody>
                            </table>
                             <table class="w-full">
                                <tbody>
                                    <tr v-for="(val, name) in reportData.equity" :key="name" class="border-b">
                                        <td class="py-2">{{ name }}</td>
                                        <td class="text-right font-mono">{{ val.toLocaleString() }}</td>
                                    </tr>
                                     <tr class="font-bold">
                                        <td class="py-2">Total Equity</td>
                                        <td class="text-right font-mono">{{ reportData.total_equity?.toLocaleString() }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div v-else>
                        <pre class="bg-gray-50 p-4 rounded text-sm overflow-auto">{{ JSON.stringify(reportData, null, 2) }}</pre>
                    </div>
                </div>
            </UCard>
        </template>
    </UTabs>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const loading = ref(false)
const reportData = ref({})

const tabs = [
    { key: 'balance_sheet', label: 'Balance Sheet' },
    { key: 'profit_loss', label: 'Profit & Loss' },
    { key: 'trial_balance', label: 'Trial Balance' }
]

const fetchReport = async (type: string) => {
    loading.value = true
    try {
        let endpoint = ''
        if (type === 'balance_sheet') endpoint = '/finance/reports/balance-sheet'
        else if (type === 'profit_loss') endpoint = '/finance/reports/profit-loss'
        else if (type === 'trial_balance') endpoint = '/finance/reports/trial-balance'
        
        if (endpoint) {
            const res = await $api.get(endpoint)
            reportData.value = res.data
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const onTabChange = (index: number) => {
    const tab = tabs[index]
    fetchReport(tab.key)
}

onMounted(() => {
    fetchReport('balance_sheet')
})
</script>
