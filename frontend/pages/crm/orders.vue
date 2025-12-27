<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Sales Orders</h2>
        <p class="text-gray-500">Manage customer orders and sales</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Order</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ orders.length }}</p>
          <p class="text-sm text-gray-500">Total Orders</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ draftOrders }}</p>
          <p class="text-sm text-gray-500">Draft</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ confirmedOrders }}</p>
          <p class="text-sm text-gray-500">Confirmed</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ formatCurrency(totalRevenue) }}</p>
          <p class="text-sm text-gray-500">Total Revenue</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="orders" 
        :loading="loading"
        searchable
        :search-keys="['customer_name', 'id']"
        empty-message="No orders yet. Create a new order to get started."
      >
        <template #id-data="{ row }">
          <span class="font-mono text-xs">{{ row.id.slice(0, 8) }}...</span>
        </template>
        <template #customer_name-data="{ row }">
          <span class="font-medium">{{ row.customer_name || 'Unknown' }}</span>
        </template>
        <template #date-data="{ row }">
          {{ formatDate(row.date) }}
        </template>
        <template #total_amount-data="{ row }">
          <span class="font-mono font-medium">{{ formatCurrency(row.total_amount) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton v-if="row.status === 'Draft'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="confirmOrder(row.id)" title="Confirm" />
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewOrder(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create Order Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      title="New Sales Order"
      :loading="saving"
      @submit="submitOrder"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create a new sales order for a customer.</p>
        
        <UFormGroup label="Customer" required hint="Select customer for this order" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect 
            v-model="selectedCustomer" 
            :options="customerOptions" 
            placeholder="Select customer..."
            searchable
          />
        </UFormGroup>

        <div v-if="selectedCustomer" class="p-3 bg-gray-50 rounded-lg text-sm">
          <p><strong>Credit Limit:</strong> {{ formatCurrency(getCustomerById(selectedCustomer)?.credit_limit || 0) }}</p>
          <p><strong>Current Balance:</strong> {{ formatCurrency(getCustomerById(selectedCustomer)?.current_balance || 0) }}</p>
          <p v-if="getCustomerById(selectedCustomer)?.credit_limit === 0" class="text-red-500 mt-2">
            <UIcon name="i-heroicons-exclamation-triangle" class="w-4 h-4 mr-1" />
            This customer has no credit limit and cannot place orders.
          </p>
        </div>

        <!-- Order Items -->
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3">Order Items</h4>
          
          <div class="grid grid-cols-12 gap-2 mb-3">
            <div class="col-span-5">
              <USelect 
                v-model="currentItem.product_id" 
                :options="availableProductOptions" 
                placeholder="Select product..."
                searchable
                size="sm"
              />
            </div>
            <div class="col-span-2">
              <UInput v-model.number="currentItem.quantity" type="number" min="1" placeholder="Qty" size="sm" />
            </div>
            <div class="col-span-3">
              <UInput v-model.number="currentItem.unit_price" type="number" min="0" placeholder="Price" size="sm" />
            </div>
            <div class="col-span-2">
              <UButton icon="i-heroicons-plus" color="gray" size="sm" :disabled="!currentItem.product_id || currentItem.quantity <= 0" @click="addItem">Add</UButton>
            </div>
          </div>

          <div v-if="cart.length > 0" class="border rounded-lg">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-gray-50 text-left">
                  <th class="p-2">Product</th>
                  <th class="p-2 text-right">Qty</th>
                  <th class="p-2 text-right">Price</th>
                  <th class="p-2 text-right">Subtotal</th>
                  <th class="p-2 w-10"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in cart" :key="idx" class="border-t">
                  <td class="p-2">{{ getProductById(item.product_id)?.name }}</td>
                  <td class="p-2 text-right">
                    <UInput v-model.number="item.quantity" type="number" min="1" size="xs" class="w-20 text-right" />
                  </td>
                  <td class="p-2 text-right">
                    <UInput v-model.number="item.unit_price" type="number" min="0" size="xs" class="w-24 text-right" />
                  </td>
                  <td class="p-2 text-right font-medium">{{ formatCurrency(item.quantity * item.unit_price) }}</td>
                  <td class="p-2">
                    <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="removeItem(idx)" />
                  </td>
                </tr>
              </tbody>
              <tfoot class="bg-gray-50 font-bold">
                <tr>
                  <td colspan="3" class="p-2 text-right">Total:</td>
                  <td class="p-2 text-right">{{ formatCurrency(cartTotal) }}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div v-else class="text-center py-6 text-gray-400 border rounded-lg">
            No items added yet.
          </div>
        </div>
      </div>
    </FormSlideover>

    <!-- View Order Modal -->
    <UModal v-model="showView" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedOrder">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">Order Details</h3>
              <p class="text-sm text-gray-500 font-mono">{{ selectedOrder.id }}</p>
            </div>
            <UBadge :color="getStatusColor(selectedOrder.status)" variant="subtle" size="lg">{{ selectedOrder.status }}</UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500">Customer</p>
              <p class="font-medium">{{ selectedOrder.customer_name || 'Unknown' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Date</p>
              <p class="font-medium">{{ formatDate(selectedOrder.date) }}</p>
            </div>
          </div>
          
          <div v-if="selectedOrder.items?.length > 0" class="border-t pt-4">
            <h4 class="font-medium mb-2">Items</h4>
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left border-b">
                  <th class="py-2">Product</th>
                  <th class="py-2 text-right">Qty</th>
                  <th class="py-2 text-right">Price</th>
                  <th class="py-2 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in selectedOrder.items" :key="item.product_id" class="border-b">
                  <td class="py-2">{{ item.product_name || item.product_id }}</td>
                  <td class="py-2 text-right">{{ item.quantity }}</td>
                  <td class="py-2 text-right">{{ formatCurrency(item.unit_price) }}</td>
                  <td class="py-2 text-right">{{ formatCurrency(item.subtotal) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="border-t pt-4 flex justify-between items-center">
            <span class="font-medium">Total:</span>
            <span class="text-xl font-bold">{{ formatCurrency(selectedOrder.total_amount) }}</span>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showView = false">Close</UButton>
            <UButton v-if="selectedOrder.status === 'Draft'" icon="i-heroicons-check" color="green" @click="confirmOrder(selectedOrder.id); showView = false">Confirm</UButton>
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
const saving = ref(false)
const isOpen = ref(false)
const showView = ref(false)
const selectedOrder = ref<any>(null)

const orders = ref<any[]>([])
const customers = ref<any[]>([])
const products = ref<any[]>([])

const selectedCustomer = ref('')
const cart = ref<any[]>([])
const currentItem = reactive({
  product_id: '',
  quantity: 1,
  unit_price: 0
})

const columns = [
  { key: 'id', label: 'Order ID' },
  { key: 'customer_name', label: 'Customer', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'total_amount', label: 'Total', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'actions', label: '' }
]

const draftOrders = computed(() => orders.value.filter(o => o.status === 'Draft').length)
const confirmedOrders = computed(() => orders.value.filter(o => o.status === 'Confirmed').length)
const totalRevenue = computed(() => orders.value.filter(o => o.status !== 'Cancelled' && o.status !== 'Draft').reduce((sum, o) => sum + o.total_amount, 0))

const customerOptions = computed(() => customers.value.map(c => ({ label: c.name, value: c.id })))
const productOptions = computed(() => products.value.map(p => ({ label: `${p.code} - ${p.name}`, value: p.id })))
// Filter out products that are already in the cart
const availableProductOptions = computed(() => {
  const selectedIds = cart.value.map(item => item.product_id)
  return productOptions.value.filter(p => !selectedIds.includes(p.value))
})

const cartTotal = computed(() => cart.value.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0))

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val || 0)
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { 'Draft': 'gray', 'Confirmed': 'blue', 'Shipped': 'green', 'Cancelled': 'red' }
  return colors[status] || 'gray'
}

const getCustomerById = (id: string) => customers.value.find(c => c.id === id)
const getProductById = (id: string) => products.value.find(p => p.id === id)

const fetchData = async () => {
  loading.value = true
  try {
    const [ordersRes, custRes, prodRes] = await Promise.all([
      $api.get('/crm/orders').catch(() => ({ data: [] })),
      $api.get('/ar/customers').catch(() => ({ data: [] })),
      $api.get('/manufacturing/products').catch(() => ({ data: [] }))
    ])
    orders.value = ordersRes.data || []
    customers.value = custRes.data || []
    products.value = prodRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  selectedCustomer.value = ''
  cart.value = []
  currentItem.product_id = ''
  currentItem.quantity = 1
  currentItem.unit_price = 0
  isOpen.value = true
}

const addItem = () => {
  if (!currentItem.product_id) return
  const product = getProductById(currentItem.product_id)
  cart.value.push({
    product_id: currentItem.product_id,
    quantity: currentItem.quantity,
    unit_price: currentItem.unit_price || product?.suggested_selling_price || 100
  })
  currentItem.product_id = ''
  currentItem.quantity = 1
  currentItem.unit_price = 0
}

const removeItem = (idx: number) => {
  cart.value.splice(idx, 1)
}

const submitOrder = async () => {
  if (!selectedCustomer.value) {
    toast.add({ title: 'Error', description: 'Please select a customer', color: 'red' })
    return
  }
  
  // Check credit limit
  const customer = getCustomerById(selectedCustomer.value)
  if (customer && customer.credit_limit === 0) {
    toast.add({ title: 'Error', description: 'This customer has no credit limit and cannot place orders', color: 'red' })
    return
  }
  
  if (cart.value.length === 0) {
    toast.add({ title: 'Error', description: 'Please add at least one item', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const payload = {
      customer_id: selectedCustomer.value,
      items: cart.value.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price
      }))
    }
    await $api.post('/crm/orders', payload)
    toast.add({ title: 'Created', description: 'Order created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to create order', color: 'red' })
  } finally {
    saving.value = false
  }
}

const confirmOrder = async (id: string) => {
  try {
    await $api.post(`/crm/orders/${id}/confirm`)
    toast.add({ title: 'Confirmed', description: 'Order confirmed successfully', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to confirm order', color: 'red' })
  }
}

const viewOrder = (row: any) => {
  selectedOrder.value = row
  showView.value = true
}

onMounted(() => { fetchData() })
</script>
