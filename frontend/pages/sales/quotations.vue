<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Sales Quotations</h2>
        <p class="text-gray-500">Manage price quotes and proposals</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Quote</UButton>
      </div>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable
        :columns="columns"
        :data="quotations"
        :pagination="pagination"
        :loading="loading"
        @page-change="handlePageChange"
        @limit-change="handleLimitChange"
        @refresh="fetchData"
      >
        <template #quotation_number-data="{ row }">
            <span class="font-mono font-medium text-blue-600 cursor-pointer hover:underline" @click="openEdit(row)">{{ row.quotation_number }}</span>
        </template>
        <template #date-data="{ row }">
            {{ formatDateShort(row.date) }}
        </template>
        <template #valid_until-data="{ row }">
             <span :class="isExpired(row) ? 'text-red-500' : ''">{{ formatDateShort(row.valid_until) }}</span>
        </template>
        <template #total_amount-data="{ row }">
            {{ formatCurrency(row.total_amount) }}
        </template>
        <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
             <div class="flex gap-1 justify-end">
                <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
                <UButton v-if="row.status === 'Accepted'" icon="i-heroicons-document-check" color="green" variant="ghost" size="xs" title="Converted" disabled />
                <UButton v-else-if="row.status !== 'Draft'" icon="i-heroicons-arrow-right-circle" color="blue" variant="ghost" size="xs" title="Convert to Order" @click="convertToOrder(row)" />
            </div>
        </template>
      </ServerDataTable>
    </UCard>

    <!-- Create/Edit Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Quote ' + form.quotation_number : 'New Quotation'"
      :loading="saving"
      @submit="save"
    >
      <div class="space-y-6">
        
        <!-- Quote Info & Status -->
        <div class="grid grid-cols-2 gap-4">
             <UFormGroup label="Quote Number" required hint="Auto-generated unique identifier" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="form.quotation_number" disabled placeholder="QU-2026..." />
             </UFormGroup>
             <UFormGroup label="Status" required hint="Current status" :ui="{ hint: 'text-xs text-gray-400' }">
                <USelectMenu v-model="form.status" :options="['Draft', 'Sent', 'Accepted', 'Rejected', 'Expired']" />
             </UFormGroup>
        </div>

        <!-- Customer -->
        <UFormGroup label="Customer" required hint="Select a prospective customer" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu 
                v-model="form.customer_id" 
                :options="customerOptions" 
                value-attribute="value"
                option-attribute="label"
                searchable 
                placeholder="Select customer..." 
            />
        </UFormGroup>

        <!-- Dates -->
        <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Quote Date" required hint="Date issued" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput type="date" v-model="form.date" />
            </UFormGroup>
            <UFormGroup label="Expiry Date" hint="Valid until" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput type="date" v-model="form.valid_until" />
            </UFormGroup>
        </div>

        <!-- Products Table -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium text-sm text-gray-700">Products</h4>
              <p class="text-xs text-gray-400">Add products and proposed pricing</p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg bg-gray-50">
            No items. Click "Add Item" to start.
          </div>

          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center bg-gray-50 p-2 rounded-md border">
            <USelectMenu 
                v-model="item.product_id" 
                :options="productOptions" 
                value-attribute="value"
                option-attribute="label"
                placeholder="Select Product..." 
                class="flex-[3]" 
                size="sm" 
                searchable
                @change="(val) => onProductChange(item, val)"
            />
            <UInput v-model.number="item.quantity" type="number" placeholder="Qty" class="w-20" size="sm" />
            <UInput v-model.number="item.unit_price" type="number" placeholder="Price" class="w-24" size="sm" />
             <div class="w-24 text-right text-xs font-medium truncate">
                {{ formatCurrency(item.quantity * item.unit_price) }}
            </div>
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="removeItem(idx)" />
          </div>
        </div>

        <!-- Totals & Discounts -->
        <div class="flex flex-col gap-4">
             <!-- Totals Section -->
            <div class="bg-gray-50 p-4 rounded-lg space-y-3">
                 <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-600">Subtotal</span>
                    <span class="font-medium">{{ formatCurrency(form.subtotal) }}</span>
                </div>
                 
                 <div class="flex justify-between items-center gap-2">
                    <div class="flex-1">
                        <span class="text-sm text-gray-600 block">Discount</span>
                        <div class="flex items-center gap-1 mt-1">
                            <UInput v-model.number="form.discount_amount" type="number" size="sm" placeholder="0" input-class="text-right" class="w-24" />
                            <UPopover>
                                <UButton size="2xs" color="yellow" variant="ghost" icon="i-heroicons-sparkles" title="Simulate Coin Redeem" />
                                <template #panel>
                                    <div class="p-2 text-xs w-48">
                                        <p class="mb-2">Customer Points: <span class="font-bold text-yellow-600">500</span></p>
                                        <UButton size="xs" block @click="redeemCoin">Use 100 pts (-10k)</UButton>
                                    </div>
                                </template>
                            </UPopover>
                        </div>
                    </div>
                    <span class="text-sm font-medium text-red-500">- {{ formatCurrency(form.discount_amount) }}</span>
                 </div>

                 <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-600">Tax (Auto 11%)</span>
                    <span class="font-medium">{{ formatCurrency(form.tax_amount) }}</span>
                </div>

                 <div class="flex justify-between items-center text-base font-bold border-t pt-3 border-gray-200 mt-2">
                    <span>Grand Total</span>
                    <span>{{ formatCurrency(form.total_amount) }}</span>
                </div>
            </div>

            <!-- Terms & Notes -->
            <UFormGroup label="Terms & Conditions" hint="Standard terms, warranties, payment deadlines" :ui="{ hint: 'text-xs text-gray-400' }">
                <UTextarea v-model="form.terms_conditions" rows="4" placeholder="Enter terms here..." />
            </UFormGroup>

            <UFormGroup label="Notes" hint="Internal notes or customer remarks" :ui="{ hint: 'text-xs text-gray-400' }">
                <UTextarea v-model="form.notes" rows="2" placeholder="Add notes..." />
            </UFormGroup>
        </div>

      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const { $api } = useNuxtApp()
