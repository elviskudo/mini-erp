<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Products & BOM</h2>
        <p class="text-gray-500">Manage products and bill of materials</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Add Product</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable 
        :columns="columns" 
        :rows="products" 
        :loading="loading"
        search-placeholder="Search products..."
      >
        <template #image-data="{ row }">
          <div class="w-12 h-12 bg-gray-100 rounded overflow-hidden">
            <img v-if="row.image_url" :src="row.image_url" alt="" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              <UIcon name="i-heroicons-photo" class="w-5 h-5" />
            </div>
          </div>
        </template>
        <template #type-data="{ row }">
          <UBadge :color="getTypeColor(row.type)" variant="subtle">{{ row.type }}</UBadge>
        </template>
        <template #barcode-data="{ row }">
          <ClientOnly>
            <Barcode v-if="row.code" :value="row.code" :height="30" :display-value="false" />
          </ClientOnly>
        </template>
        <template #qrcode-data="{ row }">
          <ClientOnly>
            <QRCode v-if="row.code" :value="row.code" :size="40" />
          </ClientOnly>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Product' : 'Add Product'"
      :loading="submitting"
      @submit="saveProduct"
    >
      <div class="space-y-4">
        <UFormGroup label="Product Code" required hint="Unique SKU for inventory tracking" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.code" placeholder="e.g. PRD-001" />
        </UFormGroup>
        
        <UFormGroup label="Product Name" required hint="Display name for this product" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g. Steel Bar" />
        </UFormGroup>

        <UFormGroup label="Description" hint="Detailed product information" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" placeholder="Product description..." rows="2" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Type" required hint="Product category" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.type" :options="typeOptions" />
          </UFormGroup>
          <UFormGroup label="Unit of Measure" hint="Default unit for stock" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.uom" placeholder="e.g. PCS, KG, L" />
          </UFormGroup>
        </div>

        <!-- Product Origin -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup>
            <UCheckbox v-model="form.is_manufactured" label="Manufactured Product" />
            <p class="text-xs text-gray-400 mt-1">Check if produced in-house</p>
          </UFormGroup>
          <UFormGroup>
            <UCheckbox v-model="form.requires_cold_chain" label="Cold Chain Required" />
            <p class="text-xs text-gray-400 mt-1">Needs temperature control</p>
          </UFormGroup>
        </div>

        <!-- Cold Chain Temperature (conditional) -->
        <div v-if="form.requires_cold_chain" class="border border-blue-200 rounded-lg p-3 bg-blue-50">
          <UFormGroup label="Max Storage Temperature (°C)" required hint="Maximum allowed storage temp" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.max_storage_temp" type="number" step="0.1" placeholder="e.g. 8" />
          </UFormGroup>
        </div>

        <!-- Margin & Pricing -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Desired Margin (%)" hint="Target profit margin" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.desired_margin" type="number" step="0.01" placeholder="30" />
          </UFormGroup>
          <UFormGroup label="Standard Cost" hint="Base cost for pricing" :ui="{ hint: 'text-xs text-gray-400' }">
            <CurrencyInput v-model="form.standard_cost" :currency="currencyCode" />
          </UFormGroup>
        </div>

        <!-- Image Upload Dropzone -->
        <UFormGroup label="Product Image" hint="Optional product photo" :ui="{ hint: 'text-xs text-gray-400' }">
          <div 
            class="w-full border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors"
            :class="isDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="$refs.imageInput.click()"
          >
            <div v-if="imagePreview" class="flex flex-col items-center gap-3">
              <img :src="imagePreview" alt="Preview" class="w-32 h-32 object-cover rounded-lg" />
              <UButton 
                type="button"
                variant="ghost" 
                color="red"
                size="xs"
                icon="i-heroicons-trash"
                @click.stop="clearImage"
              >
                Remove Image
              </UButton>
            </div>
            <div v-else class="flex flex-col items-center gap-2 text-gray-500">
              <UIcon name="i-heroicons-cloud-arrow-up" class="w-10 h-10" />
              <p class="text-sm">Drag and drop image here, or click to browse</p>
              <p class="text-xs text-gray-400">PNG, JPG up to 2MB</p>
            </div>
          </div>
          <input 
            type="file" 
            accept="image/*" 
            @change="handleImageUpload"
            class="hidden"
            ref="imageInput"
          />
        </UFormGroup>

        <!-- Barcode & QR Code Preview -->
        <div v-if="form.code" class="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h4 class="text-sm font-medium text-gray-700 mb-3">Barcode & QR Code Preview</h4>
          <div class="flex items-center gap-6">
            <div class="text-center">
              <ClientOnly>
                <Barcode :value="form.code" :height="50" />
                <template #fallback>
                  <div class="h-16 bg-gray-100 rounded animate-pulse"></div>
                </template>
              </ClientOnly>
            </div>
            <div class="text-center">
              <ClientOnly>
                <QRCode :value="form.code" :size="80" />
                <template #fallback>
                  <div class="w-20 h-20 bg-gray-100 rounded animate-pulse"></div>
                </template>
              </ClientOnly>
            </div>
          </div>
        </div>

        <!-- BOM Section (Only for non-Raw Material items) -->
        <div v-if="form.type !== 'Raw Material'" class="border-t border-gray-200 pt-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-900">Bill of Materials</h4>
            <UButton size="xs" icon="i-heroicons-plus" variant="soft" @click="addBomItem">Add Component</UButton>
          </div>
          
          <div v-if="form.bom_items.length === 0" class="text-sm text-gray-500 italic py-2">
            No components added yet.
          </div>

          <div v-else class="space-y-2 max-h-60 overflow-y-auto">
            <div v-for="(item, index) in form.bom_items" :key="index" class="flex gap-2 items-end bg-gray-50 p-3 rounded-lg">
              <UFormGroup label="Component" class="flex-1">
                <USelect 
                  v-model="item.component_id" 
                  :options="rawMaterials" 
                  option-attribute="name" 
                  value-attribute="id" 
                  placeholder="Select material" 
                />
              </UFormGroup>
              <UFormGroup label="Qty" class="w-20">
                <UInput v-model="item.quantity" type="number" step="0.001" />
              </UFormGroup>
              <UFormGroup label="Waste %" class="w-20">
                <UInput v-model="item.waste_percentage" type="number" step="0.1" />
              </UFormGroup>
              <UButton 
                icon="i-heroicons-trash" 
                color="red" 
                variant="ghost" 
                class="mb-1"
                @click="removeBomItem(index)" 
              />
            </div>
          </div>
        </div>
      </div>
    </FormSlideover>

    <!-- Delete Confirmation Modal -->
    <UModal v-model="isDeleteModalOpen">
      <UCard>
        <template #header>
          <div class="flex items-center gap-2 text-red-600">
            <UIcon name="i-heroicons-exclamation-triangle" class="w-6 h-6" />
            <span class="font-semibold">Delete Product</span>
          </div>
        </template>
        <p class="text-gray-600">
          Are you sure you want to delete <strong>{{ deleteTarget?.name }}</strong>? This action cannot be undone.
        </p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="gray" variant="outline" @click="isDeleteModalOpen = false">Cancel</UButton>
            <UButton color="red" :loading="deleting" @click="deleteProduct">Delete</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const { currencyCode, formatCurrency } = useCurrency()
