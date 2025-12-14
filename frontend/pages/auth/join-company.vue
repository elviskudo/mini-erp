<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-purple-100">
    <div class="w-full max-w-md">
      <!-- Step 1: Find Company -->
      <UCard v-if="step === 1" class="shadow-xl">
        <template #header>
          <div class="text-center">
            <h1 class="text-2xl font-bold text-gray-900">Join Your Company</h1>
            <p class="text-gray-500 mt-1">Enter your company code to get started</p>
          </div>
        </template>

        <form @submit.prevent="findCompany" class="space-y-4">
          <UFormGroup label="Company Code" required>
            <UInput 
              v-model="companyCode" 
              placeholder="ABC123"
              class="text-center text-2xl tracking-widest uppercase"
              maxlength="6"
            />
          </UFormGroup>

          <div v-if="foundCompany" class="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p class="text-sm text-green-600">Found company:</p>
            <p class="font-bold text-green-800 text-lg">{{ foundCompany.name }}</p>
          </div>

          <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-x-circle" />

          <UButton type="submit" block size="lg" :loading="loading" color="pink">
            {{ foundCompany ? 'Continue →' : 'Find Company' }}
          </UButton>
        </form>

        <template #footer>
          <p class="text-center text-sm text-gray-500">
            Want to register a new company? 
            <NuxtLink to="/auth/register-company" class="text-pink-500 hover:underline">Register here</NuxtLink>
          </p>
        </template>
      </UCard>

      <!-- Step 2: Register as Employee -->
      <UCard v-else class="shadow-xl">
        <template #header>
          <div class="text-center">
            <h1 class="text-2xl font-bold text-gray-900">Create Your Account</h1>
            <p class="text-gray-500 mt-1">Joining <strong>{{ foundCompany?.name }}</strong></p>
          </div>
        </template>

        <form @submit.prevent="requestJoin" class="space-y-4">
          <UFormGroup label="Full Name">
            <UInput v-model="form.fullName" placeholder="John Doe" />
          </UFormGroup>

          <UFormGroup label="Username" required>
            <UInput v-model="form.username" placeholder="johndoe" />
          </UFormGroup>

          <UFormGroup label="Email" required>
            <UInput v-model="form.email" type="email" placeholder="john@company.com" />
          </UFormGroup>

          <UFormGroup label="Password" required>
            <UInput v-model="form.password" type="password" placeholder="Min 6 characters" />
          </UFormGroup>

          <UAlert color="blue" variant="soft" icon="i-heroicons-information-circle">
            Your join request will need approval from your company admin.
          </UAlert>

          <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-x-circle" />
          <UAlert v-if="success" color="green" variant="soft" :title="success" icon="i-heroicons-check-circle" />

          <div class="flex space-x-3">
            <UButton variant="outline" @click="step = 1" :disabled="loading">
              ← Back
            </UButton>
            <UButton type="submit" class="flex-1" size="lg" :loading="loading" color="pink">
              Request to Join
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
const companyCode = ref('')
const foundCompany = ref<{ id: string; name: string; company_code: string } | null>(null)

const form = reactive({
  fullName: '',
  username: '',
  email: '',
  password: ''
})

const findCompany = async () => {
  error.value = ''
  
  if (!companyCode.value.trim() || companyCode.value.length !== 6) {
    error.value = 'Please enter a valid 6-character company code'
    return
  }
  
  // If already found, go to step 2
  if (foundCompany.value) {
    step.value = 2
    return
  }
  
  loading.value = true
  
  try {
    const response = await $api.get(`/saas/find-company/${companyCode.value.toUpperCase()}`)
    foundCompany.value = response.data
    step.value = 2
    
  } catch (e: any) {
    if (e.response?.status === 404) {
      error.value = 'Company not found. Please check the code and try again.'
    } else {
      error.value = e.response?.data?.detail || 'Failed to find company'
    }
  } finally {
    loading.value = false
  }
}

const requestJoin = async () => {
  error.value = ''
  success.value = ''
  
  if (!form.username || !form.email || !form.password) {
    error.value = 'All required fields must be filled'
    return
  }
  
  if (form.password.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  
  loading.value = true
  
  try {
    await $api.post('/saas/request-join', {
      company_code: companyCode.value.toUpperCase(),
      username: form.username,
      email: form.email,
      password: form.password,
      full_name: form.fullName || null
    })
    
    success.value = 'Request submitted! Please verify your email.'
    
    setTimeout(() => {
      navigateTo(`/auth/verify?email=${encodeURIComponent(form.email)}`)
    }, 2000)
    
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to submit join request'
  } finally {
    loading.value = false
  }
}
</script>
