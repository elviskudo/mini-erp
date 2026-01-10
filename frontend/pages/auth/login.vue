<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-purple-100">
    <!-- Decorative background elements -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
    </div>

    <div class="w-full max-w-md relative z-10">
      <!-- Logo/Brand -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-pink-500 to-purple-500 rounded-2xl shadow-gumroad-lg mb-4">
          <span class="text-2xl font-bold text-white">ME</span>
        </div>
        <h1 class="text-3xl font-bold text-gray-900">Mini ERP</h1>
        <p class="text-gray-500 mt-1">Welcome back! Sign in to continue.</p>
      </div>

      <UCard class="shadow-xl border-0 backdrop-blur-sm bg-white/90">
        <form @submit.prevent="handleLogin" class="space-y-5">
          <UFormGroup label="Username" name="username" :error="errors.username">
            <UInput 
              v-model="username" 
              icon="i-heroicons-user" 
              placeholder="Enter username"
              size="lg"
              :color="errors.username ? 'red' : undefined"
            />
          </UFormGroup>
          
          <UFormGroup label="Password" name="password" :error="errors.password">
            <UInput 
              v-model="password" 
              type="password" 
              icon="i-heroicons-lock-closed" 
              placeholder="Enter password"
              size="lg"
              :color="errors.password ? 'red' : undefined"
            />
          </UFormGroup>

          <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-exclamation-triangle" />

          <UButton type="submit" block size="lg" :loading="loading" color="pink" class="font-semibold shadow-gumroad hover:shadow-gumroad-lg transition-shadow">
            Sign In →
          </UButton>
        </form>

        <template #footer>
          <div class="text-center space-y-3 pt-2">
            <p class="text-sm text-gray-500">
              New to Mini ERP? 
              <NuxtLink to="/auth/register-company" class="text-pink-600 hover:text-pink-700 font-medium">
                Create a company
              </NuxtLink>
            </p>
            <p class="text-sm text-gray-500">
              Want to join an existing company? 
              <NuxtLink to="/auth/join-company" class="text-pink-600 hover:text-pink-700 font-medium">
                Enter code
              </NuxtLink>
            </p>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  layout: false
})

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const errors = reactive({
  username: '',
  password: ''
})

const authStore = useAuthStore()
const { $api } = useNuxtApp()
const router = useRouter()

// Simple check - button enabled when both fields have content
const isFormFilled = computed(() => {
  return username.value.trim() !== '' && password.value !== ''
})

// Validation functions (called on submit)
const validateForm = () => {
  let isValid = true
  
  // Username validation
  if (!username.value.trim()) {
    errors.username = 'Username is required'
    isValid = false
  } else if (username.value.length < 3) {
    errors.username = 'Username must be at least 3 characters'
    isValid = false
  } else {
    errors.username = ''
  }

  // Password validation
  if (!password.value) {
    errors.password = 'Password is required'
    isValid = false
  } else if (password.value.length < 6) {
    errors.password = 'Password must be at least 6 characters'
    isValid = false
  } else if (password.value.length > 72) {
    errors.password = 'Password cannot exceed 72 characters'
    isValid = false
  } else {
    errors.password = ''
  }

  return isValid
}

const handleLogin = async () => {
    // Clear previous errors
    errors.username = ''
    errors.password = ''
    error.value = ''
    
    // Validate form
    if (!validateForm()) {
      return
    }

    loading.value = true
    try {
        const formData = new FormData()
        formData.append('username', username.value)
        formData.append('password', password.value)

        // Login to get token
        const response: any = await $api.post('/auth/token', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        
        authStore.setToken(response.data.access_token)
        
        // Fetch user details and tenant info
        try {
          const user: any = await $api.get('/auth/me')
          
          if (user.data.tenant_id) {
             // Fetch tenant details including timezone
             try {
               const tenant: any = await $api.get(`/tenants/${user.data.tenant_id}`)
               authStore.setTenant({
                 id: tenant.data.id,
                 name: tenant.data.name,
                 company_code: tenant.data.domain,
                 timezone: tenant.data.timezone || 'UTC',
                 currency: tenant.data.currency || 'USD'
               })
             } catch (tenantError) {
               console.error('Failed to fetch tenant details:', tenantError)
             }
          }
        } catch (meError) {
          console.error('Failed to fetch user details:', meError)
        }

        // Force reload to ensure cookie is picked up by middleware/plugins
        window.location.href = '/'
        
    } catch (e: any) {
        console.error(e)
        error.value = e.data?.detail || 'Login failed. Check credentials.'
    } finally {
        loading.value = false
    }
}
</script>