const toast = useToast()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const editMode = ref(false)
const products = ref<any[]>([])
const rawMaterials = ref<any[]>([])

// Delete state
const isDeleteModalOpen = ref(false)
const deleteTarget = ref<any>(null)
const deleting = ref(false)

const columns = [
  { key: 'image', label: 'Image', sortable: false },
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Type' },
  { key: 'uom', label: 'Unit' },
  { key: 'barcode', label: 'Barcode', sortable: false },
  { key: 'qrcode', label: 'QR Code', sortable: false },
  { key: 'actions', label: '' }
]

const typeOptions = [
  { label: 'Raw Material', value: 'Raw Material' },
  { label: 'WIP', value: 'WIP' },
  { label: 'Finished Goods', value: 'Finished Goods' }
]

const form = reactive({
  id: '',
  code: '',
  name: '',
  description: '',
  type: 'Raw Material',
  uom: 'pcs',
  image_url: '',
  is_manufactured: true,
  requires_cold_chain: false,
  max_storage_temp: null as number | null,
  desired_margin: 30,
  standard_cost: 0,
  bom_items: [] as any[]
})

const imagePreview = ref<string | null>(null)
const imageFile = ref<File | null>(null)
const isDragging = ref(false)

const resetForm = () => {
  Object.assign(form, {
    id: '',
    code: '',
    name: '',
    description: '',
    type: 'Raw Material',
    uom: 'pcs',
    image_url: '',
    is_manufactured: true,
    requires_cold_chain: false,
    max_storage_temp: null,
    desired_margin: 30,
    standard_cost: 0,
    bom_items: []
  })
  imagePreview.value = null
  imageFile.value = null
  isDragging.value = false
}

