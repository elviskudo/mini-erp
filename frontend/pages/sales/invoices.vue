<template>
    <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">Invoices</h1>
                <p class="text-gray-500">Manage sales invoices</p>
            </div>
            <UButton icon="i-heroicons-plus" @click="openCreate">New Invoice</UButton>
        </div>

        <UCard :ui="{ body: { padding: 'p-4' } }">
            <ServerDataTable
                :columns="columns"
                :data="items"
                :pagination="pagination"
                :loading="loading"
                search-placeholder="Search invoices..."
                @page-change="handlePageChange"
                @limit-change="handleLimitChange"
                @refresh="fetchData"
            >
                <template #total_amount-data="{ row }">
                   {{ formatCurrency(row.total_amount) }}
                </template>
                 <template #paid_amount-data="{ row }">
                   {{ formatCurrency(row.paid_amount) }}
                </template>
                 <template #status-data="{ row }">
                    <UBadge :color="getStatusColor(row.status)" variant="soft">{{ row.status }}</UBadge>
                </template>
                <template #actions-data="{ row }">
                    <div class="flex gap-1">
                        <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
                        <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="deleteItem(row)" />
                    </div>
                </template>
            </ServerDataTable>
        </UCard>

        <!-- Form Slideover -->
        <FormSlideover
            v-model="isOpen"
            :title="editMode ? 'Edit Invoice ' + form.invoice_number : 'New Invoice'"
            :loading="saving"
            @submit="save"
        >
            <div class="space-y-6">
                 <!-- Header Info -->
                <div class="grid grid-cols-1 gap-4">
                    <UFormGroup label="Customer" required>
                        <UInput v-model="form.customer_id" placeholder="Select Customer (UUID)" />
                    </UFormGroup>
                    <div class="grid grid-cols-2 gap-4">
                        <UFormGroup label="Date" required>
                            <UInput type="date" v-model="form.date" />
                        </UFormGroup>
                        <UFormGroup label="Due Date">
                             <UInput type="date" v-model="form.due_date" />
                        </UFormGroup>
                    </div>
                </div>

                <!-- Items Table -->
                <div>
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="font-semibold text-gray-700">Items</h3>
                        <UButton size="xs" icon="i-heroicons-plus" variant="soft" @click="addItemRow">Add</UButton>
                    </div>
                    
                    <div v-for="(item, index) in form.items" :key="index" class="p-3 mb-2 bg-gray-50 rounded-lg space-y-2 border">
                        <div class="flex justify-between items-start">
                             <UFormGroup class="flex-1 mr-2">
                                <UInput v-model="item.description" placeholder="Description" size="sm" />
                             </UFormGroup>
                             <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="removeItemRow(index)" />
                        </div>
                        <div class="grid grid-cols-4 gap-2">
                            <UFormGroup>
                                <UInput type="number" v-model.number="item.quantity" @input="calculateRow(item)" placeholder="Qty" size="sm" />
                            </UFormGroup>
                             <UFormGroup class="col-span-2">
                                <UInput type="number" v-model.number="item.unit_price" @input="calculateRow(item)" placeholder="Price" size="sm" />
                            </UFormGroup>
                             <UFormGroup>
                                <UInput type="number" v-model.number="item.discount" @input="calculateRow(item)" placeholder="Disc %" size="sm" />
                            </UFormGroup>
                        </div>
                        <div class="text-right text-sm font-medium text-gray-600">
                            {{ formatCurrency(item.total) }}
                        </div>
                    </div>
                </div>

                <!-- Summary -->
                 <div class="bg-gray-50 p-4 rounded-lg space-y-2">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-500">Subtotal</span>
                        <span>{{ formatCurrency(form.subtotal) }}</span>
                    </div>
                     <div class="flex justify-between text-sm">
                        <span class="text-gray-500">Tax (11%)</span>
                        <span>{{ formatCurrency(form.tax_amount) }}</span>
                    </div>
                    <div class="flex justify-between text-base font-bold border-t pt-2 border-gray-200">
                        <span>Total</span>
                        <span>{{ formatCurrency(form.total_amount) }}</span>
                    </div>
                     <div class="flex justify-between text-sm text-green-600">
                        <span>Paid</span>
                        <span>{{ formatCurrency(form.paid_amount) }}</span>
                    </div>
                </div>

                <UFormGroup label="Notes">
                    <UTextarea v-model="form.notes" placeholder="Additional notes..." />
                </UFormGroup>
            </div>
        </FormSlideover>
    </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
    middleware: 'auth'
})

const { $api } = useNuxtApp()
const authStore = useAuthStore()
const toast = useToast()

