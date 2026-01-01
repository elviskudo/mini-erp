<template>
  <div class="space-y-4">
    <!-- Search and filters -->
    <div class="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
      <UInput
        v-model="searchQuery"
        icon="i-heroicons-magnifying-glass"
        :placeholder="searchPlaceholder"
        class="w-full sm:w-64"
      />
      <slot name="filters" />
    </div>

    <!-- Table -->
    <UTable
      :columns="sortableColumns"
      :rows="paginatedRows"
      :loading="loading"
      @select="$emit('select', $event)"
    >
      <template v-for="(_, slot) in $slots" #[slot]="scope">
        <slot :name="slot" v-bind="scope" />
      </template>
    </UTable>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-sm text-gray-500">
        Showing {{ startIndex + 1 }} to {{ Math.min(endIndex, filteredRows.length) }} of {{ filteredRows.length }} results
      </p>
      <UPagination
        v-model="currentPage"
        :page-count="pageSize"
        :total="filteredRows.length"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Column {
  key: string
  label: string
  sortable?: boolean
}

interface Props {
  columns: Column[]
  rows: any[]
  loading?: boolean
  searchPlaceholder?: string
  pageSize?: number
  searchKeys?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchPlaceholder: 'Search...',
  pageSize: 10,
  searchKeys: () => ['name', 'code', 'email', 'title']
})

defineEmits(['select'])

const searchQuery = ref('')
const currentPage = ref(1)
const sortColumn = ref('')
const sortDirection = ref<'asc' | 'desc'>('asc')

// Make columns sortable by default
const sortableColumns = computed(() => {
  return props.columns.map(col => ({
    ...col,
    sortable: col.sortable !== false
  }))
})

// Filter rows based on search
const filteredRows = computed(() => {
  if (!searchQuery.value) return props.rows
  
  const query = searchQuery.value.toLowerCase()
  return props.rows.filter(row => {
    return props.searchKeys.some(key => {
      const value = row[key]
      if (typeof value === 'string') {
        return value.toLowerCase().includes(query)
      }
      if (typeof value === 'number') {
        return value.toString().includes(query)
      }
      return false
    })
  })
})

// Sort rows
const sortedRows = computed(() => {
  if (!sortColumn.value) return filteredRows.value
  
  return [...filteredRows.value].sort((a, b) => {
    const aVal = a[sortColumn.value]
    const bVal = b[sortColumn.value]
    
    if (aVal === bVal) return 0
    if (aVal === null || aVal === undefined) return 1
    if (bVal === null || bVal === undefined) return -1
    
    const comparison = aVal < bVal ? -1 : 1
    return sortDirection.value === 'asc' ? comparison : -comparison
  })
})

// Pagination
const totalPages = computed(() => Math.ceil(filteredRows.value.length / props.pageSize))
const startIndex = computed(() => (currentPage.value - 1) * props.pageSize)
const endIndex = computed(() => startIndex.value + props.pageSize)

const paginatedRows = computed(() => {
  return sortedRows.value.slice(startIndex.value, endIndex.value)
})

// Reset to page 1 when search changes
watch(searchQuery, () => {
  currentPage.value = 1
})
</script>
