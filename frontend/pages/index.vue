<template>
    <div class="space-y-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p class="text-gray-500">Welcome back, {{ authStore.user?.username }}</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <UCard>
                <div class="text-center">
                     <p class="text-sm text-gray-500">Pending PRs</p>
                     <p class="text-3xl font-bold text-primary-600">3</p>
                </div>
            </UCard>
              <UCard>
                <div class="text-center">
                     <p class="text-sm text-gray-500">Production Orders</p>
                     <p class="text-3xl font-bold text-orange-600">5</p>
                </div>
            </UCard>
              <UCard>
                <div class="text-center">
                     <p class="text-sm text-gray-500">Low Stock Items</p>
                     <p class="text-3xl font-bold text-red-600">12</p>
                </div>
            </UCard>
        </div>

        <UCard>
            <template #header>
                <h3 class="font-semibold">Getting Started</h3>
            </template>
            <p class="text-gray-600 mb-4">
                The Frontend Foundation is successfully installed! You can now navigate through the modules using the sidebar.
            </p>
             <p class="text-sm text-gray-500">
                Note: Many pages are placeholders. We will implement them one by one.
            </p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
definePageMeta({
  middleware: 'auth'
})
const authStore = useAuthStore()
</script>
