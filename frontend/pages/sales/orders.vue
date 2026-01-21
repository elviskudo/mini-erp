<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Sales Orders</h2>
        <p class="text-gray-500">Manage customer confirmed orders</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Order</UButton>
      </div>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">

      <ServerDataTable
        :columns="columns"
        :data="orders"
        :pagination="pagination"
        :loading="loading"
        @page-change="handlePageChange"
        @limit-change="handleLimitChange"
        @refresh="fetchData"
      >
        <template #order_number-data="{ row }">
            <span class="font-mono font-medium text-blue-600">{{ row.order_number }}</span>
        </template>
        <template #total_amount-data="{ row }">
            {{ formatCurrency(row.total_amount) }}
        </template>
        <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
             <div class="flex gap-1">
                <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
                <UButton v-if="row.status === 'Draft'" icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="deleteItem(row)" />
            </div>
        </template>
      </ServerDataTable>
    </UCard>

    <!-- Create/Edit Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Order ' + form.order_number : 'New Sales Order'"
      :loading="saving"
      @submit="save"
    >
      <div class="space-y-6">
        
        <!-- Order Info & Status -->
        <div class="grid grid-cols-2 gap-4">
             <UFormGroup label="Order Number" required hint="Auto-generated" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="form.order_number" disabled placeholder="SO-2026..." />
             </UFormGroup>
             <UFormGroup label="Status" required hint="Current status" :ui="{ hint: 'text-xs text-gray-400' }">
                <USelectMenu v-model="form.status" :options="['Draft', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled']" />
             </UFormGroup>
        </div>

        <!-- Customer -->
        <UFormGroup label="Customer" required hint="Select a customer from CRM" :ui="{ hint: 'text-xs text-gray-400' }">
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
            <UFormGroup label="Order Date" required hint="Date placed" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput type="date" v-model="form.date" />
            </UFormGroup>
            <UFormGroup label="Delivery Date" hint="Expected delivery" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput type="date" v-model="form.delivery_date" />
            </UFormGroup>
        </div>

        <!-- Products Table -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium text-sm text-gray-700">Products</h4>
              <p class="text-xs text-gray-400">Add products: select item, enter quantity</p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg bg-gray-50">
            No items added. Click "Add Item" to start.
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
            <div class="w-24 text-right text-xs truncate">
                 {{ formatCurrency(item.unit_price) }}
            </div>
             <div class="w-24 text-right text-xs font-medium truncate">
                {{ formatCurrency(item.quantity * item.unit_price) }}
            </div>
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="removeItem(idx)" />
          </div>
        </div>

        <!-- Totals & Payment -->
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
                                <UButton size="2xs" color="yellow" variant="ghost" icon="i-heroicons-sparkles" />
                                <template #panel>
                                    <div class="p-2 text-xs w-48">
                                        <p class="mb-2">Loyalty Points Balance: <span class="font-bold text-yellow-600">500</span></p>
                                        <UButton size="xs" block @click="redeemCoin">Use 100 pts (Rp 10.000)</UButton>
                                    </div>
                                </template>
                            </UPopover>
                        </div>
                    </div>
                    <span class="text-sm font-medium text-red-500">- {{ formatCurrency(form.discount_amount) }}</span>
                 </div>

                 <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-600">Tax (11% VAT)</span>
                    <span class="font-medium">{{ formatCurrency(form.tax_amount) }}</span>
                </div>

                 <div class="flex justify-between items-center text-base font-bold border-t pt-3 border-gray-200 mt-2">
                    <span>Grand Total</span>
                    <span>{{ formatCurrency(form.total_amount) }}</span>
                </div>
            </div>

            <!-- Payment Terms -->
            <UFormGroup label="Payment Terms" hint="e.g. Net 30" :ui="{ hint: 'text-xs text-gray-400' }">
                <USelectMenu v-model="form.payment_terms" :options="paymentTermsOptions" />
            </UFormGroup>

            <!-- Notes -->
            <UFormGroup label="Notes" hint="Internal notes" :ui="{ hint: 'text-xs text-gray-400' }">
                <UTextarea v-model="form.notes" rows="3" placeholder="Add notes..." />
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

