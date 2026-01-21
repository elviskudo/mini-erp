<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Sales Invoices</h2>
        <p class="text-gray-500">Manage customer billing and payments</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Invoice</UButton>
      </div>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable
        :columns="columns"
        :data="invoices"
        :pagination="pagination"
        :loading="loading"
        @page-change="handlePageChange"
        @limit-change="handleLimitChange"
        @refresh="fetchData"
      >
        <template #invoice_number-data="{ row }">
            <span class="font-mono font-medium text-blue-600 cursor-pointer hover:underline" @click="viewDetail(row)">{{ row.invoice_number }}</span>
        </template>
        <template #date-data="{ row }">
            {{ formatDateShort(row.date) }}
        </template>
        <template #due_date-data="{ row }">
             <span :class="isOverdue(row) ? 'text-red-500 font-bold' : ''">{{ formatDateShort(row.due_date) }}</span>
        </template>
        <template #total_amount-data="{ row }">
            {{ formatCurrency(row.total_amount) }}
        </template>
        <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
             <div class="flex gap-1 justify-end">
                <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="viewDetail(row)" />
                <UButton v-if="row.status !== 'Paid' && row.status !== 'Cancelled'" icon="i-heroicons-banknotes" color="green" variant="ghost" size="xs" title="Record Payment" @click="recordPayment(row)" />
            </div>
        </template>
      </ServerDataTable>
    </UCard>

    <!-- Create Invoice Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      title="New Invoice"
      :loading="saving"
      @submit="save"
    >
      <div class="space-y-6">
        
        <!-- Header Info -->
        <div class="grid grid-cols-2 gap-4">
             <UFormGroup label="Invoice Number" required hint="Auto-generated" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="form.invoice_number" disabled placeholder="INV-2026..." />
             </UFormGroup>
             <UFormGroup label="Status" required hint="Current status" :ui="{ hint: 'text-xs text-gray-400' }">
                <USelectMenu v-model="form.status" :options="['Draft', 'Sent', 'Paid', 'Overdue', 'Cancelled']" />
             </UFormGroup>
        </div>

        <!-- Link Sales Order -->
        <UFormGroup label="Linked Sales Order" required hint="Select a confirmed order to bill" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu 
                v-model="form.sales_order_id" 
                :options="salesOrderOptions" 
                value-attribute="value"
                option-attribute="label"
                searchable 
                placeholder="Select Sales Order..." 
                @change="onOrderSelect"
            />
        </UFormGroup>

        <!-- Customer (Auto-filled) -->
        <UFormGroup label="Customer" required hint="Customer to bill (auto-filled)" :ui="{ hint: 'text-xs text-gray-400' }">
             <USelectMenu 
                v-model="form.customer_id" 
                :options="customerOptions" 
                value-attribute="value"
                option-attribute="label"
                disabled
                placeholder="Select Customer..." 
            />
        </UFormGroup>

        <!-- Dates -->
        <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Invoice Date" required hint="Issue date" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput type="date" v-model="form.date" />
            </UFormGroup>
            <UFormGroup label="Due Date" hint="Payment deadline" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput type="date" v-model="form.due_date" />
            </UFormGroup>
        </div>

        <!-- Products Table -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <h4 class="font-medium text-sm text-gray-700">Billable Items</h4>
              <p class="text-xs text-gray-400">Items from Sales Order</p>
            </div>
          </div>
          
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg bg-gray-50">
            Select a Sales Order to load items.
          </div>

          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center bg-gray-50 p-2 rounded-md border">
            <div class="flex-[3] text-sm">
                <span class="font-medium">{{ getProductName(item.product_id) }}</span>
            </div>
            <UInput v-model.number="item.quantity" type="number" placeholder="Qty" class="w-20" size="sm" />
            <UInput v-model.number="item.unit_price" type="number" placeholder="Price" class="w-24" size="sm" />
             <div class="w-24 text-right text-xs font-medium truncate">
                {{ formatCurrency(item.quantity * item.unit_price) }}
            </div>
          </div>
        </div>

        <!-- Totals & Loyalty -->
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
                                <UButton size="2xs" color="purple" variant="ghost" icon="i-heroicons-star" title="Apply Coin from Loyalty" />
                                <template #panel>
                                    <div class="p-2 text-xs w-48">
                                        <p class="mb-2">Loyalty Balance: <span class="font-bold text-purple-600">1250 pts</span></p>
                                        <UButton size="xs" block color="purple" @click="redeemCoin">Use 500 pts (-50k)</UButton>
                                    </div>
                                </template>
                            </UPopover>
                        </div>
                    </div>
                    <span class="text-sm font-medium text-red-500">- {{ formatCurrency(form.discount_amount) }}</span>
                 </div>

                 <div v-if="form.loyalty_coins_used > 0" class="flex justify-between items-center text-xs text-purple-600">
                    <span>Loyalty Coins Used</span>
                    <span>{{ form.loyalty_coins_used }} pts</span>
                 </div>

                 <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-600">Tax (11%)</span>
                    <span class="font-medium">{{ formatCurrency(form.tax_amount) }}</span>
                </div>

                 <div class="flex justify-between items-center text-base font-bold border-t pt-3 border-gray-200 mt-2">
                    <span>Grand Total</span>
                    <span>{{ formatCurrency(form.total_amount) }}</span>
                </div>
            </div>

            <UFormGroup label="Notes" hint="Billing notes" :ui="{ hint: 'text-xs text-gray-400' }">
                <UTextarea v-model="form.notes" rows="3" placeholder="Add notes..." />
            </UFormGroup>
        </div>

      </div>
    </FormSlideover>

    <!-- Detail/Payment Modal -->
    <UModal v-model="showDetail" :ui="{ width: 'max-w-xl' }">
        <UCard v-if="selectedInvoice">
            <template #header>
                <div class="flex justify-between items-center">
                    <h3 class="font-bold text-lg">{{ selectedInvoice.invoice_number }}</h3>
                    <UBadge :color="getStatusColor(selectedInvoice.status)">{{ selectedInvoice.status }}</UBadge>
                </div>
            </template>
            <div class="space-y-3 text-sm">
                <div class="grid grid-cols-2 gap-2">
                    <div class="text-gray-500">Customer</div>
                    <div class="font-medium text-right">{{ getCustomerName(selectedInvoice.customer_id) }}</div>
                    <div class="text-gray-500">Date</div>
                    <div class="text-right">{{ formatDateShort(selectedInvoice.date) }}</div>
                    <div class="text-gray-500">Total Amount</div>
                    <div class="font-bold text-right text-lg">{{ formatCurrency(selectedInvoice.total_amount) }}</div>
                </div>
                <!-- Items list could go here -->
            </div>
            <template #footer>
                <div class="flex justify-end gap-2">
                    <UButton variant="ghost" @click="showDetail = false">Close</UButton>
                    <UButton v-if="selectedInvoice.status !== 'Paid'" color="green" icon="i-heroicons-banknotes" @click="recordPayment(selectedInvoice)">Record Payment</UButton>
                </div>
            </template>
        </UCard>
    </UModal>

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
const showDetail = ref(false)
const search = ref('')
const selectedInvoice = ref<any>(null)

