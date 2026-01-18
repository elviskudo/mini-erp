<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 max-w-md w-full p-8 text-center">
       <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <UIcon name="i-heroicons-check" class="w-10 h-10 text-green-600" />
       </div>
       
       <h1 class="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
       <p class="text-gray-500 mb-8">Thank you for your purchase. A receipt has been sent to your email.</p>
       
       <div class="border-t border-b border-gray-100 py-4 mb-8 space-y-2">
          <div class="flex justify-between text-sm">
             <span class="text-gray-500">Order ID</span>
             <span class="font-medium text-gray-900">#NDP-88219</span>
          </div>
           <div class="flex justify-between text-sm">
             <span class="text-gray-500">Payment Method</span>
             <span class="font-medium text-gray-900">QRIS</span>
          </div>
           <div class="flex justify-between text-sm">
             <span class="text-gray-500">Amount Paid</span>
             <span class="font-medium text-gray-900">Rp 99.000</span>
          </div>
       </div>

       <div class="space-y-3">
          <UButton block color="green" size="lg" icon="i-heroicons-chat-bubble-left-right" @click="contactWhatsApp">
             Confirm on WhatsApp
          </UButton>
          <UButton block color="gray" variant="ghost" to="/u/naikin/home">
             Back to Merchant
          </UButton>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'blank'
})

const contactWhatsApp = () => {
    const phone = '628123456789' // Mock merchant number
    const text = encodeURIComponent("Halo, saya sudah melakukan pembayaran untuk Order #NDP-88219. Mohon diproses ya!")
    window.open(`https://wa.me/${phone}?text=${text}`, '_blank')
}
</script>
