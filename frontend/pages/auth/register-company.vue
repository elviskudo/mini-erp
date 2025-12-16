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
            <UInput v-model="owner.password" type="password" placeholder="Strong password" />
            
            <!-- Password Strength Indicator -->
            <div class="mt-2 space-y-2">
              <div class="flex gap-1">
                <div 
                  v-for="i in 5" 
                  :key="i" 
                  class="h-1.5 flex-1 rounded-full transition-all"
                  :class="i <= passwordStrength.score ? strengthColors[passwordStrength.score] : 'bg-gray-200'"
                />
              </div>
              <p class="text-xs" :class="strengthTextColors[passwordStrength.score]">
                {{ passwordStrength.label }}
              </p>
              
              <!-- Requirements Checklist -->
              <div class="text-xs space-y-1 mt-2">
                <div :class="passwordChecks.minLength ? 'text-green-600' : 'text-gray-400'">
                  {{ passwordChecks.minLength ? '✓' : '○' }} Minimal 8 karakter
                </div>
                <div :class="passwordChecks.hasUpper ? 'text-green-600' : 'text-gray-400'">
                  {{ passwordChecks.hasUpper ? '✓' : '○' }} 1 huruf besar (A-Z)
                </div>
                <div :class="passwordChecks.hasLower ? 'text-green-600' : 'text-gray-400'">
                  {{ passwordChecks.hasLower ? '✓' : '○' }} 1 huruf kecil (a-z)
                </div>
                <div :class="passwordChecks.hasNumber ? 'text-green-600' : 'text-gray-400'">
                  {{ passwordChecks.hasNumber ? '✓' : '○' }} 1 angka (0-9)
                </div>
                <div :class="passwordChecks.hasSymbol ? 'text-green-600' : 'text-gray-400'">
                  {{ passwordChecks.hasSymbol ? '✓' : '○' }} 1 simbol (!@#$%^&*...)
                </div>
              </div>
            </div>
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

// Password strength colors
const strengthColors: Record<number, string> = {
  0: 'bg-gray-200',
  1: 'bg-red-500',
  2: 'bg-orange-500',
  3: 'bg-yellow-500',
  4: 'bg-lime-500',
  5: 'bg-green-500'
}

const strengthTextColors: Record<number, string> = {
  0: 'text-gray-400',
  1: 'text-red-500',
  2: 'text-orange-500',
  3: 'text-yellow-600',
  4: 'text-lime-600',
  5: 'text-green-600'
}

// Password requirement checks
const passwordChecks = computed(() => ({
  minLength: owner.password.length >= 8,
  hasUpper: /[A-Z]/.test(owner.password),
  hasLower: /[a-z]/.test(owner.password),
  hasNumber: /[0-9]/.test(owner.password),
  hasSymbol: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~]/.test(owner.password)
}))

// Password strength score (0-5)
const passwordStrength = computed(() => {
  const checks = passwordChecks.value
  let score = 0
  
  if (checks.minLength) score++
  if (checks.hasUpper) score++
  if (checks.hasLower) score++
  if (checks.hasNumber) score++
  if (checks.hasSymbol) score++
  
  const labels: Record<number, string> = {
    0: 'Masukkan password',
    1: 'Sangat Lemah',
    2: 'Lemah',
    3: 'Cukup',
    4: 'Kuat',
    5: 'Sangat Kuat'
  }
  
  return { score, label: labels[score] }
})

// Check if password meets all requirements
const isPasswordValid = computed(() => {
  const checks = passwordChecks.value
  return checks.minLength && checks.hasUpper && checks.hasLower && checks.hasNumber && checks.hasSymbol
})

const registerCompany = async () => {
  console.log('=== registerCompany called ===')
  console.log('company.name:', company.name)
  error.value = ''
  
  if (!company.name.trim()) {
    error.value = 'Company name is required'
    return
  }
  
  loading.value = true
  
  try {
    const response: any = await $fetch('/api/saas/register-tenant', {
      method: 'POST',
      body: {
        name: company.name,
        domain: company.domain || null,
        currency: company.currency,
        timezone: company.timezone
      }
    })
    
    console.log('API Response:', response)
    tenantId.value = response.id
    companyCode.value = response.company_code
    console.log('Setting step to 2')
    step.value = 2
    console.log('Step is now:', step.value)
    
  } catch (e: any) {
    console.error('Register error:', e)
    const errorDetail = e.data?.detail || e.message || 'Failed to register company'
    
    // Check if domain already registered - auto-redirect to step 2
    if (errorDetail.toLowerCase().includes('domain') && errorDetail.toLowerCase().includes('exist')) {
      console.log('Domain already exists, fetching existing tenant...')
      try {
        // Try to find company by domain
        const existingTenant: any = await $fetch(`/api/saas/find-by-domain/${company.domain}`)
        if (existingTenant) {
          company.name = existingTenant.name
          tenantId.value = existingTenant.id
          companyCode.value = existingTenant.company_code
          step.value = 2
          error.value = ''
          return
        }
      } catch (findError) {
        console.error('Could not find existing tenant:', findError)
      }
    }
    
    // Check if name already registered - auto-redirect to step 2
    if (errorDetail.toLowerCase().includes('already') && errorDetail.toLowerCase().includes('exist')) {
      console.log('Company already exists, fetching existing tenant...')
      try {
        // Try to find company by name
        const existingTenant: any = await $fetch(`/api/saas/find-by-name/${encodeURIComponent(company.name)}`)
        if (existingTenant) {
          tenantId.value = existingTenant.id
          companyCode.value = existingTenant.company_code
          step.value = 2
          error.value = ''
          return
        }
      } catch (findError) {
        console.error('Could not find existing tenant:', findError)
      }
    }
    
    error.value = errorDetail
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
  
  if (!isPasswordValid.value) {
    error.value = 'Password harus memenuhi semua persyaratan'
    return
  }
  
  loading.value = true
  
  try {
    const response: any = await $fetch('/api/saas/register-owner', {
      method: 'POST',
      body: {
        tenant_id: tenantId.value,
        username: owner.username,
        email: owner.email,
        password: owner.password,
        full_name: owner.fullName || null
      }
    })
    
    success.value = 'Account created! Redirecting to verify email...'
    
    // Pass OTP code in URL for dev mode auto-fill
    const otpParam = response.otp_code ? `&otp=${response.otp_code}` : ''
    setTimeout(() => {
      navigateTo(`/auth/verify?email=${encodeURIComponent(owner.email)}${otpParam}`)
    }, 1500)
    
  } catch (e: any) {
    console.error('Register owner error:', e)
    error.value = e.data?.detail || e.message || 'Failed to register owner'
  } finally {
    loading.value = false
  }
}
</script>