const orders = ref([])
const pagination = ref(null)
const currentPage = ref(1)
const currentLimit = ref(10)

const customers = ref<any[]>([])
const products = ref<any[]>([])

// === Helpers ===
const columns = [
    { key: 'order_number', label: 'Order Number', sortable: true },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'customer_id', label: 'Customer' },
    { key: 'total_amount', label: 'Total' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(val)

const getStatusColor = (status: string) => {
    const map: Record<string, string> = {
        'Draft': 'gray',
        'Confirmed': 'blue',
        'Shipped': 'orange',
        'Delivered': 'green',
        'Cancelled': 'red'
    }
    return map[status] || 'gray'
}

// === Options ===
const customerOptions = computed(() => customers.value.map(c => ({ label: `${c.name} ${c.phone}`, value: c.id })))
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code || ''} - ${p.name}`, value: p.id, price: p.standard_cost }))) // Include price in option for easier lookup

const paymentTermsOptions = ['Cash', 'Net 7', 'Net 15', 'Net 30', 'Net 60', 'Due on delivery']

// === Form ===
interface OrderItem {
    product_id: string
    quantity: number
    unit_price: number
    total: number
}

const form = reactive({
    id: '',
    order_number: '',
    customer_id: '',
    date: new Date().toISOString().split('T')[0],
    delivery_date: '',
    status: 'Draft',
    notes: '',
    payment_terms: '',
    subtotal: 0,
    discount_amount: 0,
    tax_amount: 0,
    total_amount: 0,
    items: [] as OrderItem[]
})

// === Actions ===
const fetchData = async () => {
    loading.value = true
    // 1. Fetch Orders (Active blocking)
    try {
        const res = await $api.get('/sales/orders', { params: { page: currentPage.value, limit: currentLimit.value, search: search.value } })
        if (res.data?.success || Array.isArray(res.data?.data)) {
             orders.value = res.data.data || []
             pagination.value = res.data.meta?.pagination
        } else {
             orders.value = []
        }
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to load orders', color: 'red' })
    } finally {
        loading.value = false
    }

    // 2. Fetch Aux Data (Background - non-blocking for UI)
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
        console.error('Background load error', e)
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
    form.order_number = 'SO-' + new Date().toISOString().slice(2,10).replace(/-/g, '') + '-' + Math.floor(Math.random() * 1000)
    isOpen.value = true
    editMode.value = false
}

const openEdit = (row: any) => {
    Object.assign(form, JSON.parse(JSON.stringify(row)))
    if (!form.items) form.items = []
    
    // Ensure we have aux data if not loaded yet
    if (customers.value.length === 0) loadAuxData()
    
    isOpen.value = true
    editMode.value = true
}

const resetForm = () => {
    Object.assign(form, {
        id: '',
        order_number: '',
        customer_id: '',
        date: new Date().toISOString().split('T')[0],
        delivery_date: '',
        status: 'Draft',
        notes: '',
        payment_terms: '',
        subtotal: 0,
        discount_amount: 0,
        tax_amount: 0,
        total_amount: 0,
        items: []
    })
}

const onProductChange = (item: OrderItem, productId: string) => {
    // Find product in options (which includes price) or raw products array
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
    toast.add({ title: 'Coin Redeemed', description: ' Discount applied!', color: 'green' })
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
    saving.value = true // Trigger spinner immediately
    
    // Validation
    if (!form.customer_id) {
        toast.add({ title: 'Validation', description: 'Customer is required', color: 'red' })
        saving.value = false
        return
    }
    if (form.items.length === 0) {
        toast.add({ title: 'Validation', description: 'Add at least one product', color: 'red' })
        saving.value = false
        return
    }

    try {
        if (editMode.value) {
            await $api.put(`/sales/orders/${form.id}`, form)
            toast.add({ title: 'Updated', description: 'Sales Order updated.' })
        } else {
            await $api.post('/sales/orders', form)
            toast.add({ title: 'Created', description: 'Sales Order created.' })
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

const deleteItem = async (row: any) => {
    if (!confirm('Are you sure?')) return
    // await $api.delete(`/sales/orders/${row.id}`)
    toast.add({ title: 'Deleted', color: 'green' })
    fetchData()
}

onMounted(() => {
    fetchData()
})
</script>
