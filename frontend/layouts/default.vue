<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Mobile Sidebar Backdrop -->
    <div 
      v-if="isSidebarOpen" 
      class="fixed inset-0 bg-black/50 z-[9998] md:hidden"
      @click="isSidebarOpen = false"
    ></div>

    <!-- Sidebar - with high z-index for popup menus -->
    <aside 
      class="fixed md:static inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col z-[9999] transform transition-transform duration-200 ease-in-out"
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

      <nav class="flex-1 px-4 py-4 space-y-1 overflow-y-auto overflow-x-visible">
        <MenuItems :items="links" @item-click="closeSidebarOnMobile" />
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

      <main class="flex-1 overflow-y-auto p-4 md:p-6 relative z-0">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
// Menu state
const authStore = useAuthStore()

// Initialize auth from cookie on layout mount
onMounted(() => {
  authStore.initialize()
  fetchMenus()
})

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

// Menu state
const links = ref([])

const fetchMenus = async () => {
    try {
        const { $api } = useNuxtApp()
        const response = await $api.get('/menus')
        if (response.data && response.data.data) {
            links.value = response.data.data
        } else if (Array.isArray(response.data)) {
            // Fallback for non-standard responses
            links.value = response.data
        }
    } catch (e) {
        console.error('Failed to fetch menus:', e)
        links.value = []
    }
}

const logout = () => {
    authStore.logout()
}

// Notification Logic (socket.io loaded dynamically)
const toast = useToast()
const notifications = ref<any[]>([])
const unreadCount = computed(() => notifications.value.length)

const clearNotifications = () => {
    notifications.value = []
}

onMounted(() => {
    // Lazy connect to Realtime Server - non-blocking with short timeout
    const connectSocket = async () => {
        // Only try to connect if on client side and user is authenticated
        if (!authStore.isAuthenticated || typeof window === 'undefined') return;
        
        try {
            const { io } = await import("socket.io-client");
            const socket = io("http://localhost:3001", {
                auth: {
                    tenantId: authStore.user?.tenant_id,
                    userId: authStore.user?.id
                },
                query: {
                    tenant_id: authStore.user?.tenant_id,
                    user_id: authStore.user?.id
                },
                // Short timeout to prevent blocking
                timeout: 3000,
                reconnectionAttempts: 2
            });
            
            socket.on("connect", () => {
                console.log("Connected to Realtime Server. Socket ID:", socket.id);
            });
            
            socket.on("connect_error", (error) => {
                console.warn("Realtime server unavailable - notifications disabled");
                socket.disconnect();
            });
            
            socket.on("notification", (payload: any) => {
                notifications.value.unshift(payload);
                
                let icon = 'i-heroicons-bell';
                let color = 'primary';
                if (payload.type === 'success') {
                    icon = 'i-heroicons-check-circle';
                    color = 'green';
                } else if (payload.type === 'error') {
                    icon = 'i-heroicons-x-circle';
                    color = 'red';
                } else if (payload.type === 'warning') {
                    icon = 'i-heroicons-exclamation-triangle';
                    color = 'yellow';
                }
                
                toast.add({
                    title: payload.title,
                    description: payload.message,
                    icon: icon,
                    color: color,
                    timeout: 5000
                });
            });
        } catch (e) {
            console.warn("Socket.io not available - notifications disabled");
        }
    };
    
    // Connect socket lazily after initial render
    setTimeout(connectSocket, 1000);
})
</script>
