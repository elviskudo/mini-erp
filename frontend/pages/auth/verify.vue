<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <UCard class="w-full max-w-sm">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900">Verify Email</h1>
          <p class="text-gray-500 mt-1">Enter the verification code sent to your email</p>
        </div>
      </template>

      <form @submit.prevent="handleVerify" class="space-y-4">
        <div class="text-center mb-4">
          <p class="text-sm text-gray-600">We sent a code to:</p>
          <p class="font-medium text-gray-900">{{ email }}</p>
        </div>

        <UFormGroup label="Verification Code" name="otp" :error="error">
          <UInput 
            v-model="otpCode"
            placeholder="Enter 6-digit code"
            class="text-center text-2xl tracking-widest"
            maxlength="6"
            :color="error ? 'red' : undefined"
          />
        </UFormGroup>

        <UAlert v-if="success" color="green" variant="soft" :title="success" icon="i-heroicons-check-circle" />

        <UButton type="submit" block :loading="loading" :disabled="otpCode.length !== 6">
          Verify Email
        </UButton>

        <div class="text-center">
          <UButton 
            variant="ghost" 
            :loading="resending"
            :disabled="resendCooldown > 0"
            @click="handleResend"
          >
            {{ resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend Code' }}
          </UButton>
        </div>

        <div class="text-center text-sm text-gray-500">
          <NuxtLink to="/auth/login" class="text-primary-500 hover:underline">Back to Login</NuxtLink>
        </div>
      </form>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const route = useRoute()

const email = ref(route.query.email as string || '')
const otpCode = ref(route.query.otp as string || '')  // Auto-fill from URL
const error = ref('')
const success = ref('')
const loading = ref(false)
const resending = ref(false)
const resendCooldown = ref(0)

// Start cooldown timer
let cooldownInterval: NodeJS.Timeout | null = null

const startCooldown = () => {
  resendCooldown.value = 60
  cooldownInterval = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      clearInterval(cooldownInterval!)
    }
  }, 1000)
}

onMounted(() => {
  if (!email.value) {
    navigateTo('/auth/login')
  }
  // Only start cooldown if no OTP in URL (email was actually sent)
  if (!route.query.otp) {
    startCooldown()
  }
})

onUnmounted(() => {
  if (cooldownInterval) {
    clearInterval(cooldownInterval)
  }
})

const handleVerify = async () => {
  error.value = ''
  success.value = ''
  loading.value = true
  
  try {
    const response: any = await $fetch('/api/auth/verify-otp', {
      method: 'POST',
      body: {
        email: email.value,
        otp_code: otpCode.value
      }
    })
    
    success.value = response.message || 'Email verified successfully!'
    
    setTimeout(() => {
      navigateTo('/auth/login')
    }, 2000)
    
  } catch (e: any) {
    error.value = e.data?.detail || 'Verification failed'
  } finally {
    loading.value = false
  }
}

const handleResend = async () => {
  error.value = ''
  resending.value = true
  
  try {
    const response: any = await $fetch('/api/auth/send-otp', {
      method: 'POST',
      body: {
        email: email.value
      }
    })
    
    // Auto-fill OTP if returned (dev mode)
    if (response.otp_code) {
      otpCode.value = response.otp_code
    }
    
    startCooldown()
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to resend code'
  } finally {
    resending.value = false
  }
}
</script>
