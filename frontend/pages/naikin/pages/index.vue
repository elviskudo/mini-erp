<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Landing Pages</h1>
        <p class="text-sm text-gray-500">Manage your marketing pages and funnels</p>
      </div>
      <UButton icon="i-heroicons-plus" color="black" to="/naikin/pages/create">New Page</UButton>
    </div>

    <!-- Filters -->
    <div class="flex gap-4 mb-6">
      <UInput icon="i-heroicons-magnifying-glass" placeholder="Search pages..." class="w-64" />
      <USelectMenu placeholder="Status" :options="['All', 'Published', 'Draft']" />
    </div>

    <!-- Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <!-- Create New Card -->
      <NuxtLink to="/naikin/pages/create" class="border-2 border-dashed border-gray-200 rounded-xl flex flex-col items-center justify-center p-8 hover:border-pink-500 hover:bg-pink-50 transition-colors group cursor-pointer h-[280px]">
        <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center group-hover:bg-pink-100 transition-colors mb-4">
          <UIcon name="i-heroicons-plus" class="w-6 h-6 text-gray-400 group-hover:text-pink-600" />
        </div>
        <span class="font-medium text-gray-900">Create New Page</span>
      </NuxtLink>

      <!-- Page Card Mockups -->
      <UCard v-for="page in pages" :key="page.id" class="flex flex-col h-[280px] hover:ring-2 hover:ring-pink-500/20 transition-all cursor-pointer group" :ui="{ body: { padding: 'p-0' } }">
        <!-- Preview Image area -->
        <div class="h-40 bg-gray-100 relative overflow-hidden group-hover:opacity-90 transition-opacity">
           <div class="absolute inset-0 flex items-center justify-center text-gray-300">
              <UIcon name="i-heroicons-photo" class="w-12 h-12" />
           </div>
           <!-- Status Badge -->
           <div class="absolute top-3 left-3">
              <UBadge :color="page.status === 'Published' ? 'green' : 'gray'" size="xs" variant="solid">{{ page.status }}</UBadge>
           </div>
           <!-- Menu -->
           <div class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <UButton color="white" icon="i-heroicons-ellipsis-horizontal" size="xs" variant="solid" />
           </div>
        </div>
        
        <!-- Content -->
        <div class="p-4 flex flex-col flex-1">
          <h3 class="font-bold text-gray-900 truncate">{{ page.title }}</h3>
          <div class="text-xs text-gray-500 mb-4 flex items-center gap-1">
             <UIcon name="i-heroicons-link" class="w-3 h-3" />
             /u/{{ page.slug }}
          </div>
          
          <div class="mt-auto flex items-center justify-between pt-4 border-t border-gray-100">
             <div class="flex flex-col">
                <span class="text-xs text-gray-500">Visits</span>
                <span class="font-bold text-gray-900">{{ page.visits }}</span>
             </div>
             <div class="flex flex-col items-end">
                <span class="text-xs text-gray-500">Conversions</span>
                <span class="font-bold text-gray-900">{{ page.conversions }}%</span>
             </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'naikin',
  middleware: 'auth'
})

// Mock Data
const pages = ref([
  { id: 1, title: 'Ebook Sales Landing', slug: 'ebook-viral-2025', status: 'Published', visits: '1.2k', conversions: 4.5 },
  { id: 2, title: 'Webinar Registration', slug: 'webinar-bisnis', status: 'Draft', visits: '0', conversions: 0 },
  { id: 3, title: 'Product Showcase', slug: 'sepatu-keren', status: 'Published', visits: '850', conversions: 2.1 },
])
</script>
