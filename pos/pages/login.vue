<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <UCard class="shadow-xl">
        <template #header>
          <div class="text-center">
            <div class="w-16 h-16 bg-orange-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <UIcon name="i-heroicons-shopping-cart" class="w-8 h-8 text-white" />
            </div>
            <h1 class="text-2xl font-bold text-gray-900">POS Login</h1>
            <p class="text-gray-500 mt-1">Sign in to access the Point of Sale</p>
          </div>
        </template>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <UFormGroup label="Username" required>
            <UInput 
              v-model="form.username" 
              type="text" 
              placeholder="Enter username"
              size="lg"
              icon="i-heroicons-user"
            />
          </UFormGroup>

          <UFormGroup label="Password" required>
            <UInput 
              v-model="form.password" 
              type="password" 
              placeholder="••••••••"
              size="lg"
              icon="i-heroicons-lock-closed"
            />
          </UFormGroup>

          <UAlert v-if="error" color="red" variant="soft" icon="i-heroicons-exclamation-triangle">
            {{ error }}
          </UAlert>

          <UButton 
            type="submit" 
            block 
            size="lg" 
            color="orange"
            :loading="loading"
          >
            <UIcon name="i-heroicons-arrow-right-on-rectangle" class="mr-2" />
            Sign In
          </UButton>
        </form>

        <template #footer>
          <p class="text-center text-sm text-gray-500">
            Only <strong>Admin</strong>, <strong>Manager</strong>, and <strong>Cashier</strong> roles can access POS
          </p>
        </template>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const { $api } = useNuxtApp()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

// Check for unauthorized error from middleware
if (route.query.error === 'unauthorized') {
  error.value = 'You do not have permission to access POS. Only Admin, Manager, and Cashier roles are allowed.'
}

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    const response = await $api.post('/auth/login', {
      username: form.username,
      password: form.password
    })

    const { access_token, user } = response.data

    // Check if user has POS access
    const allowedRoles = ['ADMIN', 'MANAGER', 'CASHIER']
    if (!allowedRoles.includes(user.role)) {
      error.value = 'You do not have permission to access POS'
      return
    }

    authStore.setAuth(access_token, user)
    router.push('/pos')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Invalid email or password'
  } finally {
    loading.value = false
  }
}
</script>
