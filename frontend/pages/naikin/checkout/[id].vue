<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-pink-500 border-t-transparent"></div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- Main Checkout Form -->
        <div class="md:col-span-2 space-y-6">
          <!-- Customer Info -->
          <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 class="text-lg font-bold text-gray-900 mb-4">Contact Information</h2>
            <form class="space-y-4">
               <div>
                  <label class="block text-sm font-medium text-gray-700">Full Name</label>
                  <input type="text" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500 sm:text-sm p-2 border" placeholder="John Doe" />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700">Email Address</label>
                  <input type="email" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500 sm:text-sm p-2 border" placeholder="john@example.com" />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700">WhatsApp Number</label>
                  <input type="tel" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500 sm:text-sm p-2 border" placeholder="+62..." />
               </div>
            </form>
          </div>

          <!-- Payment Method -->
          <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
             <h2 class="text-lg font-bold text-gray-900 mb-4">Payment Method</h2>
             
             <div class="space-y-3">
                <div 
                    class="border rounded-lg p-4 flex items-center justify-between cursor-pointer transition-all"
                    :class="paymentMethod === 'qris' ? 'border-pink-500 bg-pink-50 ring-1 ring-pink-500' : 'border-gray-200 hover:border-gray-300'"
                    @click="paymentMethod = 'qris'"
                >
                    <div class="flex items-center gap-3">
                        <div class="w-4 h-4 rounded-full border flex items-center justify-center" :class="paymentMethod === 'qris' ? 'border-pink-500 bg-pink-500' : 'border-gray-300'">
                           <div v-if="paymentMethod === 'qris'" class="w-1.5 h-1.5 bg-white rounded-full"></div>
                        </div>
                        <span class="font-medium text-gray-900">QRIS (Instant)</span>
                    </div>
                    <!-- Mock QRIS Logo -->
                    <div class="w-10 h-6 bg-gray-200 rounded flex items-center justify-center text-[10px] font-bold text-gray-500">QRIS</div>
                </div>

                 <div 
                    class="border rounded-lg p-4 flex items-center justify-between cursor-pointer transition-all"
                    :class="paymentMethod === 'bank' ? 'border-pink-500 bg-pink-50 ring-1 ring-pink-500' : 'border-gray-200 hover:border-gray-300'"
                    @click="paymentMethod = 'bank'"
                >
                    <div class="flex items-center gap-3">
                        <div class="w-4 h-4 rounded-full border flex items-center justify-center" :class="paymentMethod === 'bank' ? 'border-pink-500 bg-pink-500' : 'border-gray-300'">
                           <div v-if="paymentMethod === 'bank'" class="w-1.5 h-1.5 bg-white rounded-full"></div>
                        </div>
                        <span class="font-medium text-gray-900">Bank Transfer</span>
                    </div>
                     <div class="flex gap-1">
                        <div class="w-8 h-5 bg-blue-600 rounded"></div>
                        <div class="w-8 h-5 bg-yellow-400 rounded"></div>
                     </div>
                </div>
             </div>

             <!-- Mock QR Code Display -->
             <div v-if="paymentMethod === 'qris'" class="mt-6 flex flex-col items-center p-4 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                 <div class="w-48 h-48 bg-white p-2 shadow-sm rounded-lg mb-2">
                     <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=MockPayment" alt="QRIS" class="w-full h-full" />
                 </div>
                 <p class="text-sm text-gray-500">Scan to Pay Rp {{ product.price.toLocaleString() }}</p>
             </div>
          </div>
        </div>

        <!-- Order Summary -->
        <div class="md:col-span-1">
           <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 sticky top-4">
              <h3 class="text-lg font-bold text-gray-900 mb-4">Order Summary</h3>
              
              <div class="flex gap-4 mb-4 pb-4 border-b border-gray-100">
                 <div class="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0">
                    <img v-if="product.image" :src="product.image" class="w-full h-full object-cover rounded-lg" />
                    <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                        <UIcon name="i-heroicons-photo" />
                    </div>
                 </div>
                 <div>
                    <h4 class="font-medium text-gray-900 line-clamp-2">{{ product.title }}</h4>
                    <span class="text-sm text-gray-500">Digital Product</span>
                 </div>
              </div>

              <div class="space-y-2 mb-6">
                 <div class="flex justify-between text-sm">
                    <span class="text-gray-500">Subtotal</span>
                    <span class="text-gray-900 font-medium">Rp {{ product.price.toLocaleString() }}</span>
                 </div>
                 <div class="flex justify-between text-sm">
                    <span class="text-gray-500">Fee</span>
                    <span class="text-gray-900 font-medium">Rp 0</span>
                 </div>
                 <div class="flex justify-between text-lg font-bold pt-2 border-t border-gray-100">
                    <span class="text-gray-900">Total</span>
                    <span class="text-pink-600">Rp {{ product.price.toLocaleString() }}</span>
                 </div>
              </div>

              <UButton block color="pink" size="lg" :loading="processing" @click="handlePay">
                 Pay Now
              </UButton>
              
              <p class="text-xs text-center text-gray-400 mt-4 flex items-center justify-center gap-1">
                 <UIcon name="i-heroicons-lock-closed" class="w-3 h-3" />
                 Secure Payment by Xendit
              </p>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'blank'
})

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const processing = ref(false)
const paymentMethod = ref('qris')

// Mock Product Data
const product = ref({
    title: 'Viral Ebook Campaign Bundle',
    price: 99000,
    image: null as string | null
})

onMounted(() => {
    // Simulate fetching checkout data details
    setTimeout(() => {
        loading.value = false
    }, 500)
})

const handlePay = () => {
    processing.value = true
    
    // Simulate Payment Processing
    setTimeout(() => {
        processing.value = false
        router.push('/naikin/checkout/success')
    }, 2000)
}
</script>
