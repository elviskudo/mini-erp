<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <UCard class="w-full max-w-sm">
      <template #header>
        <div class="text-center">
            <h1 class="text-2xl font-bold text-gray-900">Mini ERP</h1>
            <p class="text-gray-500 mt-1">Sign in to your account</p>
        </div>
      </template>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <UFormGroup label="Username" name="username" :error="errors.username">
            <UInput 
              v-model="username" 
              icon="i-heroicons-user" 
              placeholder="Enter username"
              :color="errors.username ? 'red' : undefined"
            />
        </UFormGroup>
        
        <UFormGroup label="Password" name="password" :error="errors.password">
            <UInput 
              v-model="password" 
              type="password" 
              icon="i-heroicons-lock-closed" 
              placeholder="Enter password"
              :color="errors.password ? 'red' : undefined"
            />
        </UFormGroup>

        <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-exclamation-triangle" />

        <UButton type="submit" block :loading="loading">
            Sign In
        </UButton>
      </form>
    </UCard>
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

        const response = await $api.post('/auth/token', formData, {
             headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
        
        authStore.setToken(response.data.access_token)
        navigateTo('/')
        
    } catch (e: any) {
        console.error(e)
        error.value = e.response?.data?.detail || 'Login failed. Check credentials.'
    } finally {
        loading.value = false
    }
}
</script>
