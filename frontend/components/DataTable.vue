<template>
  <div class="space-y-4">
    <!-- Search and Controls Row -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <!-- Search -->
      <div v-if="searchable" class="w-full sm:w-80">
        <UInput
          v-model="searchQuery"
          icon="i-heroicons-magnifying-glass"
          :placeholder="searchPlaceholder"
          @input="onSearch"
        />
      </div>
      
      <!-- Page Size Selector -->
      <div v-if="paginated" class="flex items-center gap-2 text-sm text-gray-500">
        <span>Show</span>
        <USelect
          v-model="currentPageSize"
          :options="pageSizeOptions"
          size="sm"
          class="w-20"
          @change="onPageSizeChange"
        />
        <span>entries</span>
      </div>
    </div>

    <!-- Table -->
    <UTable
      :columns="sortableColumns"
      :rows="paginatedRows"
      :loading="loading"
      @select="$emit('select', $event)"
    >
      <!-- Pass through all slots -->
      <template v-for="(_, slotName) in $slots" #[slotName]="slotProps">
        <slot :name="slotName" v-bind="slotProps" />
      </template>
      
      <!-- Sortable Headers -->
      <template v-for="col in sortableColumns" :key="col.key" #[`${col.key}-header`]>
        <button
          v-if="sortable && col.sortable !== false"
          class="flex items-center gap-1 font-semibold hover:text-primary-500 transition-colors"
          @click="toggleSort(col.key)"
        >
          {{ col.label }}
          <UIcon 
            v-if="sortColumn === col.key"
            :name="sortDirection === 'asc' ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
            class="w-4 h-4"
          />
          <UIcon 
            v-else
            name="i-heroicons-chevron-up-down"
            class="w-4 h-4 text-gray-300"
          />
        </button>
        <span v-else class="font-semibold">{{ col.label }}</span>
      </template>
    </UTable>

    <!-- Pagination & Info Row -->
    <div v-if="paginated && filteredRows.length > 0" class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <!-- Info -->
      <div class="text-sm text-gray-500">
        Showing {{ startIndex + 1 }} to {{ endIndex }} of {{ filteredRows.length }} entries
        <span v-if="searchQuery">(filtered from {{ rows.length }} total)</span>
      </div>
      
      <!-- Pagination -->
      <UPagination
        v-model="currentPage"
        :page-count="currentPageSize"
        :total="filteredRows.length"
        :ui="{ rounded: 'first:rounded-l-md last:rounded-r-md' }"
      />
    </div>

    <!-- Empty State -->
    <div v-if="!loading && filteredRows.length === 0" class="text-center py-8 text-gray-500">
      <UIcon name="i-heroicons-document-magnifying-glass" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p v-if="searchQuery">No results found for "{{ searchQuery }}"</p>
      <p v-else>{{ emptyText }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Column {
  key: string
  label: string
  sortable?: boolean
  searchable?: boolean
}

interface Props {
  columns: Column[]
  rows: any[]
  loading?: boolean
  searchable?: boolean
  sortable?: boolean
  paginated?: boolean
  pageSize?: number
  searchPlaceholder?: string
  emptyText?: string
  searchFields?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchable: true,
  sortable: true,
  paginated: true,
  pageSize: 10,
  searchPlaceholder: 'Search...',
  emptyText: 'No data available',
  searchFields: () => []
})

const emit = defineEmits(['select'])

// Search
const searchQuery = ref('')
const searchDebounce = ref<NodeJS.Timeout>()

// Sorting
const sortColumn = ref<string>('')
const sortDirection = ref<'asc' | 'desc'>('asc')

// Pagination
const currentPage = ref(1)
const currentPageSize = ref(props.pageSize)
const pageSizeOptions = [10, 25, 50, 100]

// Computed: Columns with sort indicator
const sortableColumns = computed(() => {
  return props.columns.map(col => ({
    ...col,
    sortable: col.sortable !== false
  }))
})

// Computed: Search fields to use
const effectiveSearchFields = computed(() => {
  if (props.searchFields.length > 0) {
    return props.searchFields
  }
  // Default: search all string columns
  return props.columns
    .filter(col => col.searchable !== false && col.key !== 'actions')
    .map(col => col.key)
})

// Computed: Filtered rows by search
const filteredRows = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.rows
  }
  
  const query = searchQuery.value.toLowerCase()
  return props.rows.filter(row => {
    return effectiveSearchFields.value.some(field => {
      const value = getNestedValue(row, field)
      return value && String(value).toLowerCase().includes(query)
    })
  })
})

// Computed: Sorted rows
const sortedRows = computed(() => {
  if (!sortColumn.value) {
    return filteredRows.value
  }
  
  return [...filteredRows.value].sort((a, b) => {
    const aVal = getNestedValue(a, sortColumn.value)
    const bVal = getNestedValue(b, sortColumn.value)
    
    if (aVal === bVal) return 0
    if (aVal === null || aVal === undefined) return 1
    if (bVal === null || bVal === undefined) return -1
    
    const comparison = aVal < bVal ? -1 : 1
    return sortDirection.value === 'asc' ? comparison : -comparison
  })
})

// Computed: Paginated rows
const startIndex = computed(() => (currentPage.value - 1) * currentPageSize.value)
const endIndex = computed(() => Math.min(startIndex.value + currentPageSize.value, filteredRows.value.length))

const paginatedRows = computed(() => {
  if (!props.paginated) {
    return sortedRows.value
  }
  return sortedRows.value.slice(startIndex.value, endIndex.value)
})

// Methods
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((acc, part) => acc?.[part], obj)
}

const onSearch = () => {
  clearTimeout(searchDebounce.value)
  searchDebounce.value = setTimeout(() => {
    currentPage.value = 1 // Reset to first page on search
  }, 300)
}

const toggleSort = (column: string) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}

const onPageSizeChange = () => {
  currentPage.value = 1 // Reset to first page on page size change
}

// Watch for external row changes
watch(() => props.rows, () => {
  currentPage.value = 1
})
</script>
