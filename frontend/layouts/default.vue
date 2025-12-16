<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Mobile Sidebar Backdrop -->
    <div 
      v-if="isSidebarOpen" 
      class="fixed inset-0 bg-black/50 z-40 md:hidden"
      @click="isSidebarOpen = false"
    ></div>

    <!-- Sidebar -->
    <aside 
      class="fixed md:static inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col z-50 transform transition-transform duration-200 ease-in-out"
      :class="[
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      ]"
    >
      <div class="h-16 flex items-center justify-between px-6 border-b border-gray-200">
        <span class="text-xl font-bold text-primary-600">Mini ERP</span>
        <UButton 
          icon="i-heroicons-x-mark" 
          color="gray" 
          variant="ghost" 
          class="md:hidden"
          @click="isSidebarOpen = false"
        />
      </div>

      <nav class="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        <template v-for="link in links" :key="link.label">
          <!-- Direct Link -->
          <NuxtLink 
            v-if="!link.children"
            :to="link.to"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              $route.path === link.to 
                ? 'bg-primary-50 text-primary-700' 
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            @click="closeSidebarOnMobile"
          >
            <UIcon :name="link.icon" class="w-5 h-5 flex-shrink-0" />
            <span>{{ link.label }}</span>
          </NuxtLink>
          
          <!-- Collapsible Menu -->
          <div v-else>
            <button 
              @click="toggleMenu(link.label)"
              class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <div class="flex items-center gap-3">
                <UIcon :name="link.icon" class="w-5 h-5 flex-shrink-0" />
                <span>{{ link.label }}</span>
              </div>
              <UIcon 
                :name="openMenus.includes(link.label) ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-right'" 
                class="w-4 h-4 flex-shrink-0 transition-transform" 
              />
            </button>
            
            <!-- Children -->
            <div v-show="openMenus.includes(link.label)" class="ml-8 mt-1 space-y-1">
              <NuxtLink 
                v-for="child in link.children" 
                :key="child.to"
                :to="child.to"
                class="block px-3 py-2 rounded-lg text-sm transition-colors"
                :class="[
                  $route.path === child.to 
                    ? 'bg-primary-50 text-primary-700 font-medium' 
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                ]"
                @click="closeSidebarOnMobile"
              >
                {{ child.label }}
              </NuxtLink>
            </div>
          </div>
        </template>
      </nav>

      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold text-sm">
                {{ userInitials }}
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ authStore.user?.username || 'User' }}</p>
                <p class="text-xs text-gray-500 truncate capitalize">{{ authStore.user?.role || 'Guest' }}</p>
            </div>
             <UButton icon="i-heroicons-arrow-right-on-rectangle" color="gray" variant="ghost" @click="logout" />
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Header -->
        <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 md:px-6">
            <!-- Mobile: Hamburger + Title -->
            <div class="flex items-center gap-3 md:hidden">
                <UButton 
                  icon="i-heroicons-bars-3" 
                  color="gray" 
                  variant="ghost" 
                  @click="isSidebarOpen = true"
                />
                <span class="text-lg font-bold">Mini ERP</span>
            </div>
            
            <!-- Desktop: Spacer -->
            <div class="hidden md:block flex-1"></div>
            
            <div class="flex items-center gap-2 md:gap-4">
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
        </header>

      <main class="flex-1 overflow-y-auto p-4 md:p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const authStore = useAuthStore()
const route = useRoute()

// Mobile sidebar state
const isSidebarOpen = ref(false)

// Close sidebar on route change (mobile)
watch(() => route.path, () => {
  isSidebarOpen.value = false
})

const closeSidebarOnMobile = () => {
  if (window.innerWidth < 768) {
    isSidebarOpen.value = false
  }
}

const userInitials = computed(() => {
    const name = authStore.user?.username || 'U'
    return name.substring(0, 2).toUpperCase()
})

// Collapsible menu state
const openMenus = ref<string[]>([])

const toggleMenu = (label: string) => {
    const index = openMenus.value.indexOf(label)
    if (index === -1) {
        openMenus.value.push(label)
    } else {
        openMenus.value.splice(index, 1)
    }
}

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
      icon: 'i-heroicons-clipboard-document-list',
      children: [
          { label: 'All Projects', to: '/projects' }
      ]
  },
  {
      label: 'Maintenance',
      icon: 'i-heroicons-cog-8-tooth',
      children: [
          { label: 'Work Orders', to: '/maintenance' }
      ]
  },
  {
      label: 'B2B Portal',
      icon: 'i-heroicons-globe-alt',
      children: [
          { label: 'Browse Catalog', to: '/portal/shop' }
      ]
  },
  {
      label: 'Compliance',
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
const notifications = ref<any[]>([])
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
    
    socket.on("notification", (payload: any) => {
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
