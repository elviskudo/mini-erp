<template>
  <div class="min-h-screen bg-gray-50 font-sans text-gray-900 flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col fixed h-full z-20 transition-transform duration-300" :class="{ '-translate-x-full': !sidebarOpen, 'translate-x-0': sidebarOpen, 'lg:translate-x-0': true }">
      <!-- Logo -->
      <div class="p-6 flex items-center gap-3">
        <div class="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white font-bold text-xl">
          <UIcon name="i-heroicons-bolt" />
        </div>
        <div>
          <h1 class="font-bold text-lg leading-tight">Vertex</h1>
          <p class="text-xs text-gray-400">Workspace</p>
        </div>
        <UButton color="gray" variant="ghost" icon="i-heroicons-bars-3-bottom-left" class="ml-auto lg:hidden" @click="sidebarOpen = false" />
      </div>

      <!-- Menu -->
      <div class="flex-1 overflow-y-auto px-4 py-2 space-y-6">
        <div>
          <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 px-2">Menu</div>
          <nav class="space-y-1">
            <NuxtLink to="/naikin/dashboard" class="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors" :class="$route.path.includes('dashboard') ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'">
              <div class="flex items-center gap-3">
                <UIcon name="i-heroicons-squares-2x2" class="w-5 h-5" />
                Dashboard
              </div>
            </NuxtLink>
            
            <NuxtLink to="/naikin/notifications" class="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
              <div class="flex items-center gap-3">
                <UIcon name="i-heroicons-bell" class="w-5 h-5" />
                Notifications
              </div>
              <UBadge color="gray" variant="solid" size="xs" :ui="{ rounded: 'rounded-full' }">14</UBadge>
            </NuxtLink>

            <div class="space-y-1">
               <button class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                  <div class="flex items-center gap-3">
                    <UIcon name="i-heroicons-clipboard-document-check" class="w-5 h-5" />
                    Task
                  </div>
                  <UIcon name="i-heroicons-chevron-down" class="w-4 h-4 text-gray-400" />
               </button>
               <div class="pl-11 pr-2 space-y-1">
                  <div class="flex justify-between text-sm text-gray-500 py-1 hover:text-gray-900 cursor-pointer">
                    <span>Backlog</span>
                    <span class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">24</span>
                  </div>
                  <div class="flex justify-between text-sm text-gray-500 py-1 hover:text-gray-900 cursor-pointer">
                    <span>In progress</span>
                    <span class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">8</span>
                  </div>
                   <div class="flex justify-between text-sm text-gray-500 py-1 hover:text-gray-900 cursor-pointer">
                    <span>Validation</span>
                    <span class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">4</span>
                  </div>
               </div>
            </div>
          </nav>
        </div>

        <div>
            <nav class="space-y-1">
                 <NuxtLink to="/naikin/contacts" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                    <UIcon name="i-heroicons-users" class="w-5 h-5" />
                    Contact
                 </NuxtLink>
                 <NuxtLink to="/naikin/mail" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                    <UIcon name="i-heroicons-envelope" class="w-5 h-5" />
                    Mail
                 </NuxtLink>
                 <NuxtLink to="/naikin/companies" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                    <UIcon name="i-heroicons-building-office" class="w-5 h-5" />
                    Companies
                 </NuxtLink>
                 <NuxtLink to="/naikin/calendar" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                    <UIcon name="i-heroicons-calendar" class="w-5 h-5" />
                    Calendar
                 </NuxtLink>
                 <NuxtLink to="/naikin/integrations" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                    <UIcon name="i-heroicons-puzzle-piece" class="w-5 h-5" />
                    Integration
                 </NuxtLink>
            </nav>
        </div>
      </div>

      <!-- Footer Menu -->
      <div class="p-4 border-t border-gray-100 space-y-1">
         <NuxtLink to="/naikin/feedback" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
            <UIcon name="i-heroicons-chat-bubble-left-right" class="w-5 h-5" />
            Feedback
         </NuxtLink>
         <NuxtLink to="/naikin/help" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
            <UIcon name="i-heroicons-flag" class="w-5 h-5" />
            Help Center
         </NuxtLink>
         <div class="flex items-center justify-between px-3 py-2">
            <div class="flex items-center gap-3 text-sm font-medium text-gray-600">
                <UIcon name="i-heroicons-moon" class="w-5 h-5" />
                Dark Mode
            </div>
            <UToggle v-model="darkMode" />
         </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 lg:ml-64 flex flex-col min-h-screen transition-all duration-300">
      <!-- Header -->
      <header class="bg-white border-b border-gray-100 sticky top-0 z-10 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-4">
             <button class="lg:hidden text-gray-600" @click="sidebarOpen = true">
                <UIcon name="i-heroicons-bars-3" class="w-6 h-6" />
             </button>
             <h2 class="text-xl font-bold text-gray-900">Dashboard</h2>
        </div>

        <div class="flex items-center gap-4">
            <!-- Search -->
            <div class="relative hidden md:block">
                <UIcon name="i-heroicons-magnifying-glass" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input type="text" placeholder="Search anything" class="pl-10 pr-12 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64" />
                <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <UKbd>⌘</UKbd>
                    <UKbd>K</UKbd>
                </div>
            </div>

            <!-- Actions -->
            <UButton color="gray" variant="ghost" icon="i-heroicons-cog-6-tooth" />
            <UButton color="gray" variant="ghost" icon="i-heroicons-bell" />
            
            <!-- User Profile -->
            <div class="flex items-center gap-3 pl-4 border-l border-gray-200">
                <UAvatar src="https://i.pravatar.cc/150?u=anatasia" alt="Anatasia" />
                <div class="hidden md:block text-sm">
                    <div class="font-medium text-gray-900">Anatasya</div>
                </div>
                <UIcon name="i-heroicons-chevron-down" class="w-4 h-4 text-gray-400" />
            </div>
        </div>
      </header>

      <!-- Page Content -->
      <main class="p-6">
        <!-- Top Toolbar -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <div class="flex items-center gap-4">
                <UButton color="white" class="shadow-sm border border-indigo-100 text-indigo-600">
                    <UIcon name="i-heroicons-sparkles" />
                    Ask AI
                </UButton>
                <div class="flex items-center gap-2 text-xs text-gray-400">
                    <UIcon name="i-heroicons-arrow-path" class="w-3 h-3" />
                    Last update : 25 April 2025
                </div>
            </div>

            <div class="flex items-center gap-2">
                <UButton color="white" variant="solid" icon="i-heroicons-calendar" trailing>Year</UButton>
                <UButton color="white" variant="solid" icon="i-heroicons-funnel">Filter</UButton>
                <UButton color="blue" icon="i-heroicons-arrow-down-tray" trailing>Import / Export</UButton>
            </div>
        </div>

        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
const sidebarOpen = ref(false)
const darkMode = ref(false)
</script>
