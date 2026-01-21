<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Credit Notes</h1>
        <p class="text-gray-500">Manage returns and credit memos</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Credit Note</UButton>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable
        :columns="columns"
        :data="creditNotes"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @limit-change="handleLimitChange"
      >
        <template #date-data="{ row }">
          {{ formatDateShort(row.date) }}
        </template>
        <template #total_amount-data="{ row }">
          {{ formatCurrency(row.total_amount) }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <!-- Create/Edit Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Credit Note' : 'New Credit Note'"
      :loading="saving"
      @submit="save"
    >
      <div class="space-y-6">
        
        <!-- Header Info -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Credit Note #" required>
            <UInput v-model="form.credit_note_number" disabled placeholder="CN-2026..." />
          </UFormGroup>
          <UFormGroup label="Status">
            <USelectMenu v-model="form.status" :options="['Draft', 'Issued', 'Applied', 'Cancelled']" />
          </UFormGroup>
        </div>

        <!-- Link Invoice (Optional) -->
        <UFormGroup label="Linked Invoice" hint="Optional - link to original invoice">
          <USelectMenu 
            v-model="form.invoice_id" 
            :options="invoiceOptions" 
            value-attribute="value"
            option-attribute="label"
            searchable 
            placeholder="Select Invoice..." 
            @change="onInvoiceSelect"
          />
        </UFormGroup>

        <!-- Customer -->
        <UFormGroup label="Customer" required>
          <USelectMenu 
            v-model="form.customer_id" 
            :options="customerOptions" 
            value-attribute="value"
            option-attribute="label"
            searchable
            placeholder="Select Customer..." 
          />
        </UFormGroup>

        <!-- Reason & Date -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Date" required>
            <UInput type="date" v-model="form.date" />
          </UFormGroup>
          <UFormGroup label="Reason">
            <USelectMenu v-model="form.reason" :options="['Return', 'Adjustment', 'Discount', 'Other']" />
          </UFormGroup>
        </div>

        <!-- Items -->
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium text-sm text-gray-700">Credit Items</h4>
            <UButton size="xs" variant="ghost" icon="i-heroicons-plus" @click="addItem">Add Item</UButton>
          </div>
          
          <div v-if="form.items.length === 0" class="text-center py-4 text-gray-400 text-sm border rounded-lg bg-gray-50">
            No items added yet. Click "Add Item" to start.
          </div>

          <div v-for="(item, idx) in form.items" :key="idx" class="flex gap-2 mb-2 items-center">
            <USelectMenu 
              v-model="item.product_id" 
              :options="productOptions" 
              value-attribute="value"
              option-attribute="label"
              searchable
              placeholder="Product..." 
              class="flex-[3]"
              size="sm"
            />
            <UInput v-model.number="item.quantity" type="number" placeholder="Qty" class="w-20" size="sm" />
            <UInput v-model.number="item.unit_price" type="number" placeholder="Price" class="w-24" size="sm" />
            <div class="w-24 text-right text-sm font-medium">{{ formatCurrency(item.quantity * item.unit_price) }}</div>
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="removeItem(idx)" />
          </div>
        </div>

        <!-- Totals -->
        <div class="bg-gray-50 p-4 rounded-lg space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Subtotal</span>
            <span class="font-medium">{{ formatCurrency(form.subtotal) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Tax (11%)</span>
            <span>{{ formatCurrency(form.tax_amount) }}</span>
          </div>
          <div class="flex justify-between text-lg font-bold border-t pt-2">
            <span>Total Credit</span>
            <span class="text-red-600">{{ formatCurrency(form.total_amount) }}</span>
          </div>
        </div>

        <!-- Notes -->
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" placeholder="Reason for credit..." />
        </UFormGroup>

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

const creditNotes = ref([])
const pagination = ref(null)
const currentPage = ref(1)
const currentLimit = ref(10)

const customers = ref<any[]>([])
const products = ref<any[]>([])
const invoices = ref<any[]>([])

// === Helpers ===
const columns = [
    { key: 'credit_note_number', label: 'Credit Note #', sortable: true },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'reason', label: 'Reason' },
    { key: 'total_amount', label: 'Amount' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const formatDateShort = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const getStatusColor = (status: string) => {
    const map: Record<string, string> = {
        'Draft': 'gray',
        'Issued': 'blue',
        'Applied': 'green',
        'Cancelled': 'red'
    }
    return map[status] || 'gray'
}

// === Options ===
const customerOptions = computed(() => customers.value.map(c => ({ label: c.name, value: c.id })))
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code || ''} - ${p.name}`, value: p.id, price: p.standard_cost })))
const invoiceOptions = computed(() => invoices.value.map(i => ({ label: `${i.invoice_number}`, value: i.id, raw: i })))

// === Form ===
interface CreditNoteItem {
    product_id: string
    description: string
    quantity: number
    unit_price: number
    total: number
}

const form = reactive({
    id: '',
    credit_note_number: '',
    invoice_id: '',
    customer_id: '',
    date: new Date().toISOString().split('T')[0],
    reason: 'Return',
    status: 'Draft',
    subtotal: 0,
    tax_amount: 0,
    total_amount: 0,
    notes: '',
    items: [] as CreditNoteItem[]
})

// === Actions ===
const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/sales/credit-notes', { params: { page: currentPage.value, limit: currentLimit.value } })
        if (res.data?.success || Array.isArray(res.data?.data)) {
            creditNotes.value = res.data.data || []
            pagination.value = res.data.meta?.pagination
        }
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to load credit notes', color: 'red' })
    } finally {
        loading.value = false
    }
    loadAuxData()
}

const loadAuxData = async () => {
    try {
        const [custRes, prodRes, invRes] = await Promise.all([
            $api.get('/crm/customers', { params: { limit: 100 } }).catch(() => ({ data: [] })),
            $api.get('/inventory/products', { params: { limit: 100 } }).catch(() => ({ data: [] })),
            $api.get('/sales/invoices', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } }))
        ])
        
        const cData = custRes.data
        customers.value = Array.isArray(cData) ? cData : (cData?.data || [])
        
        const pData = prodRes.data
        products.value = Array.isArray(pData) ? pData : (pData?.data || [])
        
        if (invRes.data?.data) invoices.value = invRes.data.data
    } catch (e) {
        console.error('Aux load error', e)
    }
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const handleLimitChange = (l: number) => { currentLimit.value = l; fetchData() }

const openCreate = () => {
    resetForm()
    editMode.value = false
    form.credit_note_number = 'CN-' + new Date().toISOString().slice(2,10).replace(/-/g, '') + '-' + Math.floor(Math.random() * 1000)
    if (customers.value.length === 0) loadAuxData()
    isOpen.value = true
}

const openEdit = (row: any) => {
    resetForm()
    editMode.value = true
    Object.assign(form, {
        ...row,
        items: row.items || []
    })
    isOpen.value = true
}

const onInvoiceSelect = (val: any) => {
    const inv = invoiceOptions.value.find(o => o.value === val)
    if (inv?.raw) {
        form.customer_id = inv.raw.customer_id
    }
}

const resetForm = () => {
    Object.assign(form, {
        id: '',
        credit_note_number: '',
        invoice_id: '',
        customer_id: '',
        date: new Date().toISOString().split('T')[0],
        reason: 'Return',
        status: 'Draft',
        subtotal: 0,
        tax_amount: 0,
        total_amount: 0,
        notes: '',
        items: []
    })
}

const addItem = () => {
    form.items.push({
        product_id: '',
        description: '',
        quantity: 1,
        unit_price: 0,
        total: 0
    })
}

const removeItem = (idx: number) => {
    form.items.splice(idx, 1)
    calculateTotals()
}

const calculateTotals = () => {
    let sub = 0
    form.items.forEach(item => {
        const lineTotal = item.quantity * item.unit_price
        if (item.total !== lineTotal) item.total = lineTotal
        sub += lineTotal
    })
    form.subtotal = sub
    form.tax_amount = sub * 0.11
    form.total_amount = sub + form.tax_amount
}

watch(() => form.items, calculateTotals, { deep: true })

const save = async () => {
    if (!form.customer_id) return toast.add({ title: 'Validation', description: 'Customer is required', color: 'red' })

    saving.value = true
    try {
        if (editMode.value) {
            await $api.put(`/sales/credit-notes/${form.id}`, form)
            toast.add({ title: 'Updated', description: 'Credit note updated.' })
        } else {
            await $api.post('/sales/credit-notes', form)
            toast.add({ title: 'Created', description: 'Credit note created.' })
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

onMounted(() => {
    fetchData()
})
</script>
