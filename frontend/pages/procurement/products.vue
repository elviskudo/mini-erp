<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Product Catalog</h2>
        <p class="text-gray-500">Manage purchasable products with vendor pricing and lead times</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
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
      :title="editMode ? 'Edit Product' : 'Add New Product'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Fill in the product details below. Products can be linked to vendors for pricing.</p>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Product Code" required hint="Unique identifier for this product (e.g., RM-001, FG-050)" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="e.g. RM-001" />
          </UFormGroup>
          <UFormGroup label="Product Type" required hint="Classification of the product" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.type" :options="typeOptions" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Product Name" required hint="Full descriptive name of the product" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g. Raw Sugar Grade A" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Detailed description, specifications, or notes about the product" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="3" placeholder="Enter product specifications, quality requirements, or other details..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Standard Cost (Rp)" hint="Base purchase price per unit before vendor-specific pricing" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.standard_cost" type="number" placeholder="0" />
          </UFormGroup>
          <UFormGroup label="Unit of Measure (UoM)" hint="How the product is measured (kg, pcs, liter, etc.)" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.uom" :options="uomOptions" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Minimum Order Qty" hint="Minimum quantity for purchase orders" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.min_order_qty" type="number" placeholder="1" />
          </UFormGroup>
          <UFormGroup label="Reorder Point" hint="Stock level that triggers reorder alert" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.reorder_point" type="number" placeholder="0" />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>

    <!-- Vendor Link Modal -->
    <UModal v-model="showVendorModal" :ui="{ width: 'max-w-xl' }">
      <UCard v-if="selectedProduct">
        <template #header>
          <div>
            <h3 class="font-semibold">Link Vendor to Product</h3>
            <p class="text-sm text-gray-500">{{ selectedProduct.code }} - {{ selectedProduct.name }}</p>
          </div>
        </template>
        <div class="space-y-4">
          <p class="text-sm text-gray-500 pb-2 border-b">Link this product to a vendor with agreed pricing and delivery terms.</p>
          
          <UFormGroup label="Vendor" required hint="Select the supplier for this product" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="vendorLinkForm.vendor_id" :options="vendorOptions" placeholder="Choose vendor..." />
          </UFormGroup>
          
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Agreed Price (Rp)" hint="Contracted price per unit from this vendor" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="vendorLinkForm.agreed_price" type="number" placeholder="0" />
            </UFormGroup>
            <UFormGroup label="Lead Time (days)" hint="Days from order to delivery" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="vendorLinkForm.lead_time_days" type="number" placeholder="7" />
            </UFormGroup>
          </div>
          
          <UFormGroup label="Minimum Order Quantity" hint="Minimum quantity vendor accepts per order" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="vendorLinkForm.min_order_qty" type="number" placeholder="1" />
          </UFormGroup>
          
          <UCheckbox v-model="vendorLinkForm.is_preferred" label="Set as Preferred Vendor" help="Preferred vendor will be suggested first when creating purchase orders" />
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
  { label: 'Work in Progress (WIP)', value: 'WIP' },
  { label: 'Finished Goods', value: 'Finished Goods' },
  { label: 'Packaging', value: 'Packaging' },
  { label: 'Consumables', value: 'Consumables' }
]

const uomOptions = [
  { label: 'Pieces (pcs)', value: 'pcs' },
  { label: 'Kilogram (kg)', value: 'kg' },
  { label: 'Gram (g)', value: 'g' },
  { label: 'Liter (L)', value: 'L' },
  { label: 'Milliliter (mL)', value: 'mL' },
  { label: 'Meter (m)', value: 'm' },
  { label: 'Box', value: 'box' },
  { label: 'Carton', value: 'carton' },
  { label: 'Pack', value: 'pack' },
  { label: 'Roll', value: 'roll' }
]

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  id: '',
  code: '',
  name: '',
  description: '',
  type: 'Raw Material',
  standard_cost: 0,
  uom: 'pcs',
  min_order_qty: 1,
  reorder_point: 0
})

const vendorLinkForm = reactive({
  vendor_id: '',
  agreed_price: 0,
  lead_time_days: 7,
  min_order_qty: 1,
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
  Object.assign(form, { id: '', code: '', name: '', description: '', type: 'Raw Material', standard_cost: 0, uom: 'pcs', min_order_qty: 1, reorder_point: 0 })
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
  Object.assign(vendorLinkForm, { vendor_id: '', agreed_price: 0, lead_time_days: 7, min_order_qty: 1, is_preferred: false })
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

const exportData = (format: string) => {
  const data = products.value.map(p => ({
    'Code': p.code,
    'Name': p.name,
    'Type': p.type,
    'UoM': p.uom,
    'Standard Cost': p.standard_cost || 0,
    'Description': p.description || ''
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map(row => headers.map(h => `"${row[h as keyof typeof row] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `product_catalog.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Product catalog exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    // For PDF, we'll open print dialog
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Product Catalog</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Product Catalog</h1>
        <p>Exported: ${new Date().toLocaleDateString()}</p>
        <table><tr>${Object.keys(data[0] || {}).map(h => `<th>${h}</th>`).join('')}</tr>
        ${data.map(row => `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}
        </table></body></html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }
}

onMounted(() => { fetchData() })
</script>
