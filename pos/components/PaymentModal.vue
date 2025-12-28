<template>
  <UModal v-model="isOpen" :ui="{ width: 'max-w-lg' }">
    <UCard>
      <template #header>
        <div class="text-center">
          <h3 class="text-xl font-semibold">Complete Payment</h3>
          <p class="text-3xl font-bold text-orange-500 mt-2">{{ formatPrice(cartStore.total) }}</p>
        </div>
      </template>

      <div class="space-y-4">
        <!-- Payment Methods -->
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="method in paymentMethods"
            :key="method.value"
            :class="[
              'p-4 border-2 rounded-xl text-center transition-all',
              selectedMethod === method.value 
                ? 'border-orange-500 bg-orange-50' 
                : 'border-gray-200 hover:border-orange-300'
            ]"
            @click="selectedMethod = method.value"
          >
            <UIcon :name="method.icon" :class="['w-8 h-8 mx-auto mb-2', selectedMethod === method.value ? 'text-orange-500' : 'text-gray-400']" />
            <p class="font-medium">{{ method.label }}</p>
          </button>
        </div>

        <!-- Customer Credit Info -->
        <div v-if="selectedMethod === 'CREDIT' && cartStore.customer" class="p-4 bg-orange-50 rounded-lg">
          <div class="flex justify-between mb-2">
            <span class="text-gray-600">Available Credit:</span>
            <span class="font-bold">{{ formatPrice(cartStore.customer.current_balance) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Amount to Charge:</span>
            <span class="font-bold text-orange-600">{{ formatPrice(cartStore.total) }}</span>
          </div>
          <div v-if="cartStore.customer.current_balance < cartStore.total" class="mt-2">
            <UAlert color="red" variant="soft" icon="i-heroicons-exclamation-triangle">
              Insufficient credit. Balance needed: {{ formatPrice(cartStore.total - cartStore.customer.current_balance) }}
            </UAlert>
          </div>
        </div>

        <!-- Cash Payment -->
        <div v-if="selectedMethod === 'CASH'" class="space-y-3">
          <UFormGroup label="Cash Received">
            <UInput v-model.number="cashReceived" type="number" size="lg" placeholder="0.00" />
          </UFormGroup>
          <div v-if="cashReceived >= cartStore.total" class="p-3 bg-green-50 rounded-lg">
            <div class="flex justify-between">
              <span>Change:</span>
              <span class="font-bold text-green-600">{{ formatPrice(cashReceived - cartStore.total) }}</span>
            </div>
          </div>
        </div>

        <!-- QRIS/Stripe Info -->
        <div v-if="selectedMethod === 'QRIS'" class="text-center p-6 bg-gray-50 rounded-lg">
          <UIcon name="i-heroicons-qr-code" class="w-16 h-16 mx-auto text-gray-400 mb-3" />
          <p class="text-gray-500">Scan QR code to pay</p>
          <p class="text-sm text-gray-400">Waiting for payment confirmation...</p>
        </div>

        <div v-if="selectedMethod === 'STRIPE'" class="text-center p-6 bg-gray-50 rounded-lg">
          <UIcon name="i-heroicons-credit-card" class="w-16 h-16 mx-auto text-gray-400 mb-3" />
          <p class="text-gray-500">Processing card payment...</p>
          <UInput v-model="paymentReference" placeholder="Enter Stripe payment ID" class="mt-3" />
        </div>

        <UAlert v-if="error" color="red" variant="soft" icon="i-heroicons-exclamation-triangle">
          {{ error }}
        </UAlert>
      </div>

      <template #footer>
        <div class="flex gap-3">
          <UButton color="gray" variant="outline" class="flex-1" @click="isOpen = false">
            Cancel
          </UButton>
          <UButton 
            color="orange" 
            class="flex-1" 
            :loading="processing"
            :disabled="!canComplete"
            @click="completePayment"
          >
            <UIcon name="i-heroicons-check-circle" class="mr-1" />
            Complete Payment
          </UButton>
        </div>
      </template>
    </UCard>
  </UModal>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'completed', transaction: { id: string, payment_method: string }): void
}>()

const { $api } = useNuxtApp()
const cartStore = useCartStore()

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const paymentMethods = [
  { value: 'CASH', label: 'Cash', icon: 'i-heroicons-banknotes' },
  { value: 'QRIS', label: 'QRIS', icon: 'i-heroicons-qr-code' },
  { value: 'STRIPE', label: 'Card', icon: 'i-heroicons-credit-card' },
  { value: 'CREDIT', label: 'Customer Credit', icon: 'i-heroicons-wallet' }
]

const selectedMethod = ref('CASH')
const cashReceived = ref(0)
const paymentReference = ref('')
const processing = ref(false)
const error = ref('')
import { useCurrency } from '~/composables/useCurrency'

const { formatPrice } = useCurrency()

const canComplete = computed(() => {
  if (processing.value) return false
  
  switch (selectedMethod.value) {
    case 'CASH':
      return cashReceived.value >= cartStore.total
    case 'CREDIT':
      return cartStore.customer && cartStore.customer.current_balance >= cartStore.total
    case 'STRIPE':
      return paymentReference.value.length > 0
    case 'QRIS':
      return true // Simulated
    default:
      return true
  }
})

const completePayment = async () => {
  error.value = ''
  processing.value = true

  try {
    const payload = {
      customer_id: cartStore.customer?.id || null,
      items: cartStore.items.map(item => ({
        product_id: item.product_id,
        name: item.name,
        quantity: item.quantity,
        unit_price: item.unit_price
      })),
      promo_code: cartStore.promo?.code || null,
      payment_method: selectedMethod.value,
      payment_reference: selectedMethod.value === 'STRIPE' ? paymentReference.value : null
    }

    const result = await $api.post('/pos/transaction', payload)
    emit('completed', { 
      id: result.data?.id || 'unknown',
      payment_method: selectedMethod.value 
    })
    
    // Reset
    selectedMethod.value = 'CASH'
    cashReceived.value = 0
    paymentReference.value = ''
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Payment failed'
  } finally {
    processing.value = false
  }
}

// Pre-fill cash received with total
watch(() => props.modelValue, (val) => {
  if (val) {
    cashReceived.value = cartStore.total
  }
})
</script>
