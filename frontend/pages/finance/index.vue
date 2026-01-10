<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Finance Dashboard</h1>
        <p class="text-sm text-gray-500">Overview of financial performance and key metrics</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <UCard v-for="card in summaryCards" :key="card.title">
        <div class="flex items-center gap-3">
          <div :class="['p-3 rounded-lg', card.bgColor]">
            <UIcon :name="card.icon" :class="['w-6 h-6', card.iconColor]" />
          </div>
          <div>
            <p class="text-sm font-medium text-gray-500">{{ card.title }}</p>
            <p class="text-xl font-bold text-gray-900">{{ card.value }}</p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Cash Position -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">Cash Position</h3>
            <NuxtLink to="/finance/banking/accounts">
              <UButton size="xs" variant="ghost">View All</UButton>
            </NuxtLink>
          </div>
        </template>
        <div class="space-y-3">
          <div v-for="account in bankAccounts" :key="account.name" 
               class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center gap-3">
              <UIcon name="i-heroicons-building-library" class="w-5 h-5 text-blue-600" />
              <span class="font-medium">{{ account.name }}</span>
            </div>
            <span class="font-semibold text-gray-900">{{ formatCurrency(account.balance) }}</span>
          </div>
          <div class="pt-3 border-t border-gray-200 flex justify-between">
            <span class="font-semibold text-gray-700">Total Cash</span>
            <span class="font-bold text-lg text-green-600">{{ formatCurrency(totalCash) }}</span>
          </div>
        </div>
      </UCard>

      <!-- Accounts Receivable Summary -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">Accounts Receivable</h3>
            <NuxtLink to="/finance/ar/aging">
              <UButton size="xs" variant="ghost">View Aging</UButton>
            </NuxtLink>
          </div>
        </template>
        <div class="space-y-3">
          <div v-for="aging in arAging" :key="aging.period" 
               class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span class="text-gray-600">{{ aging.period }}</span>
            <span :class="['font-semibold', aging.class]">{{ formatCurrency(aging.amount) }}</span>
          </div>
          <div class="pt-3 border-t border-gray-200 flex justify-between">
            <span class="font-semibold text-gray-700">Total Receivable</span>
            <span class="font-bold text-lg text-primary-600">{{ formatCurrency(totalAR) }}</span>
          </div>
        </div>
      </UCard>

      <!-- Accounts Payable Summary -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">Accounts Payable</h3>
            <NuxtLink to="/finance/ap/aging">
              <UButton size="xs" variant="ghost">View Aging</UButton>
            </NuxtLink>
          </div>
        </template>
        <div class="space-y-3">
          <div v-for="aging in apAging" :key="aging.period" 
               class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span class="text-gray-600">{{ aging.period }}</span>
            <span :class="['font-semibold', aging.class]">{{ formatCurrency(aging.amount) }}</span>
          </div>
          <div class="pt-3 border-t border-gray-200 flex justify-between">
            <span class="font-semibold text-gray-700">Total Payable</span>
            <span class="font-bold text-lg text-red-600">{{ formatCurrency(totalAP) }}</span>
          </div>
        </div>
      </UCard>

      <!-- Quick Actions -->
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Quick Actions</h3>
        </template>
        <div class="grid grid-cols-2 gap-3">
          <NuxtLink to="/finance/ar/invoices" 
                    class="flex flex-col items-center gap-2 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <UIcon name="i-heroicons-document-plus" class="w-8 h-8 text-primary-600" />
            <span class="text-sm font-medium">New Invoice</span>
          </NuxtLink>
          <NuxtLink to="/finance/ap/payments" 
                    class="flex flex-col items-center gap-2 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <UIcon name="i-heroicons-banknotes" class="w-8 h-8 text-green-600" />
            <span class="text-sm font-medium">Record Payment</span>
          </NuxtLink>
          <NuxtLink to="/finance/banking/transactions" 
                    class="flex flex-col items-center gap-2 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <UIcon name="i-heroicons-arrows-right-left" class="w-8 h-8 text-blue-600" />
            <span class="text-sm font-medium">Bank Transaction</span>
          </NuxtLink>
          <NuxtLink to="/finance/gl" 
                    class="flex flex-col items-center gap-2 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <UIcon name="i-heroicons-book-open" class="w-8 h-8 text-purple-600" />
            <span class="text-sm font-medium">Journal Entry</span>
          </NuxtLink>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
const summaryCards = ref([
  { title: 'Total Revenue (MTD)', value: 'Rp 125,500,000', icon: 'i-heroicons-arrow-trending-up', bgColor: 'bg-green-100', iconColor: 'text-green-600' },
  { title: 'Total Expenses (MTD)', value: 'Rp 78,250,000', icon: 'i-heroicons-arrow-trending-down', bgColor: 'bg-red-100', iconColor: 'text-red-600' },
  { title: 'Outstanding AR', value: 'Rp 45,000,000', icon: 'i-heroicons-document-text', bgColor: 'bg-blue-100', iconColor: 'text-blue-600' },
  { title: 'Outstanding AP', value: 'Rp 32,500,000', icon: 'i-heroicons-clipboard-document-list', bgColor: 'bg-orange-100', iconColor: 'text-orange-600' }
])

const bankAccounts = ref([
  { name: 'BCA Giro Utama', balance: 250000000 },
  { name: 'Mandiri Operasional', balance: 85000000 },
  { name: 'Petty Cash', balance: 5000000 }
])

const arAging = ref([
  { period: 'Current (0-30 days)', amount: 25000000, class: 'text-green-600' },
  { period: '31-60 days', amount: 12000000, class: 'text-yellow-600' },
  { period: '61-90 days', amount: 5000000, class: 'text-orange-600' },
  { period: '> 90 days', amount: 3000000, class: 'text-red-600' }
])

const apAging = ref([
  { period: 'Current (0-30 days)', amount: 20000000, class: 'text-green-600' },
  { period: '31-60 days', amount: 8000000, class: 'text-yellow-600' },
  { period: '> 60 days', amount: 4500000, class: 'text-red-600' }
])

const totalCash = computed(() => bankAccounts.value.reduce((sum, acc) => sum + acc.balance, 0))
const totalAR = computed(() => arAging.value.reduce((sum, item) => sum + item.amount, 0))
const totalAP = computed(() => apAging.value.reduce((sum, item) => sum + item.amount, 0))

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value)
}

const fetchData = () => {
  // TODO: Fetch real data from API
}
</script>