const toast = useToast()
const authStore = useAuthStore()

definePageMeta({
    middleware: 'auth'
})

// === State ===
const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const editMode = ref(false)
const search = ref('')

const quotations = ref([])
const pagination = ref(null)
const currentPage = ref(1)
const currentLimit = ref(10)

const customers = ref<any[]>([])
const products = ref<any[]>([])

// === Helpers ===
const columns = [
    { key: 'quotation_number', label: 'Quote #', sortable: true },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'valid_until', label: 'Expiry' },
    { key: 'total_amount', label: 'Total' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(val || 0)
const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const isExpired = (row: any) => {
    if (!row.valid_until) return false
    return new Date(row.valid_until) < new Date() && row.status !== 'Accepted'
}

const getStatusColor = (status: string) => {
    const map: Record<string, string> = {
        'Draft': 'gray',
        'Sent': 'blue',
        'Accepted': 'green',
        'Rejected': 'red',
        'Expired': 'orange'
    }
    return map[status] || 'gray'
}

// === Options ===
const customerOptions = computed(() => customers.value.map(c => ({ label: `${c.name} ${c.phone || ''}`, value: c.id })))
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code || ''} - ${p.name}`, value: p.id, price: p.standard_cost })))

// === Form ===
interface QuoteItem {
    product_id: string
    quantity: number
    unit_price: number
    total: number
}

const form = reactive({
    id: '',
    quotation_number: '',
    customer_id: '',
    date: new Date().toISOString().split('T')[0],
    valid_until: '',
    status: 'Draft',
    notes: '',
    terms_conditions: '',
    subtotal: 0,
    discount_amount: 0,
    tax_amount: 0,
    total_amount: 0,
    items: [] as QuoteItem[]
})

// === Actions ===
// === Actions ===
const fetchData = async () => {
    loading.value = true
    // 1. Fetch Data (Blocking)
    try {
        const res = await $api.get('/sales/quotations', { params: { page: currentPage.value, limit: currentLimit.value, search: search.value } })
        if (res.data?.success || Array.isArray(res.data?.data)) {
             quotations.value = res.data.data || []
             pagination.value = res.data.meta?.pagination
        } else {
             quotations.value = []
        }
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to load quotations', color: 'red' })
    } finally {
        loading.value = false
    }

    // 2. Load Aux (Background)
    loadAuxData()
}

const loadAuxData = async () => {
    try {
        const [custRes, prodRes] = await Promise.all([
            $api.get('/crm/customers', { params: { limit: 100 } }).catch(() => ({ data: [] })),
            $api.get('/inventory/products', { params: { limit: 100 } }).catch(() => ({ data: [] }))
        ])
        
        const cData = custRes.data
        customers.value = Array.isArray(cData) ? cData : (cData?.data || [])
        
        const pData = prodRes.data
        products.value = Array.isArray(pData) ? pData : (pData?.data || [])
    } catch (e) {
        console.error("Aux load error", e)
    }
}

const handlePageChange = (p: number) => {
    currentPage.value = p
    fetchData()
}
const handleLimitChange = (l: number) => {
    currentLimit.value = l
    fetchData()
}

const openCreate = () => {
    resetForm()
    form.quotation_number = 'QU-' + new Date().toISOString().slice(2,10).replace(/-/g, '') + '-' + Math.floor(Math.random() * 1000)
    // Default valid for 14 days
    const validDate = new Date()
    validDate.setDate(validDate.getDate() + 14)
    form.valid_until = validDate.toISOString().split('T')[0]
    
    isOpen.value = true
    editMode.value = false
}

const openEdit = (row: any) => {
    Object.assign(form, JSON.parse(JSON.stringify(row)))
    // Ensure nested fields
    if (row.items) form.items = row.items
    
    // Check Date format (if comes as ISO string with time)
    if (form.date) form.date = form.date.split('T')[0]
    if (form.valid_until) form.valid_until = form.valid_until.split('T')[0]
    
    // Ensure options loaded
    if (customers.value.length === 0) loadAuxData()

    isOpen.value = true
    editMode.value = true
}

const resetForm = () => {
    Object.assign(form, {
        id: '',
        quotation_number: '',
        customer_id: '',
        date: new Date().toISOString().split('T')[0],
        valid_until: '',
        status: 'Draft',
        notes: '',
        terms_conditions: '',
        subtotal: 0,
        discount_amount: 0,
        tax_amount: 0,
        total_amount: 0,
        items: []
    })
}

const onProductChange = (item: QuoteItem, productId: string) => {
    const prodOption = productOptions.value.find(p => p.value === productId)
    if (prodOption) {
        item.unit_price = prodOption.price || 0
    }
}

const addItem = () => {
    form.items.push({
        product_id: '',
        quantity: 1,
        unit_price: 0,
        total: 0
    })
}

const removeItem = (index: number) => {
    form.items.splice(index, 1)
}

const redeemCoin = () => {
    form.discount_amount = 10000 
    toast.add({ title: 'Coin Redeemed', description: 'Discount applied!', color: 'green' })
}

const calculateTotals = () => {
    let sub = 0
    form.items.forEach(item => {
        const lineTotal = item.quantity * item.unit_price
        if (item.total !== lineTotal) item.total = lineTotal
        sub += lineTotal
    })
    
    if (form.subtotal !== sub) form.subtotal = sub
    
    const taxable = Math.max(0, sub - form.discount_amount)
    const tax = taxable * 0.11
    
    if (form.tax_amount !== tax) form.tax_amount = tax
    
    const total = taxable + tax
    if (form.total_amount !== total) form.total_amount = total
}

// Watchers for auto-calculation
watch(() => form.items, calculateTotals, { deep: true })
watch(() => form.discount_amount, calculateTotals)

const save = async () => {
    if (!form.customer_id) return toast.add({ title: 'Validation', description: 'Customer is required', color: 'red' })

    saving.value = true
    try {
        if (editMode.value) {
            await $api.put(`/sales/quotations/${form.id}`, form)
            toast.add({ title: 'Updated', description: 'Quotation updated.' })
        } else {
            await $api.post('/sales/quotations', form)
            toast.add({ title: 'Created', description: 'Quotation created.' })
        }
        isOpen.value = false
        fetchData()
        resetForm()
    } catch(e: any) {
         toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed to save', color: 'red' })
    } finally {
        saving.value = false
    }
}

const convertToOrder = async (row: any) => {
    if (!confirm('Convert this quotation to a confirmed Sales Order?')) return
    try {
        await $api.post(`/sales/quotations/${row.id}/convert`)
        toast.add({ title: 'Success', description: 'Converted to Order', color: 'green' })
        fetchData()
    } catch (e: any) {
        toast.add({ title: 'Error', description: 'Failed to convert', color: 'red' })
    }
}

onMounted(() => {
    fetchData()
})
</script>
