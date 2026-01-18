<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Categories</h2>
        <p class="text-gray-500">Manage product categories for organization and filtering</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchCategories">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Category</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ categories.length }}</p>
          <p class="text-sm text-gray-500">Total Categories</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ activeCount }}</p>
          <p class="text-sm text-gray-500">Active</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-gray-600">{{ inactiveCount }}</p>
          <p class="text-sm text-gray-500">Inactive</p>
        </div>
      </UCard>
    </div>

    <!-- Data Table -->
    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="categories" 
        :loading="loading"
        searchable
        :search-keys="['name', 'description']"
        empty-message="No categories yet. Add a new category to organize your products."
      >
        <template #name-data="{ row }">
          <div class="flex items-center gap-3">
            <div v-if="row.image_url" class="w-10 h-10 rounded-lg overflow-hidden bg-gray-100">
              <img :src="row.image_url" :alt="row.name" class="w-full h-full object-cover" />
            </div>
            <div v-else class="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
              <UIcon name="i-heroicons-folder" class="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <p class="font-medium">{{ row.name }}</p>
              <p v-if="row.description" class="text-xs text-gray-400 truncate max-w-xs">{{ row.description }}</p>
            </div>
          </div>
        </template>
        
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">
            {{ row.is_active ? 'Active' : 'Inactive' }}
          </UBadge>
        </template>
        
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="editCategory(row)" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEdit ? 'Edit Category' : 'Add Category'"
      :loading="saving"
      @submit="saveCategory"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create categories to organize your products.</p>
        
        <UFormGroup label="Category Name" required hint="Display name for this category">
          <UInput v-model="form.name" placeholder="e.g., Electronics, Beverages, Food" />
        </UFormGroup>

        <UFormGroup label="Description" hint="Brief description of products in this category">
          <UTextarea v-model="form.description" rows="3" placeholder="Describe the types of products..." />
        </UFormGroup>

        <UFormGroup label="Image URL" hint="Optional image URL for the category">
          <UInput v-model="form.image_url" placeholder="https://example.com/image.jpg" />
        </UFormGroup>

        <UFormGroup hint="Active categories appear in POS and product selection">
          <UCheckbox v-model="form.is_active" label="Active" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const isEdit = ref(false)
const editId = ref('')

const categories = ref<any[]>([])

const form = reactive({
  name: '',
  description: '',
  image_url: '',
  is_active: true
})

const columns = [
  { key: 'name', label: 'Category', sortable: true },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const activeCount = computed(() => categories.value.filter((c: any) => c.is_active).length)
const inactiveCount = computed(() => categories.value.filter((c: any) => !c.is_active).length)

// Helper to safely extract array from various API response formats
const extractArray = (response: any): any[] => {
  if (!response) return []
  if (Array.isArray(response)) return response
  if (response.data && Array.isArray(response.data)) return response.data
  if (response.data?.data && Array.isArray(response.data.data)) return response.data.data
  if (typeof response === 'object' && response.data) {
    const d = response.data
    if (Array.isArray(d)) return d
    if (d.data && Array.isArray(d.data)) return d.data
  }
  return []
}

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await $api.get('/manufacturing/categories')
    categories.value = extractArray(res)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to load', color: 'red' })
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.name = ''
  form.description = ''
  form.image_url = ''
  form.is_active = true
  isEdit.value = false
  editId.value = ''
}

const openCreate = () => {
  resetForm()
  isOpen.value = true
}

const editCategory = (category: any) => {
  isEdit.value = true
  editId.value = category.id
  form.name = category.name
  form.description = category.description || ''
  form.image_url = category.image_url || ''
  form.is_active = category.is_active
  isOpen.value = true
}

const saveCategory = async () => {
  if (!form.name.trim()) {
    toast.add({ title: 'Error', description: 'Name is required', color: 'red' })
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await $api.put(`/manufacturing/categories/${editId.value}`, form)
      toast.add({ title: 'Updated', description: 'Category updated', color: 'green' })
    } else {
      await $api.post('/manufacturing/categories', form)
      toast.add({ title: 'Created', description: 'Category created', color: 'green' })
    }
    isOpen.value = false
    fetchCategories()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const confirmDelete = async (category: any) => {
  if (!confirm(`Delete "${category.name}"?\n\nThis action cannot be undone.`)) return
  
  try {
    await $api.delete(`/manufacturing/categories/${category.id}`)
    toast.add({ title: 'Deleted', description: 'Category deleted', color: 'green' })
    fetchCategories()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to delete', color: 'red' })
  }
}

onMounted(() => fetchCategories())
</script>
