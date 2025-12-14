<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Sales Orders</h2>
      <UButton icon="i-heroicons-plus" color="black" @click="openCreateModal">New Order</UButton>
    </div>

    <!-- Stats Dashboard (Simple) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <UCard>
            <div class="text-sm text-gray-500">Total Revenue</div>
            <div class="text-2xl font-bold text-green-600">{{ formatCurrency(metrics.revenue) }}</div>
        </UCard>
        <UCard>
            <div class="text-sm text-gray-500">Open Orders</div>
            <div class="text-2xl font-bold text-blue-600">{{ metrics.openOrders }}</div>
        </UCard>
        <UCard>
            <div class="text-sm text-gray-500">Completed Orders</div>
            <div class="text-2xl font-bold text-gray-600">{{ metrics.completedOrders }}</div>
        </UCard>
    </div>

    <UCard>
       <UTable :columns="columns" :rows="orders" :loading="loading">
            <template #status-data="{ row }">
                <UBadge :color="getStatusColor(row.status)" variant="soft">{{ row.status }}</UBadge>
            </template>
            <template #total_amount-data="{ row }">
                <span class="font-mono">{{ formatCurrency(row.total_amount) }}</span>
            </template>
             <template #actions-data="{ row }">
                <UButton v-if="row.status === 'Draft'" size="xs" color="green" variant="ghost" icon="i-heroicons-check" @click="confirmOrder(row.id)">Confirm</UButton>
            </template>
       </UTable>
    </UCard>

    <!-- Create Order Modal -->
    <UModal v-model="isOpen" fullscreen>
      <div class="p-6 h-full flex flex-col">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-bold">New Sales Order</h3>
            <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="isOpen = false" />
        </div>

        <div class="flex-1 overflow-y-auto space-y-6">
             <!-- Customer Selection -->
            <UFormGroup label="Customer" required>
                <USelectMenu v-model="selectedCustomer" 
                             :options="customers" 
                             option-attribute="name"
                             placeholder="Select Customer"
                             searchable 
                             searchable-placeholder="Search customer..." />
                <div v-if="selectedCustomer" class="mt-2 text-sm text-gray-500">
                    Credit Limit: <span class="font-mono font-bold">{{ formatCurrency(selectedCustomer.credit_limit) }}</span> | 
                    Balance: <span class="font-mono text-red-500">{{ formatCurrency(selectedCustomer.current_balance) }}</span>
                </div>
            </UFormGroup>

            <!-- Product Selection / Cart -->
            <div class="border rounded-lg p-4">
                <h4 class="font-bold mb-4">Order Items</h4>
                <div class="flex gap-2 mb-4 items-end">
                    <UFormGroup label="Product" class="flex-1">
                        <USelectMenu v-model="currentItem.product" 
                                     :options="products" 
                                     option-attribute="name"
                                     placeholder="Select Product"
                                     searchable />
                    </UFormGroup>
                    <UFormGroup label="Qty" class="w-24">
                        <UInput v-model="currentItem.quantity" type="number" min="1" />
                    </UFormGroup>
                     <UFormGroup label="Price" class="w-32">
                        <UInput v-model="currentItem.price" type="number" min="0" />
                    </UFormGroup>
                    <UButton icon="i-heroicons-plus" color="black" @click="addItem" :disabled="!currentItem.product">Add</UButton>
                </div>

                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-left border-b">
                            <th class="py-2">Product</th>
                            <th class="py-2 text-right">Qty</th>
                            <th class="py-2 text-right">Price</th>
                            <th class="py-2 text-right">Subtotal</th>
                            <th class="w-10"></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(item, idx) in cart" :key="idx" class="border-b last:border-0">
                            <td class="py-2">{{ item.product.name }}</td>
                            <td class="py-2 text-right">{{ item.quantity }}</td>
                            <td class="py-2 text-right">{{ formatCurrency(item.price) }}</td>
                            <td class="py-2 text-right">{{ formatCurrency(item.quantity * item.price) }}</td>
                            <td class="py-2 text-right">
                                <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="removeItem(idx)" />
                            </td>
                        </tr>
                         <tr v-if="cart.length === 0">
                            <td colspan="5" class="py-4 text-center text-gray-500">No items added.</td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr class="font-bold border-t">
                            <td colspan="3" class="py-2 text-right">Total:</td>
                            <td class="py-2 text-right">{{ formatCurrency(cartTotal) }}</td>
                            <td></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>

        <div class="border-t pt-4 mt-4 flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
            <UButton color="black" :loading="saving" :disabled="!selectedCustomer || cart.length === 0" @click="submitOrder">Place Order</UButton>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatDate } from '~/utils/format'
