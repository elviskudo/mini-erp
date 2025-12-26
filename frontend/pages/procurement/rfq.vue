<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Request for Quotation</h2>
        <p class="text-gray-500">Request price quotes from multiple vendors</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New RFQ</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ rfqs.length }}</p>
          <p class="text-sm text-gray-500">Total RFQs</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ draftCount }}</p>
          <p class="text-sm text-gray-500">Draft</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ sentCount }}</p>
          <p class="text-sm text-gray-500">Sent</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ receivedCount }}</p>
          <p class="text-sm text-gray-500">Quotes Received</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="rfqs" 
        :loading="loading"
        searchable
        :search-keys="['rfq_number']"
        empty-message="No RFQs yet. Create one to request quotes from vendors."
      >
        <template #rfq_number-data="{ row }">
          <span class="font-mono font-medium text-blue-600">{{ row.rfq_number }}</span>
        </template>
        <template #deadline-data="{ row }">
          <span v-if="row.deadline" :class="isOverdue(row.deadline) ? 'text-red-600' : ''">
            {{ formatDate(row.deadline) }}
          </span>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #vendors_count-data="{ row }">
          {{ row.vendors_count || 0 }} vendors
        </template>
        <template #items_count-data="{ row }">
          {{ row.items_count || 0 }} items
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status === 'Draft'" icon="i-heroicons-paper-airplane" size="xs" color="blue" variant="ghost" @click="sendRFQ(row)" title="Send to Vendors" />
            <UButton v-if="row.status === 'Received'" icon="i-heroicons-check-circle" size="xs" color="green" variant="ghost" @click="selectVendor(row)" title="Select Vendor" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create RFQ Modal -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create RFQ"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <UFormGroup label="Deadline" hint="Quote submission deadline" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.deadline" type="date" />
        </UFormGroup>
        
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="2" placeholder="Requirements or specifications..." />
        </UFormGroup>
        
        <!-- Items -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium">Request Items</h4>
            <UButton size="xs" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2">
            <USelect v-model="item.product_id" :options="productOptions" placeholder="Product" class="flex-1" size="sm" />
            <UInput v-model.number="item.quantity" type="number" placeholder="Qty" class="w-20" size="sm" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="form.items.splice(idx, 1)" />
          </div>
        </div>
        
        <!-- Vendors -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium">Invite Vendors</h4>
          </div>
          <div class="space-y-2">
            <UCheckbox v-for="v in vendors" :key="v.id" v-model="form.vendor_ids" :value="v.id" :label="v.name" />
          </div>
        </div>
      </div>
    </FormSlideover>

    <!-- Detail Modal -->
    <UModal v-model="showDetailModal" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedRFQ">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedRFQ.rfq_number }}</h3>
              <p class="text-sm text-gray-500">Deadline: {{ formatDate(selectedRFQ.deadline) }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedRFQ.status)" size="lg">{{ selectedRFQ.status }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div>
            <h4 class="font-medium mb-2">Request Items</h4>
            <UTable :columns="[{key:'product',label:'Product'},{key:'quantity',label:'Qty'}]" :rows="selectedRFQ.items || []" />
          </div>
          
          <div class="border-t pt-4">
            <h4 class="font-medium mb-2">Vendor Quotes</h4>
            <div v-for="v in (selectedRFQ.vendors || [])" :key="v.id" class="p-3 border rounded-lg mb-2">
              <div class="flex justify-between items-center">
                <div>
                  <p class="font-medium">{{ v.vendor_name }}</p>
                  <p v-if="v.quoted_amount" class="text-sm text-green-600">Quote: Rp {{ formatNumber(v.quoted_amount) }}</p>
                  <p v-else class="text-sm text-gray-400">Awaiting quote</p>
                </div>
                <UBadge v-if="v.is_selected" color="green">Selected</UBadge>
              </div>
            </div>
          </div>
        </div>
        
        <template #footer>
          <UButton variant="ghost" @click="showDetailModal = false">Close</UButton>
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
const showDetailModal = ref(false)

const rfqs = ref<any[]>([])
const products = ref<any[]>([])
const vendors = ref<any[]>([])
const selectedRFQ = ref<any>(null)

const columns = [
  { key: 'rfq_number', label: 'RFQ #', sortable: true },
  { key: 'deadline', label: 'Deadline', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'items_count', label: 'Items' },
  { key: 'vendors_count', label: 'Vendors' },
  { key: 'actions', label: '' }
]

const form = reactive({
  deadline: '',
  notes: '',
  items: [] as any[],
  vendor_ids: [] as string[]
})

const draftCount = computed(() => rfqs.value.filter(r => r.status === 'Draft').length)
const sentCount = computed(() => rfqs.value.filter(r => r.status === 'Sent').length)
const receivedCount = computed(() => rfqs.value.filter(r => r.status === 'Received').length)
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code} - ${p.name}`, value: p.id })))

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num)
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const isOverdue = (date: string) => new Date(date) < new Date()

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Draft: 'gray', Sent: 'blue', Received: 'green', Closed: 'purple', Cancelled: 'red' }
  return colors[status] || 'gray'
}

const addItem = () => {
  form.items.push({ product_id: '', quantity: 1 })
}

const fetchData = async () => {
  loading.value = true
  try {
    const [rfqRes, prodRes, vendorRes] = await Promise.all([
      $api.get('/procurement/rfqs'),
      $api.get('/manufacturing/products'),
      $api.get('/procurement/vendors')
    ])
    rfqs.value = rfqRes.data || []
    products.value = prodRes.data || []
    vendors.value = vendorRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { deadline: '', notes: '', items: [], vendor_ids: [] })
  isOpen.value = true
}

const viewDetails = (row: any) => {
  selectedRFQ.value = row
  showDetailModal.value = true
}

const save = async () => {
  submitting.value = true
  try {
    await $api.post('/procurement/rfqs', form)
    toast.add({ title: 'Created', description: 'RFQ created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const sendRFQ = async (row: any) => {
  try {
    await $api.put(`/procurement/rfqs/${row.id}/send`)
    toast.add({ title: 'Sent', description: 'RFQ sent to vendors', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const selectVendor = async (row: any) => {
  // Show vendor selection modal (simplified)
  toast.add({ title: 'Select', description: 'Select vendor from detail view', color: 'blue' })
  viewDetails(row)
}

onMounted(() => { fetchData() })
</script>
