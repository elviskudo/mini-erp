<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-purple-100">
    <div class="w-full max-w-lg">
      <!-- Step Indicator -->
      <div class="flex justify-center mb-8">
        <div class="flex items-center space-x-4">
          <div :class="[step === 1 ? 'bg-pink-500 text-white' : 'bg-gray-200', 'w-10 h-10 rounded-full flex items-center justify-center font-bold']">1</div>
          <div class="w-12 h-1 bg-gray-200"></div>
          <div :class="[step === 2 ? 'bg-pink-500 text-white' : 'bg-gray-200', 'w-10 h-10 rounded-full flex items-center justify-center font-bold']">2</div>
        </div>
      </div>

      <!-- Step 1: Register Company -->
      <UCard v-if="step === 1" class="shadow-xl">
        <template #header>
          <div class="text-center">
            <h1 class="text-2xl font-bold text-gray-900">Register Your Company</h1>
            <p class="text-gray-500 mt-1">Step 1 of 2: Company Details</p>
          </div>
        </template>

        <form @submit.prevent="registerCompany" class="space-y-4">
          <UFormGroup label="Company Name" required>
            <UInput v-model="company.name" placeholder="Acme Corporation" />
          </UFormGroup>

          <UFormGroup label="Domain (optional)" hint="Your unique subdomain">
            <UInput v-model="company.domain" placeholder="acme">
              <template #trailing>
                <span class="text-gray-400">.minierp.com</span>
              </template>
            </UInput>
          </UFormGroup>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Currency">
              <USelect v-model="company.currency" :options="currencies" />
            </UFormGroup>
            <UFormGroup label="Timezone">
              <USelect v-model="company.timezone" :options="timezones" />
            </UFormGroup>
          </div>

          <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-x-circle" />

          <UButton type="submit" block size="lg" :loading="loading" color="pink">
            Continue to Admin Setup →
          </UButton>
        </form>

        <template #footer>
          <p class="text-center text-sm text-gray-500">
            Already have a company? 
            <NuxtLink to="/auth/join-company" class="text-pink-500 hover:underline">Join existing</NuxtLink>
          </p>
        </template>
      </UCard>

      <!-- Step 2: Register Owner -->
      <UCard v-else class="shadow-xl">
        <template #header>
          <div class="text-center">
            <h1 class="text-2xl font-bold text-gray-900">Create Admin Account</h1>
            <p class="text-gray-500 mt-1">Step 2 of 2: Admin for <strong>{{ company.name }}</strong></p>
            <p v-if="companyCode" class="mt-2">
              <span class="text-xs text-gray-400">Company Code:</span>
              <span class="ml-2 px-2 py-1 bg-gray-100 rounded font-mono text-pink-600">{{ companyCode }}</span>
            </p>
          </div>
        </template>

        <form @submit.prevent="registerOwner" class="space-y-4">
          <UFormGroup label="Full Name">
            <UInput v-model="owner.fullName" placeholder="John Doe" />
          </UFormGroup>

          <UFormGroup label="Username" required>
            <UInput v-model="owner.username" placeholder="johndoe" />
          </UFormGroup>

          <UFormGroup label="Email" required>
            <UInput v-model="owner.email" type="email" placeholder="john@company.com" />
          </UFormGroup>

          <UFormGroup label="Password" required>
            <UInput v-model="owner.password" type="password" placeholder="Min 6 characters" />
          </UFormGroup>

          <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-x-circle" />
          <UAlert v-if="success" color="green" variant="soft" :title="success" icon="i-heroicons-check-circle" />

          <div class="flex space-x-3">
            <UButton variant="outline" @click="step = 1" :disabled="loading">
              ← Back
            </UButton>
            <UButton type="submit" class="flex-1" size="lg" :loading="loading" color="pink">
              Create Account
            </UButton>
          </div>
        </form>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const { $api } = useNuxtApp()

const step = ref(1)
const loading = ref(false)
const error = ref('')
const success = ref('')
const tenantId = ref('')
const companyCode = ref('')

const company = reactive({
  name: '',
  domain: '',
  currency: 'USD',
  timezone: 'UTC'
})

const owner = reactive({
  fullName: '',
  username: '',
  email: '',
  password: ''
})

const currencies = ['USD', 'EUR', 'IDR', 'GBP', 'JPY', 'SGD']
const timezones = ['UTC', 'Asia/Jakarta', 'Asia/Singapore', 'America/New_York', 'Europe/London']

const registerCompany = async () => {
  error.value = ''
  
  if (!company.name.trim()) {
    error.value = 'Company name is required'
    return
  }
  
  loading.value = true
  
  try {
    const response = await $api.post('/saas/register-tenant', {
      name: company.name,
      domain: company.domain || null,
      currency: company.currency,
      timezone: company.timezone
    })
    
    tenantId.value = response.data.id
    companyCode.value = response.data.company_code
    step.value = 2
    
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to register company'
  } finally {
    loading.value = false
  }
}

const registerOwner = async () => {
  error.value = ''
  success.value = ''
  
  if (!owner.username || !owner.email || !owner.password) {
    error.value = 'All fields are required'
    return
  }
  
  if (owner.password.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  
  loading.value = true
  
  try {
    await $api.post('/saas/register-owner', {
      tenant_id: tenantId.value,
      username: owner.username,
      email: owner.email,
      password: owner.password,
      full_name: owner.fullName || null
    })
    
    success.value = 'Account created! Redirecting to verify email...'
    
    setTimeout(() => {
      navigateTo(`/auth/verify?email=${encodeURIComponent(owner.email)}`)
    }, 1500)
    
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to register owner'
  } finally {
    loading.value = false
  }
}
</script>
