<template>
  <div class="fixed inset-0 bg-orange-500 flex flex-col items-center justify-center z-50">
    <!-- Animated Checkmark -->
    <div class="mb-8">
      <div class="w-24 h-24 bg-white rounded-full flex items-center justify-center animate-[scaleIn_0.5s_ease-out]">
        <svg 
          class="w-12 h-12 text-orange-500" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            class="animate-[drawCheck_0.5s_ease-out_0.3s_forwards]"
            d="M5 12l5 5L19 7" 
            stroke="currentColor" 
            stroke-width="3" 
            stroke-linecap="round" 
            stroke-linejoin="round"
            stroke-dasharray="30"
            stroke-dashoffset="30"
          />
        </svg>
      </div>
    </div>

    <!-- Success Text -->
    <h1 class="text-3xl font-bold text-white mb-4 animate-[fadeInUp_0.5s_ease-out_0.5s_both]">
      Payment Successful
    </h1>
    <p class="text-white/80 text-center max-w-xs mb-8 animate-[fadeInUp_0.5s_ease-out_0.6s_both]">
      Transaction completed successfully. Thank you for your purchase!
    </p>

    <!-- Transaction Details -->
    <div class="bg-white/10 backdrop-blur-sm rounded-xl p-6 w-80 mb-8 animate-[fadeInUp_0.5s_ease-out_0.7s_both]">
      <div class="flex justify-between text-white/70 mb-2">
        <span>Transaction ID</span>
        <span class="font-mono">{{ transaction?.id?.slice(0, 8) }}...</span>
      </div>
      <div class="flex justify-between text-white/70 mb-2">
        <span>Items</span>
        <span>{{ transaction?.items?.length || 0 }} items</span>
      </div>
      <div v-if="transaction?.customer_name" class="flex justify-between text-white/70 mb-2">
        <span>Customer</span>
        <span>{{ transaction.customer_name }}</span>
      </div>
      <div class="flex justify-between text-white font-bold text-xl pt-4 border-t border-white/20">
        <span>Total</span>
        <span>{{ formatPrice(transaction?.total || 0) }}</span>
      </div>
    </div>

    <!-- Print Buttons -->
    <div class="flex gap-3 mb-6 animate-[fadeInUp_0.5s_ease-out_0.8s_both]">
      <UButton 
        color="white" 
        variant="solid"
        icon="i-heroicons-printer"
        @click="printReceipt('58mm')"
      >
        Print 58mm
      </UButton>
      <UButton 
        color="white" 
        variant="solid"
        icon="i-heroicons-printer"
        @click="printReceipt('80mm')"
      >
        Print 80mm
      </UButton>
    </div>

    <!-- Done Button -->
    <UButton 
      color="white" 
      variant="outline"
      size="lg"
      class="animate-[fadeInUp_0.5s_ease-out_0.9s_both]"
      @click="$emit('done')"
    >
      Done - New Transaction
    </UButton>
  </div>
</template>

<script setup lang="ts">
import { useCurrency } from '~/composables/useCurrency'

const props = defineProps<{
  transaction: {
    id: string
    items: any[]
    subtotal: number
    discount: number
    tax: number
    total: number
    customer_id?: string
    customer_name?: string
    payment_method: string
    created_at?: string
  } | null
}>()

const emit = defineEmits<{
  (e: 'done'): void
}>()

const { formatPrice, settings } = useCurrency()

const printReceipt = (size: '58mm' | '80mm') => {
  const width = size === '58mm' ? 220 : 302 // pixels at 96dpi
  const transaction = props.transaction
  if (!transaction) return
  
  const currencySymbol = settings.value.currency_symbol
  const formatAmount = (val: number) => {
    const formatted = val.toLocaleString('id-ID')
    return settings.value.currency_position === 'after' 
      ? `${formatted} ${currencySymbol}` 
      : `${currencySymbol} ${formatted}`
  }
  
  const printWindow = window.open('', '_blank', `width=${width},height=600`)
  if (!printWindow) {
    alert('Pop-up blocked. Please allow pop-ups to print receipt.')
    return
  }
  
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Receipt</title>
      <style>
        @page { 
          size: ${size} auto;
          margin: 0;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
          font-family: 'Courier New', monospace; 
          font-size: ${size === '58mm' ? '10px' : '12px'};
          width: ${size};
          padding: 8px;
        }
        .center { text-align: center; }
        .bold { font-weight: bold; }
        .line { border-top: 1px dashed #000; margin: 8px 0; }
        .row { display: flex; justify-content: space-between; margin: 4px 0; }
        .item-name { flex: 1; }
        .item-qty { width: 30px; text-align: center; }
        .item-price { text-align: right; min-width: 60px; }
        .total { font-size: ${size === '58mm' ? '14px' : '16px'}; }
        .small { font-size: ${size === '58mm' ? '8px' : '10px'}; color: #666; }
      </style>
    </head>
    <body>
      <div class="center bold" style="font-size: ${size === '58mm' ? '14px' : '16px'}">POS RECEIPT</div>
      <div class="center small" style="margin-bottom: 8px">${new Date().toLocaleString('id-ID')}</div>
      <div class="small">Trans ID: ${transaction.id.slice(0, 8)}</div>
      ${transaction.customer_name ? `<div class="small">Customer: ${transaction.customer_name}</div>` : ''}
      
      <div class="line"></div>
      
      ${transaction.items.map(item => `
        <div class="row">
          <span class="item-name">${item.name}</span>
          <span class="item-qty">x${item.quantity}</span>
          <span class="item-price">${formatAmount(item.unit_price * item.quantity)}</span>
        </div>
      `).join('')}
      
      <div class="line"></div>
      
      <div class="row">
        <span>Subtotal</span>
        <span>${formatAmount(transaction.subtotal)}</span>
      </div>
      ${transaction.discount > 0 ? `
        <div class="row">
          <span>Discount</span>
          <span>-${formatAmount(transaction.discount)}</span>
        </div>
      ` : ''}
      ${transaction.tax > 0 ? `
        <div class="row">
          <span>Tax</span>
          <span>${formatAmount(transaction.tax)}</span>
        </div>
      ` : ''}
      
      <div class="line"></div>
      
      <div class="row bold total">
        <span>TOTAL</span>
        <span>${formatAmount(transaction.total)}</span>
      </div>
      
      <div class="row small">
        <span>Payment</span>
        <span>${transaction.payment_method}</span>
      </div>
      
      <div class="line"></div>
      
      <div class="center small" style="margin-top: 16px">
        Thank you for your purchase!
      </div>
    </body>
    </html>
  `
  
  printWindow.document.write(html)
  printWindow.document.close()
  
  // Auto print after a short delay
  setTimeout(() => {
    printWindow.print()
  }, 250)
}
</script>

<style>
@keyframes scaleIn {
  from { transform: scale(0); }
  to { transform: scale(1); }
}

@keyframes drawCheck {
  to { stroke-dashoffset: 0; }
}

@keyframes fadeInUp {
  from { 
    opacity: 0; 
    transform: translateY(20px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}
</style>
