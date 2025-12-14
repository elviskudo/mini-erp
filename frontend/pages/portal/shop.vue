<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
       <h2 class="text-xl font-semibold text-gray-900">B2B Customer Portal</h2>
       <div class="flex gap-4 items-center">
           <div class="text-sm text-gray-500" v-if="customer">
               Logged in as: <span class="font-bold text-gray-900">{{ customer.name }}</span>
           </div>
           <UButton icon="i-heroicons-shopping-cart" color="black" variant="soft" @click="isCartOpen = true">
               Cart ({{ cart.length }})
           </UButton>
       </div>
    </div>

    <!-- No Customer Mock Login -->
    <UCard v-if="!customer" class="max-w-md mx-auto mt-10">
        <h3 class="font-bold mb-4">Customer Login (Simulation)</h3>
        <USelectMenu v-model="customer" 
                        :options="customers" 
                        option-attribute="name"
                        placeholder="Select Self as Customer"
                        searchable />
        <p class="text-xs text-gray-500 mt-2">Select a customer to simulate the B2B logged-in view.</p>
    </UCard>

    <!-- Catalog Grid -->
    <div v-else>
         <div v-if="loading" class="text-center py-10">Loading catalog...</div>
         <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
             <UCard v-for="product in catalog" :key="product.id" class="flex flex-col h-full">
                 <div class="h-32 bg-gray-100 flex items-center justify-center rounded mb-4">
                     <UIcon name="i-heroicons-cube" class="text-4xl text-gray-300" />
                 </div>
                 <div class="flex-1">
                     <h3 class="font-bold truncate">{{ product.name }}</h3>
                     <div class="text-xs text-gray-500 mb-2">{{ product.code }}</div>
                     <div class="flex justify-between items-center mb-2">
                         <span class="font-bold text-lg">${{ product.price.toLocaleString() }}</span>
                         <UBadge :color="product.available_stock > 0 ? 'green' : 'red'" variant="subtle" size="xs">
                             {{ product.available_stock > 0 ? 'In Stock' : 'Out of Stock' }}
                         </UBadge>
                     </div>
                 </div>
                 <div class="mt-4">
                     <UButton block color="black" :disabled="product.available_stock <= 0" @click="addToCart(product)">
                         Add to Cart
                     </UButton>
                 </div>
             </UCard>
         </div>
    </div>

    <!-- Cart Modal -->
    <UModal v-model="isCartOpen">
        <div class="p-6">
            <h3 class="text-lg font-bold mb-4">Shopping Cart</h3>
            
            <div v-if="cart.length === 0" class="text-center text-gray-500 py-4">Your cart is empty.</div>
            <div v-else class="space-y-4">
                <div v-for="(item, idx) in cart" :key="idx" class="flex justify-between items-center border-b pb-2">
                    <div>
                        <div class="font-bold">{{ item.product.name }}</div>
                        <div class="text-sm text-gray-500">${{ item.product.price }} x {{ item.quantity }}</div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="font-mono font-bold">${{ (item.product.price * item.quantity).toLocaleString() }}</span>
                         <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="removeFromCart(idx)" />
                    </div>
                </div>
                
                <div class="flex justify-between pt-2 text-lg font-bold">
                    <span>Total</span>
                    <span>${{ cartTotal.toLocaleString() }}</span>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isCartOpen = false">Close</UButton>
                <UButton color="black" :loading="checkingOut" :disabled="cart.length === 0" @click="checkout">Checkout</UButton>
            </div>
        </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const checkingOut = ref(false)
const isCartOpen = ref(false)
const catalog = ref([])
const cart = ref([])
const customer = ref(null) // Logged in customer context
const customers = ref([])

const cartTotal = computed(() => {
    return cart.value.reduce((sum, item) => sum + (item.product.price * item.quantity), 0)
})

const fetchCatalog = async () => {
    loading.value = true
    try {
        const res = await $api.get('/ecommerce/catalog')
        catalog.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const fetchCustomers = async () => {
    // Just for the simulation dropdown
    try {
        const res = await $api.get('/ar/customers')
        customers.value = res.data
    } catch (e) {}
}

const addToCart = (product) => {
    const existing = cart.value.find(item => item.product.id === product.id)
    if (existing) {
        existing.quantity++
    } else {
        cart.value.push({ product, quantity: 1 })
    }
    toast.add({ title: 'Added', description: `${product.name} added to cart.` })
}

const removeFromCart = (idx) => {
    cart.value.splice(idx, 1)
}

const checkout = async () => {
    if (!customer.value) return
    checkingOut.value = true
    try {
        const payload = {
            customer_id: customer.value.id,
            items: cart.value.map(item => ({
                product_id: item.product.id,
                quantity: item.quantity
            }))
        }
        await $api.post('/ecommerce/checkout', payload)
        toast.add({ title: 'Order Placed', description: 'Your order has been received.' })
        cart.value = []
        isCartOpen.value = false
        // Refresh catalog to update stock if we were calculating it real-time
        fetchCatalog() 
    } catch (e) {
         toast.add({ title: 'Error', description: 'Checkout failed.' })
    } finally {
        checkingOut.value = false
    }
}

onMounted(() => {
    fetchCatalog()
    fetchCustomers()
})
</script>
