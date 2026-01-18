<template>
    <div class="space-y-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">Sales Dashboard</h1>
            <p class="text-gray-500">Overview of sales performance and activity.</p>
        </div>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <UCard>
                <div class="text-center">
                    <p class="text-sm text-gray-500">Monthly Revenue</p>
                    <p class="text-3xl font-bold text-green-600">{{ formatCurrency(stats.revenue_monthly) }}</p>
                </div>
            </UCard>
            <UCard>
                <div class="text-center">
                    <p class="text-sm text-gray-500">Pipeline Value</p>
                    <p class="text-3xl font-bold text-blue-600">{{ formatCurrency(stats.pipeline_value) }}</p>
                </div>
            </UCard>
            <UCard>
                <div class="text-center">
                    <p class="text-sm text-gray-500">Active Orders</p>
                    <p class="text-3xl font-bold text-orange-600">{{ stats.active_orders }}</p>
                </div>
            </UCard>
             <UCard>
                <div class="text-center">
                    <p class="text-sm text-gray-500">Conversion Rate</p>
                    <p class="text-3xl font-bold text-purple-600">{{ stats.conversion_rate }}%</p>
                </div>
            </UCard>
        </div>

        <!-- Charts Section (Placeholder for now) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <UCard>
                <template #header>
                    <h3 class="font-semibold">Sales Trend</h3>
                </template>
                <div class="h-64 flex items-center justify-center bg-gray-50">
                    <p class="text-gray-400">Chart Placeholder</p>
                </div>
            </UCard>
            <UCard>
                <template #header>
                    <h3 class="font-semibold">Top Products</h3>
                </template>
               <div class="h-64 flex items-center justify-center bg-gray-50">
                    <p class="text-gray-400">Chart Placeholder</p>
                </div>
            </UCard>
        </div>
    </div>
</template>

<script setup lang="ts">
definePageMeta({
    middleware: 'auth'
})

const { $api } = useNuxtApp()
const stats = ref({
    revenue_monthly: 0,
    pipeline_value: 0,
    active_orders: 0,
    conversion_rate: 0
})

const fetchStats = async () => {
    try {
        const res = await $api.get('/sales/stats')
        if (res.data.success) {
            stats.value = res.data.data
        }
    } catch (e) {
        console.error('Failed to fetch sales stats', e)
    }
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(value)
}

onMounted(() => {
    fetchStats()
})
</script>
