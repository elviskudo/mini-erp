<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Purchase Requests</h2>
        <p class="text-gray-500">Manage purchase requisitions</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreateModal">Create Request</UButton>
    </div>

    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="prs" :loading="loading">
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
         <template #actions-data="{ row }">
             <div class="flex gap-2">
                 <UButton v-if="row.status === 'Draft'" size="xs" color="green" variant="soft" @click="approvePr(row.id)">Approve</UButton>
                 <UButton v-if="row.status === 'Approved'" size="xs" color="blue" variant="soft" @click="openConvertModal(row)">Convert to PO</UButton>
             </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create PR Slideover - 1/3 page width -->
    <USlideover v-model="isCreateOpen" :ui="{ width: 'w-screen max-w-xl' }">
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <h3 class="text-lg font-semibold">New Purchase Request</h3>
          <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="isCreateOpen = false" />
        </div>
        
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-4">
            <div class="space-y-3">
              <div v-for="(item, index) in form.items" :key="index" class="flex gap-3 items-end p-4 bg-gray-50 rounded-lg">
                <UFormGroup label="Product" class="flex-1">
                  <USelect v-model="item.product_id" :options="products" option-attribute="name" value-attribute="id" placeholder="Select Product" />
                </UFormGroup>
                <UFormGroup label="Qty" class="w-24">
                  <UInput v-model="item.quantity" type="number" min="1" />
                </UFormGroup>
                <UButton 
                  icon="i-heroicons-trash" 
                  color="red" 
                  variant="ghost" 
                  class="mb-0.5"
                  :disabled="form.items.length === 1"
                  @click="removeItem(index)" 
                />
              </div>
            </div>
            
            <UButton size="sm" icon="i-heroicons-plus" variant="soft" @click="addItem">Add Item</UButton>
          </div>
        </div>
        
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50">
          <UButton variant="ghost" @click="isCreateOpen = false">Cancel</UButton>
          <UButton :loading="submitting" @click="createPr">Submit Request</UButton>
        </div>
      </div>
    </USlideover>

    <!-- Convert to PO Slideover -->
    <USlideover v-model="isConvertOpen" :ui="{ width: 'w-screen max-w-md' }">
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <h3 class="text-lg font-semibold">Convert PR to PO</h3>
          <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="isConvertOpen = false" />
        </div>
        
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <UFormGroup label="Select Vendor" required>
            <USelect v-model="convertForm.vendor_id" :options="vendors" option-attribute="name" value-attribute="id" placeholder="Choose vendor" />
          </UFormGroup>
          
          <div v-if="selectedPr" class="border-t pt-4">
            <p class="text-sm font-medium mb-3">Set Unit Prices</p>
            <div class="space-y-3">
              <div v-for="item in selectedPr.items" :key="item.id" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p class="font-medium">{{ item.product?.name }}</p>
                  <p class="text-sm text-gray-500">Qty: {{ item.quantity }}</p>
                </div>
                <UInput v-model="convertForm.price_map[item.product_id]" type="number" placeholder="Price" class="w-28" />
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50">
          <UButton variant="ghost" @click="isConvertOpen = false">Cancel</UButton>
          <UButton :loading="submitting" @click="convertToPo">Generate PO</UButton>
        </div>
      </div>
    </USlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const toast = useToast()
const isCreateOpen = ref(false)
const isConvertOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)

const prs = ref<any[]>([])
const products = ref<any[]>([])
const vendors = ref<any[]>([])

const selectedPr = ref<any>(null)

const columns = [
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'id', label: 'ID' },
  { key: 'actions', label: '' }
]

const form = reactive({
    items: [] as any[]
})

const convertForm = reactive({
    vendor_id: '',
    price_map: {} as Record<string, number>
})

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Draft': return 'gray'
        case 'Approved': return 'blue'
        case 'Converted': return 'green'
        case 'Rejected': return 'red'
        default: return 'primary'
    }
}

const fetchData = async () => {
    loading.value = true
    try {
        const [prRes, prodRes, vendRes]: any = await Promise.all([
            $fetch('/api/procurement/pr'),
            $fetch('/api/manufacturing/products'),
            $fetch('/api/procurement/vendors')
        ])
        prs.value = prRes
        products.value = prodRes
        vendors.value = vendRes
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const openCreateModal = () => {
    form.items = [{ product_id: '', quantity: 1 }]
    isCreateOpen.value = true
}

const addItem = () => form.items.push({ product_id: '', quantity: 1 })
const removeItem = (idx: number) => form.items.splice(idx, 1)

const createPr = async () => {
    submitting.value = true
    try {
        await $fetch('/api/procurement/pr', {
            method: 'POST',
            body: form
        })
        toast.add({ title: 'Success', description: 'Purchase request created.' })
        isCreateOpen.value = false
        fetchData()
    } catch (e) { 
        toast.add({ title: 'Error', description: 'Failed to create request.', color: 'red' })
    }
    finally { submitting.value = false }
}

const approvePr = async (id: string) => {
    if(!confirm('Approve this request?')) return
    try {
        await $fetch(`/api/procurement/pr/${id}/approve`, { method: 'POST' })
        toast.add({ title: 'Approved', description: 'Request approved.' })
        fetchData()
    } catch (e) { 
        toast.add({ title: 'Error', description: 'Failed to approve.', color: 'red' })
    }
}

const openConvertModal = (pr: any) => {
    selectedPr.value = pr
    convertForm.vendor_id = ''
    convertForm.price_map = {}
    isConvertOpen.value = true
}

const convertToPo = async () => {
    if (!selectedPr.value) return
    submitting.value = true
    try {
        const payload = {
            pr_id: selectedPr.value.id,
            vendor_id: convertForm.vendor_id,
            price_map: convertForm.price_map
        }
        await $fetch('/api/procurement/po/create_from_pr', {
            method: 'POST',
            body: payload
        })
        toast.add({ title: 'Success', description: 'PO Created!' })
        isConvertOpen.value = false
        fetchData()
        navigateTo('/procurement/orders')
    } catch (e) { 
        toast.add({ title: 'Error', description: 'Failed to convert.', color: 'red' })
    }
    finally { submitting.value = false }
}

onMounted(() => {
    fetchData()
})
</script>
