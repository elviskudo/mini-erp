<template>
  <div class="space-y-4">
    <!-- Search and filters -->
    <div class="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
      <div class="flex gap-2 items-center">
        <UInput
          v-model="localSearchQuery"
          icon="i-heroicons-magnifying-glass"
          :placeholder="searchPlaceholder"
          class="w-full sm:w-64"
          @keyup.enter="handleSearch"
        />
        <UButton
          color="gray"
          variant="ghost"
          icon="i-heroicons-arrow-path"
          :loading="loading"
          @click="refresh"
        />
      </div>
      <div class="flex gap-2 items-center">
        <USelect
          v-model="localLimit"
          :options="pageSizeOptions"
          class="w-24"
          @change="handleLimitChange"
        />
        <span class="text-sm text-gray-500">per page</span>
        <slot name="filters" />
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="loading" class="flex justify-center py-8">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8 text-primary-500" />
    </div>

    <!-- Table -->
    <UTable
      v-if="!loading"
      :columns="sortableColumns"
      :rows="data"
      @select="$emit('select', $event)"
    >
      <template v-for="(_, slot) in $slots" #[slot]="scope">
        <slot :name="slot" v-bind="scope" />
      </template>
    </UTable>

    <!-- Server-side Pagination -->
    <div v-if="pagination && pagination.total_pages > 1" class="flex flex-col sm:flex-row items-center justify-between gap-3">
      <p class="text-sm text-gray-500">
        Showing {{ ((pagination.page - 1) * pagination.limit) + 1 }} 
        to {{ Math.min(pagination.page * pagination.limit, pagination.total_items) }} 
        of {{ pagination.total_items }} results
      </p>
      <div class="flex items-center gap-2">
        <UButton
          color="gray"
          variant="ghost"
          icon="i-heroicons-chevron-left"
          :disabled="!pagination.has_prev"
          @click="handlePageChange(pagination.page - 1)"
        />
        <div class="flex gap-1">
          <template v-for="pageNum in visiblePages" :key="pageNum">
            <UButton
              v-if="pageNum !== '...'"
              :color="pageNum === pagination.page ? 'primary' : 'gray'"
              :variant="pageNum === pagination.page ? 'solid' : 'ghost'"
              size="sm"
              @click="handlePageChange(pageNum as number)"
            >
              {{ pageNum }}
            </UButton>
            <span v-else class="px-2 py-1 text-gray-400">...</span>
          </template>
        </div>
        <UButton
          color="gray"
          variant="ghost"
          icon="i-heroicons-chevron-right"
          :disabled="!pagination.has_next"
          @click="handlePageChange(pagination.page + 1)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Column {
  key: string
  label: string
  sortable?: boolean
}

interface Pagination {
  page: number
  limit: number
  total_items: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

interface Props {
  columns: Column[]
  data: any[]
  pagination?: Pagination
  loading?: boolean
  searchPlaceholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchPlaceholder: 'Search...',
})

const emit = defineEmits(['select', 'page-change', 'limit-change', 'search', 'refresh'])

const localSearchQuery = ref('')
const localLimit = ref(props.pagination?.limit || 10)

const pageSizeOptions = [
  { label: '10', value: 10 },
  { label: '25', value: 25 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
]

// Make columns sortable by default
const sortableColumns = computed(() => {
  return props.columns.map(col => ({
    ...col,
    sortable: col.sortable !== false
  }))
})

// Calculate visible page numbers
const visiblePages = computed(() => {
  if (!props.pagination) return []
  const { page, total_pages } = props.pagination
  const pages: (number | string)[] = []
  
  if (total_pages <= 7) {
    for (let i = 1; i <= total_pages; i++) pages.push(i)
  } else {
    pages.push(1)
    if (page > 3) pages.push('...')
    for (let i = Math.max(2, page - 1); i <= Math.min(total_pages - 1, page + 1); i++) {
      pages.push(i)
    }
    if (page < total_pages - 2) pages.push('...')
    pages.push(total_pages)
  }
  
  return pages
})

// Event handlers
function handlePageChange(page: number) {
  emit('page-change', page)
}

function handleLimitChange() {
  emit('limit-change', localLimit.value)
}

function handleSearch() {
  emit('search', localSearchQuery.value)
}

function refresh() {
  emit('refresh')
}

// Update local limit when prop changes
watch(() => props.pagination?.limit, (newLimit) => {
  if (newLimit) localLimit.value = newLimit
})
</script>