const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processImageFile(file)
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    processImageFile(file)
  }
}

const processImageFile = (file: File) => {
  if (file.size > 2 * 1024 * 1024) {
    toast.add({ title: 'Error', description: 'Image size must be less than 2MB', color: 'red' })
    return
  }
  imageFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target?.result as string
    form.image_url = imagePreview.value || '' // Store as base64 for now
  }
  reader.readAsDataURL(file)
}

const clearImage = () => {
  imagePreview.value = null
  imageFile.value = null
  form.image_url = ''
}

const getTypeColor = (type: string) => {
  switch(type) {
    case 'Raw Material': return 'gray'
    case 'WIP': return 'orange'
    case 'Finished Goods': return 'green'
    default: return 'primary'
  }
}

const fetchProducts = async () => {
  loading.value = true
  try {
    const res: any = await $fetch('/api/manufacturing/products', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    products.value = res
    // Filter for raw materials for BOM dropdown
    rawMaterials.value = res.filter((p: any) => p.type === 'Raw Material' || p.type === 'WIP')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  resetForm()
  editMode.value = false
  isOpen.value = true
}

const openEdit = (row: any) => {
  Object.assign(form, {
    id: row.id,
    code: row.code,
    name: row.name,
    description: row.description || '',
    type: row.type,
    uom: row.uom,
    image_url: row.image_url || '',
    is_manufactured: row.is_manufactured ?? true,
    requires_cold_chain: row.requires_cold_chain ?? false,
    max_storage_temp: row.max_storage_temp || null,
    desired_margin: (row.desired_margin || 0.3) * 100, // Convert decimal to percentage
    standard_cost: row.standard_cost || 0,
    bom_items: row.bom_items || []
  })
  // Set image preview if exists
  if (row.image_url) {
    imagePreview.value = row.image_url
  }
  editMode.value = true
  isOpen.value = true
}

const addBomItem = () => {
  form.bom_items.push({
    component_id: '',
    quantity: 1,
    waste_percentage: 0
  })
}

const removeBomItem = (index: number) => {
  form.bom_items.splice(index, 1)
}

const saveProduct = async () => {
  // Validate cold chain requirement
  if (form.requires_cold_chain && !form.max_storage_temp) {
    toast.add({ title: 'Error', description: 'Max Storage Temperature is required for cold chain products', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const payload = {
      code: form.code,
      name: form.name,
      description: form.description,
      type: form.type,
      uom: form.uom,
      image_url: form.image_url,
      is_manufactured: form.is_manufactured,
      requires_cold_chain: form.requires_cold_chain,
      max_storage_temp: form.requires_cold_chain ? form.max_storage_temp : null,
      desired_margin: form.desired_margin / 100, // Convert percentage to decimal
      standard_cost: form.standard_cost
    }
    
    if (editMode.value) {
      await $fetch(`/api/manufacturing/products/${form.id}`, {
        method: 'PUT',
        body: payload,
        headers
      })
      toast.add({ title: 'Updated', description: 'Product updated successfully.' })
    } else {
      await $fetch('/api/manufacturing/products', {
        method: 'POST',
        body: payload,
        headers
      })
      toast.add({ title: 'Created', description: 'Product created successfully.' })
    }
    
    isOpen.value = false
    fetchProducts()
    resetForm()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to save product.', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const confirmDelete = (row: any) => {
  deleteTarget.value = row
  isDeleteModalOpen.value = true
}

const deleteProduct = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await $fetch(`/api/manufacturing/products/${deleteTarget.value.id}`, { 
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    toast.add({ title: 'Deleted', description: 'Product deleted successfully.', color: 'green' })
    fetchProducts()
    isDeleteModalOpen.value = false
    deleteTarget.value = null
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to delete product.', color: 'red' })
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  fetchProducts()
})
</script>
