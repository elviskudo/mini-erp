<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Page Builder</h1>
        <p class="text-gray-500">Create and manage landing pages</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="createNew">New Page</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="pages" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #slug-data="{ row }">
          <code class="text-xs bg-gray-100 px-2 py-1 rounded">/p/{{ row.slug }}</code>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'published' ? 'green' : 'gray'" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #updated_at-data="{ row }">
          <span class="text-sm text-gray-500">{{ formatDate(row.updated_at) }}</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="editPage(row)" />
            <UButton icon="i-heroicons-eye" color="blue" variant="ghost" size="xs" @click="previewPage(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="deletePage(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const router = useRouter()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const pages = ref<any[]>([])
const pagination = ref(null)

const columns = [
    { key: 'title', label: 'Title', sortable: true },
    { key: 'slug', label: 'URL' },
    { key: 'status', label: 'Status' },
    { key: 'updated_at', label: 'Last Updated' },
    { key: 'actions', label: '' }
]

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'

const fetchPages = () => {
    // Load from localStorage
    const stored = localStorage.getItem('pageBuilder_pages')
    if (stored) {
        pages.value = JSON.parse(stored)
    } else {
        pages.value = []
    }
}

const handlePageChange = () => fetchPages()

const createNew = () => {
    const id = Date.now().toString(36)
    router.push(`/crm/marketing/pages/${id}`)
}

const editPage = (row: any) => {
    router.push(`/crm/marketing/pages/${row.id}`)
}

const previewPage = (row: any) => {
    window.open(`/preview/page/${row.id}`, '_blank')
}

const deletePage = (row: any) => {
    if (!confirm(`Delete "${row.title}"?`)) return
    pages.value = pages.value.filter(p => p.id !== row.id)
    localStorage.setItem('pageBuilder_pages', JSON.stringify(pages.value))
    toast.add({ title: 'Deleted', description: 'Page deleted' })
}

onMounted(() => fetchPages())
</script>
