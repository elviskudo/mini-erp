<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col">
      <div class="h-16 flex items-center px-6 border-b border-gray-200">
        <span class="text-xl font-bold text-primary-600">Mini ERP</span>
      </div>

      <nav class="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        <UVerticalNavigation :links="links" />
      </nav>

      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
                {{ userInitials }}
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ authStore.user?.username || 'User' }}</p>
                <p class="text-xs text-gray-500 truncate">{{ authStore.user?.role || 'Guest' }}</p>
            </div>
             <UButton icon="i-heroicons-arrow-right-on-rectangle" color="gray" variant="ghost" @click="logout" />
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Header (Mobile usually, but keeping simple for now) -->
        <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
            <span class="text-lg font-bold md:hidden">Mini ERP</span>
            <div class="flex-1"></div> <!-- Spacer -->
            
            <div class="flex items-center gap-4">
                 <!-- Notification Bell -->
                 <UPopover>
                    <UButton icon="i-heroicons-bell" color="gray" variant="ghost" :ui="{ rounded: 'rounded-full' }">
                        <template #trailing>
                            <UBadge v-if="unreadCount > 0" color="red" variant="solid" size="xs" :ui="{ rounded: 'rounded-full' }" class="-ml-2 -mt-2">{{ unreadCount }}</UBadge>
                        </template>
                    </UButton>
                    <template #panel>
                        <div class="p-4 w-80">
                            <h3 class="font-bold mb-2">Notifications</h3>
                            <div v-if="notifications.length === 0" class="text-sm text-gray-500">No new notifications.</div>
                            <div v-else class="space-y-2 max-h-60 overflow-y-auto">
                                <div v-for="(n, idx) in notifications" :key="idx" class="text-sm border-b pb-2 last:border-0">
                                    <div class="font-bold">{{ n.title }}</div>
                                    <div class="text-gray-600">{{ n.message }}</div>
                                    <div class="text-xs text-gray-400 mt-1">{{ new Date(n.timestamp).toLocaleTimeString() }}</div>
                                </div>
                            </div>
                            <div v-if="notifications.length > 0" class="mt-2 text-right">
                                <UButton size="xs" variant="ghost" @click="clearNotifications">Clear All</UButton>
                            </div>
                        </div>
                    </template>
                 </UPopover>
            </div>
            
            <UButton icon="i-heroicons-bars-3" color="gray" variant="ghost" class="md:hidden ml-2" />
        </header>

      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const userInitials = computed(() => {
    const name = authStore.user?.username || 'U'
    return name.substring(0, 2).toUpperCase()
})

const links = [
  {
    label: 'Dashboard',
    icon: 'i-heroicons-home',
    to: '/'
  },
  {
    label: 'Initial Setup',
    icon: 'i-heroicons-cog-6-tooth',
    to: '/setup'
  },
  {
    label: 'Manufacturing',
    icon: 'i-heroicons-wrench-screwdriver',
    children: [
        { label: 'Work Centers', to: '/manufacturing/work-centers' },
        { label: 'Products & BOM', to: '/manufacturing/products' },
        { label: 'Production', to: '/manufacturing/production' }
    ]
  },
   {
    label: 'Inventory',
    icon: 'i-heroicons-cube',
    children: [
        { label: 'Stock Status', to: '/inventory/stock' },
        { label: 'Warehouses', to: '/inventory/warehouses' },
        { label: 'Movements', to: '/inventory/movements' },
        { label: 'Goods Receipt', to: '/inventory/receiving' }, 
        { label: 'Opname', to: '/inventory/opname' } 
    ]
  },
  {
    label: 'Procurement',
    icon: 'i-heroicons-shopping-cart',
    children: [
        { label: 'Purchase Requests', to: '/procurement/requests' },
        { label: 'Purchase Orders', to: '/procurement/orders' },
        { label: 'Vendors', to: '/procurement/vendors' }
    ]
  },
  {
      label: 'Quality Control',
      icon: 'i-heroicons-beaker',
      to: '/qc/inspections'
  },
   {
      label: 'Logistics',
      icon: 'i-heroicons-truck',
      to: '/logistics/delivery'
  },
  {
    label: 'Finance',
    icon: 'i-heroicons-banknotes',
    children: [
        { label: 'Chart of Accounts', to: '/finance/coa' },
        { label: 'General Ledger', to: '/finance/gl' },
        { label: 'Reports', to: '/finance/reports' },
        { label: 'Fixed Assets', to: '/finance/assets' }
    ]
  },
  {
      label: 'HR & Payroll',
      icon: 'i-heroicons-user-group',
      children: [
          { label: 'Employees', to: '/hr/employees' },
          { label: 'Payroll Run', to: '/hr/payroll' }
      ]
  },
  {
      label: 'CRM & Sales',
      icon: 'i-heroicons-briefcase',
      children: [
          { label: 'Sales Orders', to: '/crm/orders' }
      ]
  },
  {
      label: 'Projects (PMO)',
      icon: 'i-heroicons-paper-airplane',
      children: [
          { label: 'All Projects', to: '/projects' }
      ]
  },
  {
      label: 'Maintenance (CMMS)',
      icon: 'i-heroicons-wrench-screwdriver',
      children: [
          { label: 'Work Orders', to: '/maintenance' }
      ]
  },
  {
      label: 'B2B Portal (Sim)',
      icon: 'i-heroicons-globe-alt',
      children: [
          { label: 'Browse Catalog', to: '/portal/shop' }
      ]
  },
  {
      label: 'Compliance (QMS)',
      icon: 'i-heroicons-shield-check',
      to: '/compliance'
  }
]

const logout = () => {
    authStore.logout()
}

// Notification Logic
import { io } from "socket.io-client";
const toast = useToast()
const notifications = ref([])
const unreadCount = computed(() => notifications.value.length)

const clearNotifications = () => {
    notifications.value = []
}

onMounted(() => {
    // Connect to Realtime Server
    const socket = io("http://localhost:3001");
    
    socket.on("connect", () => {
        console.log("Connected to Realtime Server");
    });
    
    socket.on("notification", (payload) => {
        console.log("Notification received:", payload);
        notifications.value.unshift(payload);
        
        toast.add({
            title: payload.title,
            description: payload.message,
            icon: 'i-heroicons-bell',
            timeout: 5000
        });
    });
})
</script>
