<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Product Catalog</h2>
        <p class="text-gray-500">Manage purchasable products with vendor pricing</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Product</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ products.length }}</p>
          <p class="text-sm text-gray-500">Total Products</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ activeProducts }}</p>
          <p class="text-sm text-gray-500">Raw Materials</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-purple-600">{{ finishedGoods }}</p>
          <p class="text-sm text-gray-500">Finished Goods</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ withVendors }}</p>
          <p class="text-sm text-gray-500">With Vendors</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="products" 
        :loading="loading"
        searchable
        :search-keys="['code', 'name', 'type']"
        empty-message="No products found. Add products to the catalog."
      >
        <template #code-data="{ row }">
          <span class="font-mono font-medium">{{ row.code }}</span>
        </template>
        <template #type-data="{ row }">
          <UBadge :color="row.type === 'Raw Material' ? 'blue' : row.type === 'Finished Goods' ? 'green' : 'gray'" variant="subtle">
            {{ row.type }}
          </UBadge>
        </template>
        <template #standard_cost-data="{ row }">
          Rp {{ formatNumber(row.standard_cost || 0) }}
        </template>
        <template #vendors-data="{ row }">
          <span v-if="row.vendor_count > 0" class="text-blue-600">{{ row.vendor_count }} vendors</span>
          <span v-else class="text-gray-400">No vendors</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UButton icon="i-heroicons-link" size="xs" color="blue" variant="ghost" @click="openVendorLink(row)" title="Link Vendors" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Modal -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Product' : 'Add Product'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Product Code" required>
            <UInput v-model="form.code" placeholder="e.g. RM-001" />
          </UFormGroup>
          <UFormGroup label="Type" required>
            <USelect v-model="form.type" :options="typeOptions" />
          </UFormGroup>
        </div>
        <UFormGroup label="Product Name" required>
          <UInput v-model="form.name" placeholder="e.g. Raw Sugar" />
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="form.description" rows="2" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Standard Cost (Rp)">
            <UInput v-model.number="form.standard_cost" type="number" />
          </UFormGroup>
          <UFormGroup label="UoM">
            <UInput v-model="form.uom" placeholder="e.g. kg, pcs" />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>

    <!-- Vendor Link Modal -->
    <UModal v-model="showVendorModal" :ui="{ width: 'max-w-xl' }">
      <UCard v-if="selectedProduct">
        <template #header>
          <h3 class="font-semibold">Link Vendors - {{ selectedProduct.name }}</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Select Vendor">
            <USelect v-model="vendorLinkForm.vendor_id" :options="vendorOptions" placeholder="Choose vendor..." />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Agreed Price (Rp)">
              <UInput v-model.number="vendorLinkForm.agreed_price" type="number" />
            </UFormGroup>
            <UFormGroup label="Lead Time (days)">
              <UInput v-model.number="vendorLinkForm.lead_time_days" type="number" />
            </UFormGroup>
          </div>
          <UCheckbox v-model="vendorLinkForm.is_preferred" label="Preferred Vendor" />
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showVendorModal = false">Cancel</UButton>
            <UButton @click="saveVendorLink" :loading="submitting">Link Vendor</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)
const editMode = ref(false)
const showVendorModal = ref(false)

const products = ref<any[]>([])
const vendors = ref<any[]>([])
const selectedProduct = ref<any>(null)

const columns = [
  { key: 'code', label: 'Code', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'type', label: 'Type' },
  { key: 'uom', label: 'UoM' },
  { key: 'standard_cost', label: 'Std Cost' },
  { key: 'vendors', label: 'Vendors' },
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
  standard_cost: 0,
  uom: 'pcs'
})

const vendorLinkForm = reactive({
  vendor_id: '',
  agreed_price: 0,
  lead_time_days: 7,
  is_preferred: false
})

const activeProducts = computed(() => products.value.filter(p => p.type === 'Raw Material').length)
const finishedGoods = computed(() => products.value.filter(p => p.type === 'Finished Goods').length)
const withVendors = computed(() => products.value.filter(p => p.vendor_count > 0).length)
const vendorOptions = computed(() => vendors.value.map(v => ({ label: v.name, value: v.id })))

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num)

const fetchData = async () => {
  loading.value = true
  try {
    const [productsRes, vendorsRes] = await Promise.all([
      $api.get('/manufacturing/products'),
      $api.get('/procurement/vendors')
    ])
    products.value = productsRes.data || []
    vendors.value = vendorsRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { id: '', code: '', name: '', description: '', type: 'Raw Material', standard_cost: 0, uom: 'pcs' })
  editMode.value = false
  isOpen.value = true
}

const openEdit = (row: any) => {
  Object.assign(form, row)
  editMode.value = true
  isOpen.value = true
}

const openVendorLink = (row: any) => {
  selectedProduct.value = row
  Object.assign(vendorLinkForm, { vendor_id: '', agreed_price: 0, lead_time_days: 7, is_preferred: false })
  showVendorModal.value = true
}

const save = async () => {
  submitting.value = true
  try {
    if (editMode.value) {
      await $api.put(`/manufacturing/products/${form.id}`, form)
    } else {
      await $api.post('/manufacturing/products', form)
    }
    toast.add({ title: 'Success', description: editMode.value ? 'Product updated' : 'Product created', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const saveVendorLink = async () => {
  if (!selectedProduct.value || !vendorLinkForm.vendor_id) return
  submitting.value = true
  try {
    await $api.post('/procurement/supplier-items', {
      product_id: selectedProduct.value.id,
      ...vendorLinkForm
    })
    toast.add({ title: 'Linked', description: 'Vendor linked to product', color: 'green' })
    showVendorModal.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => { fetchData() })
</script>