const { $api } = useNuxtApp()
const toast = useToast()
const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const orders = ref([])
const customers = ref([])
const products = ref([])

// Metrics for Dashboard
const metrics = computed(() => {
    const revenue = orders.value
        .filter(o => o.status !== 'Cancelled' && o.status !== 'Draft')
        .reduce((sum, o) => sum + o.total_amount, 0)
    const openOrders = orders.value.filter(o => o.status === 'Draft' || o.status === 'Confirmed').length
    const completedOrders = orders.value.filter(o => o.status === 'Shipped').length
    return { revenue, openOrders, completedOrders }
})

const columns = [
  { key: 'id', label: 'Order ID' },
  { key: 'status', label: 'Status' },
  { key: 'total_amount', label: 'Total' },
  { key: 'actions', label: 'Actions' }
]

// Form State
const selectedCustomer = ref(null)
const cart = ref([])
const currentItem = reactive({
    product: null,
    quantity: 1,
    price: 0
})

const cartTotal = computed(() => {
    return cart.value.reduce((sum, item) => sum + (item.quantity * item.price), 0)
})

// Lifecycle
const fetchOrders = async () => {
    loading.value = true
    try {
        const res = await $api.get('/crm/orders')
        // Enhance with Customer name if needed, but API just returns customer_id usually unless preloaded.
        // Assuming API returns SOResponse which might not have customer name populated deep, but let's see. 
        // Ideally backend schema SOResponse should include customer info or frontend fetches it.
        // For MVP we just show ID or fetching Customers map.
        orders.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const fetchDependencies = async () => {
    try {
        const [custRes, prodRes] = await Promise.all([
            $api.get('/ar/customers'),
            $api.get('/manufacturing/products')
        ])
        customers.value = custRes.data
        products.value = prodRes.data
    } catch (e) {
        console.error("Failed to load dependencies", e)
    }
}

// Actions
const openCreateModal = () => {
    selectedCustomer.value = null
    cart.value = []
    isOpen.value = true
    fetchDependencies()
}

const addItem = () => {
    if (!currentItem.product) return
    cart.value.push({
        product: currentItem.product,
        quantity: currentItem.quantity,
        price: currentItem.price || currentItem.product.price || 100 // Fallback price
    })
    // Reset current item
    currentItem.product = null
    currentItem.quantity = 1
    currentItem.price = 0
}

const removeItem = (idx: number) => {
    cart.value.splice(idx, 1)
}

const submitOrder = async () => {
    saving.value = true
    try {
        const payload = {
            customer_id: selectedCustomer.value.id,
            items: cart.value.map(item => ({
                product_id: item.product.id,
                quantity: item.quantity,
                unit_price: item.price
            }))
        }
        await $api.post('/crm/orders', payload)
        toast.add({ title: 'Success', description: 'Order placed successfully.' })
        isOpen.value = false
        fetchOrders()
    } catch (e) {
        // Simple error handling - shows generic or backend message
        const msg = e.response?.data?.detail || 'Failed to place order.'
        toast.add({ title: 'Order Failed', description: msg, color: 'red' })
    } finally {
        saving.value = false
    }
}

const confirmOrder = async (id: string) => {
    try {
        await $api.post(`/crm/orders/${id}/confirm`)
        toast.add({ title: 'Order Confirmed', description: 'Stock allocated.' })
        fetchOrders()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to confirm order.', color: 'red' })
    }
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'Draft': return 'gray'
        case 'Confirmed': return 'blue'
        case 'Shipped': return 'green'
        case 'Cancelled': return 'red'
        default: return 'gray'
    }
}

onMounted(() => {
    fetchOrders()
})
</script>