// Data Table State
const loading = ref(false)
const items = ref<any[]>([])
const pagination = ref<any>(null)
const currentPage = ref(1)
const currentLimit = ref(10)

// Columns
const columns = [
    { key: 'invoice_number', label: 'Number' },
    { key: 'date', label: 'Date' },
    { key: 'due_date', label: 'Due Date' },
    { key: 'total_amount', label: 'Total' },
    { key: 'paid_amount', label: 'Paid' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

// Form State
const isOpen = ref(false)
const editMode = ref(false)
const saving = ref(false)

interface Item {
    id?: string
    product_id: string
    description: string
    quantity: number
    unit_price: number
    discount: number
    tax: number
    total: number
}

const form = ref({
    id: '',
    invoice_number: 'AUTO',
    customer_id: '',
    date: new Date().toISOString().split('T')[0],
    due_date: '',
    status: 'draft',
    subtotal: 0,
    tax_amount: 0,
    discount_amount: 0,
    total_amount: 0,
    paid_amount: 0,
    notes: '',
    items: [] as Item[]
})

// Data Handling
const fetchData = async () => {
    loading.value = true
    try {
        const res: any = await $api.get('/sales/invoices', {
            params: {
                page: currentPage.value,
                limit: currentLimit.value
            }
        })
        if (res.data.success) {
            items.value = res.data.data
            pagination.value = res.data.meta?.pagination || null
        }
    } catch (e) {
        toast.add({ title: 'Error loading data', color: 'red' })
    } finally {
        loading.value = false
    }
}

const handlePageChange = (page: number) => {
    currentPage.value = page
    fetchData()
}

const handleLimitChange = (limit: number) => {
    currentLimit.value = limit
    currentPage.value = 1
    fetchData()
}

// Helpers
const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(val)
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'draft': return 'gray'
        case 'sent': return 'blue'
        case 'paid': return 'green'
        case 'overdue': return 'red'
        default: return 'gray'
    }
}

// Form Actions
const resetForm = () => {
    form.value = {
        id: '',
        invoice_number: 'AUTO',
        customer_id: '',
        date: new Date().toISOString().split('T')[0],
        due_date: '',
        status: 'draft',
        subtotal: 0,
        tax_amount: 0,
        discount_amount: 0,
        total_amount: 0,
        paid_amount: 0,
        notes: '',
        items: []
    }
    addItemRow()
}

const openCreate = () => {
    resetForm()
    editMode.value = false
    isOpen.value = true
}

const openEdit = async (row: any) => {
    try {
        loading.value = true
        const res = await $api.get(`/sales/invoices/${row.id}`)
        if (res.data.success) {
            form.value = res.data.data
            editMode.value = true
            isOpen.value = true
        }
    } catch (e) {
        toast.add({ title: 'Error loading detail', color: 'red' })
    } finally {
        loading.value = false
    }
}

const save = async () => {
    saving.value = true
    try {
        if (editMode.value) {
            await $api.post(`/sales/invoices`, form.value)
             toast.add({ title: 'Updated', color: 'green' })
        } else {
            await $api.post('/sales/invoices', form.value)
             toast.add({ title: 'Created', color: 'green' })
        }
        isOpen.value = false
        fetchData()
    } catch (e) {
        toast.add({ title: 'Failed to save', color: 'red' })
    } finally {
        saving.value = false
    }
}

const deleteItem = async (row: any) => {
    if(!confirm('Are you sure you want to delete this invoice?')) return
    try {
       // await $api.delete(`/sales/invoices/${row.id}`)
       toast.add({ title: 'Deleted', color: 'green' })
       fetchData()
    } catch(e) {
        toast.add({ title: 'Error deleting', color: 'red' })
    }
}

// Item Logic
const addItemRow = () => {
    form.value.items.push({
        product_id: '',
        description: '',
        quantity: 1,
        unit_price: 0,
        discount: 0,
        tax: 11,
        total: 0
    })
}

const removeItemRow = (index: number) => {
    form.value.items.splice(index, 1)
    calculateTotals()
}

const calculateRow = (row: Item) => {
    const sub = row.quantity * row.unit_price
    const disc = sub * (row.discount / 100)
    row.total = sub - disc
    calculateTotals()
}

const calculateTotals = () => {
    let sub = 0
    form.value.items.forEach(item => {
        sub += item.total
    })
    const tax = sub * 0.11
    form.value.subtotal = sub
    form.value.tax_amount = tax
    form.value.total_amount = sub + tax
}

onMounted(() => {
    fetchData()
})
</script>