const invoices = ref([])
const pagination = ref(null)
const currentPage = ref(1)
const currentLimit = ref(10)

const customers = ref<any[]>([])
const products = ref<any[]>([])
const salesOrders = ref<any[]>([])

// === Helpers ===
const columns = [
    { key: 'invoice_number', label: 'Invoice #', sortable: true },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'due_date', label: 'Due Date' },
    { key: 'total_amount', label: 'Total' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(val || 0)
const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const getProductName = (id: string) => products.value.find(p => p.id === id)?.name || id
const getCustomerName = (id: string) => {
    const c = customers.value.find((c: any) => c.id === id)
    return c ? c.name : id
}

const isOverdue = (row: any) => {
    if (!row.due_date || row.status === 'Paid') return false
    return new Date(row.due_date) < new Date()
}

const getStatusColor = (status: string) => {
    const map: Record<string, string> = {
        'Draft': 'gray',
        'Sent': 'blue',
        'Paid': 'green',
        'Overdue': 'red',
        'Cancelled': 'gray'
    }
    return map[status] || 'gray'
}

// === Options ===
const customerOptions = computed(() => customers.value.map(c => ({ label: `${c.name}`, value: c.id })))
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code || ''} - ${p.name}`, value: p.id, price: p.standard_cost })))
// Filter orders that are Confirmed, Shipped or Delivered for invoicing (case-insensitive)
const salesOrderOptions = computed(() => {
    const validStatuses = ['confirmed', 'shipped', 'delivered', 'draft'] // Include draft for testing
    const filtered = salesOrders.value.filter(o => 
        validStatuses.includes((o.status || '').toLowerCase())
    )
    console.log('Sales Orders for Invoice:', salesOrders.value.length, 'total,', filtered.length, 'filtered')
    console.log('First order items:', salesOrders.value[0]?.items)
    return filtered.map(o => ({ 
        label: `${o.order_number} - ${o.status} (${formatDateShort(o.date)})`, 
        value: o.id, 
        raw: o 
    }))
})

// === Form ===
interface InvoiceItem {
    product_id: string
    quantity: number
    unit_price: number
    total: number
}

const form = reactive({
    id: '',
    invoice_number: '',
    sales_order_id: '',
    customer_id: '',
    date: new Date().toISOString().split('T')[0],
    due_date: '',
    status: 'Draft',
    notes: '',
    subtotal: 0,
    discount_amount: 0,
    loyalty_coins_used: 0,
    tax_amount: 0,
    total_amount: 0,
    items: [] as InvoiceItem[]
})

// === Actions ===
const fetchData = async () => {
    loading.value = true
    // 1. Fetch Invoices (Blocking)
    try {
        const res = await $api.get('/sales/invoices', { params: { page: currentPage.value, limit: currentLimit.value, search: search.value } })
        if (res.data?.success || Array.isArray(res.data?.data)) {
             invoices.value = res.data.data || []
             pagination.value = res.data.meta?.pagination
        } else {
             invoices.value = []
        }
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to load invoices', color: 'red' })
    } finally {
        loading.value = false
    }

    // 2. Aux Data (Background)
    loadAuxData()
}

const loadAuxData = async () => {
    try {
        const [custRes, prodRes, soRes] = await Promise.all([
             $api.get('/crm/customers', { params: { limit: 100 } }).catch(() => ({ data: [] })),
             $api.get('/inventory/products', { params: { limit: 100 } }).catch(() => ({ data: [] })),
             $api.get('/sales/orders', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } }))
        ])
        
        const cData = custRes.data
        customers.value = Array.isArray(cData) ? cData : (cData?.data || [])
        
        const pData = prodRes.data
        products.value = Array.isArray(pData) ? pData : (pData?.data || [])
        
        if (soRes.data?.data) salesOrders.value = soRes.data.data
    } catch (e) {
        console.error('Aux load error', e)
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
    form.invoice_number = 'INV-' + new Date().toISOString().slice(2,10).replace(/-/g, '') + '-' + Math.floor(Math.random() * 1000)
    // Default Due Date + 30 days
    const dd = new Date()
    dd.setDate(dd.getDate() + 30)
    form.due_date = dd.toISOString().split('T')[0]
    
    // Ensure aux data
    if (salesOrders.value.length === 0) loadAuxData()
    
    isOpen.value = true
}

const onOrderSelect = (newValue: any) => {
    console.log('onOrderSelect called with:', newValue, 'type:', typeof newValue)
    
    // Handle different USelectMenu event formats
    const selectedId = typeof newValue === 'object' ? newValue?.value : (newValue || form.sales_order_id)
    
    if (selectedId) {
        form.sales_order_id = selectedId
    }
    
    console.log('Looking for order ID:', selectedId)
    console.log('Available options:', salesOrderOptions.value.map(o => ({ value: o.value, label: o.label })))
    
    const link = salesOrderOptions.value.find(o => o.value === selectedId)
    console.log('Found link:', link ? 'yes' : 'no', 'has raw:', !!link?.raw, 'has items:', !!link?.raw?.items)
    
    if (link && link.raw) {
        const so = link.raw
        form.customer_id = so.customer_id || ''
        
        // Auto-fill items from SO
        if (so.items && Array.isArray(so.items)) {
            console.log('Copying', so.items.length, 'items from order')
            form.items = so.items.map((i: any) => ({
                product_id: i.product_id || '',
                quantity: i.quantity || 0,
                unit_price: i.unit_price || 0,
                total: i.total || 0
            }))
            calculateTotals()
        } else {
            console.log('No items found in order, so.items =', so.items)
            form.items = []
        }
        
        toast.add({ title: 'Order Loaded', description: `Loaded ${form.items.length} items from ${so.order_number}`, color: 'blue' })
    } else {
        console.log('No link found for selection')
    }
}

const resetForm = () => {
    Object.assign(form, {
        id: '',
        invoice_number: '',
        sales_order_id: '',
        customer_id: '',
        date: new Date().toISOString().split('T')[0],
        due_date: '',
        status: 'Draft',
        notes: '',
        subtotal: 0,
        discount_amount: 0,
        loyalty_coins_used: 0,
        tax_amount: 0,
        total_amount: 0,
        items: []
    })
}

const redeemCoin = () => {
    // Logic to query loyalty service would go here
    // Mock simulation
    const pointsUsed = 500
    const discountValue = 50000
    
    form.discount_amount += discountValue
    form.loyalty_coins_used = pointsUsed
    
    toast.add({ title: 'Coins Redeemed', description: `Used ${pointsUsed} pts for Rp ${formatCurrency(discountValue)} discount`, color: 'purple' })
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
watch(() => form.loyalty_coins_used, calculateTotals) 

const save = async () => {
    try {
        console.log('=== SAVE FUNCTION START ===')
        console.log('form.sales_order_id:', form.sales_order_id)
        console.log('form.customer_id:', form.customer_id)
        
        if (!form.sales_order_id) {
            console.log('Validation failed: sales_order_id is empty')
            toast.add({ title: 'Validation', description: 'Link Sales Order is required', color: 'red' })
            return
        }
        if (!form.customer_id) {
            console.log('Validation failed: customer_id is empty')
            toast.add({ title: 'Validation', description: 'Customer is required', color: 'red' })
            return
        }
        
        console.log('Validation passed!')
        console.log('editMode:', editMode.value)
        console.log('Setting saving = true')
        
        saving.value = true
        
        console.log('About to call API...')
        
        if (editMode.value) {
            console.log('Calling PUT /sales/invoices/' + form.id)
            const response = await $api.put(`/sales/invoices/${form.id}`, form)
            console.log('PUT response:', response)
            toast.add({ title: 'Updated', description: 'Sales Invoice updated.' })
        } else {
            console.log('Calling POST /sales/invoices')
            const response = await $api.post('/sales/invoices', form)
            console.log('POST response:', response)
            toast.add({ title: 'Created', description: 'Sales Invoice created.' })
        }
        
        console.log('API call successful, closing form')
        isOpen.value = false
        fetchData()
        resetForm()
        console.log('=== SAVE FUNCTION END (SUCCESS) ===')
    } catch(e: any) {
        console.error('=== SAVE FUNCTION ERROR ===')
        console.error('Error object:', e)
        console.error('Error response:', e.response)
        console.error('Error data:', e.response?.data)
        toast.add({ title: 'Error', description: e.response?.data?.message || e.message || 'Failed to save', color: 'red' })
    } finally {
        saving.value = false
        console.log('saving = false (finally block)')
    }
}

const viewDetail = (row: any) => {
    selectedInvoice.value = row
    showDetail.value = true
}

const recordPayment = async (row: any) => {
    if (!confirm(`Mark invoice ${row.invoice_number} as PAID?`)) return
    try {
        await $api.post(`/sales/invoices/${row.id}/pay`)
        toast.add({ title: 'Success', description: 'Payment recorded', color: 'green' })
        fetchData()
        if (selectedInvoice.value?.id === row.id) showDetail.value = false
    } catch (e: any) {
        toast.add({ title: 'Error', description: 'Failed to record payment', color: 'red' })
    }
}

onMounted(() => {
    fetchData()
})
</script>
