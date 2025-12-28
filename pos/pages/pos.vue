<template>
  <div class="min-h-screen flex">
    <!-- Left Panel: Products -->
    <div class="flex-1 p-6 overflow-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ tenantName }}</h1>
          <p class="text-sm text-gray-500">Location ID: {{ authStore.user?.tenant_id?.slice(0, 8) }}</p>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
            Last Synced: {{ lastSync }}
          </div>
          <UButton variant="ghost" icon="i-heroicons-question-mark-circle" @click="showHelp = true">Help</UButton>
        </div>
      </div>

      <!-- Category Tabs -->
      <div class="flex gap-2 mb-6 overflow-x-auto pb-2">
        <UButton 
          v-for="cat in categories" 
          :key="cat"
          :color="selectedCategory === cat ? 'orange' : 'gray'"
          :variant="selectedCategory === cat ? 'solid' : 'outline'"
          size="sm"
          class="whitespace-nowrap"
          @click="selectedCategory = cat"
        >
          {{ cat }}
        </UButton>
      </div>

      <!-- Product Grid -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-orange-500 animate-spin" />
      </div>
      
      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div 
          v-for="product in filteredProducts" 
          :key="product.id"
          class="bg-white rounded-xl p-4 shadow-sm product-card hover:shadow-md"
          @click="addToCart(product)"
        >
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3 class="font-semibold text-gray-900">{{ product.name }}</h3>
              <p class="text-xs text-gray-400">{{ product.category || 'General' }}</p>
            </div>
            <div class="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
              <img v-if="product.image_url" :src="product.image_url" :alt="product.name" class="w-full h-full object-cover" />
              <UIcon v-else name="i-heroicons-cube" class="w-8 h-8 text-gray-300" />
            </div>
          </div>
          <p class="text-lg font-bold text-orange-500">{{ formatPrice(product.unit_price) }}</p>
        </div>
      </div>

      <!-- Wristband / Customer Info -->
      <div v-if="cartStore.customer" class="fixed bottom-0 left-0 right-[420px] bg-white border-t p-4">
        <div class="flex items-center justify-between max-w-5xl mx-auto">
          <div class="flex items-center gap-4">
            <p class="text-sm font-medium text-gray-500">CUSTOMER INFORMATION</p>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                <UIcon name="i-heroicons-user" class="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p class="font-semibold">{{ cartStore.customer.name }}</p>
                <UBadge color="orange" size="xs">Credit: {{ formatPrice(cartStore.customer.current_balance) }}</UBadge>
              </div>
            </div>
            <UButton color="red" variant="soft" size="sm" @click="unlinkCustomer">Unlink</UButton>
          </div>
          
          <!-- Promo Selection -->
          <div v-if="activePromos.length > 0" class="flex items-center gap-3">
            <p class="text-sm text-gray-500">SELECT AVAILABLE PROMO TO APPLY</p>
            <div class="flex gap-2">
              <button 
                v-for="promo in activePromos" 
                :key="promo.code"
                :class="['promo-badge', cartStore.promo?.code === promo.code ? 'active' : 'border-gray-300']"
                @click="selectPromo(promo)"
              >
                {{ promo.name }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Panel: Cart -->
    <div class="w-[420px] bg-white shadow-xl flex flex-col h-screen sticky top-0">
      <!-- Cart Header -->
      <div class="p-4 border-b flex items-center justify-between">
        <h2 class="text-xl font-bold">Current Order</h2>
        <div class="flex items-center gap-2">
          <UButton variant="ghost" size="sm" color="red" @click="cartStore.clearCart">Clear All</UButton>
          <UButton variant="ghost" size="sm" icon="i-heroicons-cog-6-tooth" />
        </div>
      </div>

      <!-- Cart Items -->
      <div class="flex-1 overflow-auto p-4 custom-scrollbar">
        <div v-if="cartStore.items.length === 0" class="text-center py-12 text-gray-400">
          <UIcon name="i-heroicons-shopping-cart" class="w-12 h-12 mx-auto mb-3" />
          <p>No items in cart</p>
          <p class="text-sm">Click products to add</p>
        </div>
        
        <div v-else class="space-y-3">
          <div 
            v-for="item in cartStore.items" 
            :key="item.product_id"
            class="flex items-center gap-3 cart-item"
          >
            <div class="w-12 h-12 bg-gray-100 rounded-lg flex-shrink-0 flex items-center justify-center overflow-hidden">
              <img v-if="item.image_url" :src="item.image_url" class="w-full h-full object-cover" />
              <UIcon v-else name="i-heroicons-cube" class="w-6 h-6 text-gray-300" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-sm truncate">{{ item.name }}</p>
            </div>
            <div class="flex items-center gap-1">
              <UButton icon="i-heroicons-minus" size="xs" color="gray" variant="ghost" @click="cartStore.decrementQuantity(item.product_id)" />
              <span class="w-8 text-center text-sm font-medium">{{ item.quantity }}</span>
              <UButton icon="i-heroicons-plus" size="xs" color="gray" variant="ghost" @click="cartStore.incrementQuantity(item.product_id)" />
            </div>
            <p class="w-16 text-right font-semibold text-sm">${{ formatPrice(item.quantity * item.unit_price) }}</p>
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="cartStore.removeItem(item.product_id)" />
          </div>
        </div>
      </div>

      <!-- Totals -->
      <div class="p-4 border-t bg-gray-50 space-y-2">
        <div class="flex justify-between text-sm">
          <span class="text-gray-500">Subtotal</span>
          <span class="font-medium">{{ formatPrice(cartStore.subtotal) }}</span>
        </div>
        <div v-if="cartStore.discount > 0" class="flex justify-between text-sm">
          <span class="text-green-600">Discounts</span>
          <span class="text-green-600 font-medium">-{{ formatPrice(cartStore.discount) }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-500">Sales Tax</span>
          <span class="font-medium">{{ formatPrice(cartStore.tax) }}</span>
        </div>
        <div class="flex justify-between text-lg font-bold pt-2 border-t">
          <span>Total</span>
          <span>{{ formatPrice(cartStore.total) }}</span>
        </div>
      </div>

      <!-- Cashless Credit (if customer linked) -->
      <div v-if="cartStore.customer" class="px-4 py-3 border-t bg-orange-50">
        <div class="flex justify-between items-center">
          <div>
            <p class="text-xs text-gray-500 uppercase">Cashless Credit</p>
            <p class="text-xl font-bold text-orange-600">{{ formatPrice(cartStore.customer.current_balance) }}</p>
            <p class="text-xs text-gray-400">Available</p>
          </div>
          <UButton color="white" variant="outline" @click="showPayment = true">Cancel</UButton>
        </div>
      </div>

      <!-- Payment Button -->
      <div class="p-4 border-t space-y-2">
        <UButton 
          v-if="!cartStore.customer"
          block 
          size="lg" 
          color="gray"
          @click="showCustomerModal = true"
        >
          <UIcon name="i-heroicons-user-plus" class="mr-2" />
          Add Customer
        </UButton>
        
        <UButton 
          block 
          size="lg" 
          color="orange"
          :disabled="cartStore.items.length === 0 || !cartStore.customer"
          @click="showPayment = true"
        >
          <UIcon name="i-heroicons-credit-card" class="mr-2" />
          {{ cartStore.customer ? 'Pay With Cashless Credit' : 'Select Customer First' }}
        </UButton>
        
        <div v-if="cartStore.customer" class="text-center text-sm text-gray-500">
          Balance Due: <span class="font-semibold">{{ formatPrice(Math.max(0, cartStore.total - cartStore.customer.current_balance)) }}</span>
        </div>
      </div>
    </div>

    <!-- Customer Modal -->
    <CustomerModal v-model="showCustomerModal" @saved="onCustomerSaved" />

    <!-- Payment Modal -->
    <PaymentModal v-model="showPayment" @completed="onPaymentCompleted" />

    <!-- Payment Success Page -->
    <PaymentSuccess 
      v-if="showSuccess" 
      :transaction="completedTransaction" 
      @done="onSuccessDone" 
    />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useCartStore } from '~/stores/cart'
import { useCurrency } from '~/composables/useCurrency'

definePageMeta({ middleware: 'auth' })

const { $api } = useNuxtApp()
const authStore = useAuthStore()
const cartStore = useCartStore()
const { formatPrice, loadSettings } = useCurrency()

const loading = ref(true)
const products = ref<any[]>([])
const categories = ref<string[]>(['All Items'])
const selectedCategory = ref('All Items')
const activePromos = ref<any[]>([])

const showCustomerModal = ref(false)
const showPayment = ref(false)
const showHelp = ref(false)
const showSuccess = ref(false)
const completedTransaction = ref<any>(null)

const tenantName = computed(() => 'POS Terminal')
const lastSync = computed(() => {
  const now = new Date()
  return `${now.getMinutes()} mins ago`
})

const filteredProducts = computed(() => {
  if (selectedCategory.value === 'All Items') return products.value
  return products.value.filter(p => p.category === selectedCategory.value)
})

const fetchProducts = async () => {
  loading.value = true
  try {
    // Load currency settings first
    await loadSettings()
    
    const [prodRes, catRes, promoRes] = await Promise.all([
      $api.get('/pos/products'),
      $api.get('/pos/categories').catch(() => ({ data: { categories: [] } })),
      $api.get('/pos/promos').catch(() => ({ data: [] }))
    ])
    products.value = prodRes.data || []
    categories.value = ['All Items', ...(catRes.data?.categories || [])]
    activePromos.value = promoRes.data || []
  } catch (e) {
    console.error('Failed to fetch products:', e)
  } finally {
    loading.value = false
  }
}

const addToCart = (product: any) => {
  cartStore.addItem({
    id: product.id,
    name: product.name,
    unit_price: product.unit_price,
    image_url: product.image_url
  })
}

const onCustomerSaved = (customer: any) => {
  cartStore.setCustomer(customer)
  showCustomerModal.value = false
}

const unlinkCustomer = () => {
  cartStore.setCustomer(null)
  cartStore.setPromo(null)
}

const selectPromo = async (promo: any) => {
  if (cartStore.promo?.code === promo.code) {
    cartStore.setPromo(null)
    return
  }
  
  try {
    const res = await $api.post(`/pos/promos/validate?code=${promo.code}&order_amount=${cartStore.subtotal}`)
    if (res.data.valid) {
      cartStore.setPromo({
        code: promo.code,
        name: promo.name,
        discount: res.data.promo.discount
      })
    }
  } catch (e) {
    console.error('Promo validation failed:', e)
  }
}

const onPaymentCompleted = (transaction: any) => {
  // Store completed transaction and show success page
  completedTransaction.value = {
    id: transaction.id,
    items: cartStore.items,
    subtotal: cartStore.subtotal,
    discount: cartStore.discount,
    tax: cartStore.tax,
    total: cartStore.total,
    customer_id: cartStore.customer?.id,
    customer_name: cartStore.customer?.name,
    payment_method: transaction.payment_method,
    created_at: new Date().toISOString()
  }
  showPayment.value = false
  showSuccess.value = true
}

const onSuccessDone = () => {
  showSuccess.value = false
  completedTransaction.value = null
  cartStore.clearCart()
  fetchProducts()
}

onMounted(() => {
  authStore.init()
  fetchProducts()
})
</script>
