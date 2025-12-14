<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900">Create Account</h1>
          <p class="text-gray-500 mt-1">Register for Mini ERP</p>
        </div>
      </template>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <!-- Tenant Selection -->
        <UFormGroup label="Organization" name="tenant" :error="errors.tenant">
          <div class="space-y-2">
            <div class="flex gap-2">
              <URadio v-model="tenantMode" value="existing" label="Join Existing" />
              <URadio v-model="tenantMode" value="new" label="Create New" />
            </div>
            
            <!-- Existing Tenant Dropdown -->
            <USelect 
              v-if="tenantMode === 'existing'"
              v-model="form.tenantId" 
              :options="tenantOptions"
              placeholder="Select organization"
              :loading="loadingTenants"
              :color="errors.tenant ? 'red' : undefined"
            />
            
            <!-- New Tenant Form -->
            <div v-if="tenantMode === 'new'" class="space-y-2">
              <UInput 
                v-model="newTenant.name" 
                placeholder="Organization name"
                :color="errors.tenant ? 'red' : undefined"
              />
              <UInput 
                v-model="newTenant.domain" 
                placeholder="Domain (optional, e.g. acme)"
              />
            </div>
          </div>
        </UFormGroup>

        <UFormGroup label="Username" name="username" :error="errors.username" required>
          <UInput 
            v-model="form.username" 
            icon="i-heroicons-user" 
            placeholder="Enter username (3-50 chars)"
            :color="errors.username ? 'red' : undefined"
            @blur="validateUsername"
          />
          <template #hint>
            <span class="text-xs text-gray-400">Letters, numbers, and underscores only</span>
          </template>
        </UFormGroup>

        <UFormGroup label="Email" name="email" :error="errors.email" required>
          <UInput 
            v-model="form.email" 
            type="email"
            icon="i-heroicons-envelope" 
            placeholder="Enter email address"
            :color="errors.email ? 'red' : undefined"
            @blur="validateEmail"
          />
        </UFormGroup>
        
        <UFormGroup label="Password" name="password" :error="errors.password" required>
          <UInput 
            v-model="form.password" 
            type="password" 
            icon="i-heroicons-lock-closed" 
            placeholder="Enter password (6-72 chars)"
            :color="errors.password ? 'red' : undefined"
            @blur="validatePassword"
          />
          <template #hint>
            <span class="text-xs text-gray-400">Minimum 6 characters, maximum 72</span>
          </template>
        </UFormGroup>

        <UFormGroup label="Confirm Password" name="confirmPassword" :error="errors.confirmPassword" required>
          <UInput 
            v-model="form.confirmPassword" 
            type="password" 
            icon="i-heroicons-lock-closed" 
            placeholder="Confirm your password"
            :color="errors.confirmPassword ? 'red' : undefined"
            @blur="validateConfirmPassword"
          />
        </UFormGroup>

        <UFormGroup label="Role" name="role">
          <USelect 
            v-model="form.role" 
            :options="roleOptions"
            placeholder="Select role"
          />
        </UFormGroup>

        <UAlert v-if="error" color="red" variant="soft" :title="error" icon="i-heroicons-exclamation-triangle" />
        <UAlert v-if="success" color="green" variant="soft" :title="success" icon="i-heroicons-check-circle" />

        <UButton type="submit" block :loading="loading">
          Create Account
        </UButton>

        <div class="text-center text-sm text-gray-500">
          Already have an account? 
          <NuxtLink to="/auth/login" class="text-primary-500 hover:underline">Sign in</NuxtLink>
        </div>
      </form>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const { $api } = useNuxtApp()
const router = useRouter()

// Tenant state
const tenantMode = ref<'existing' | 'new'>('existing')
const loadingTenants = ref(false)
const tenantOptions = ref<Array<{label: string, value: string}>>([])
const newTenant = reactive({
  name: '',
  domain: ''
})

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'Operator',
  tenantId: ''
})

const errors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  tenant: ''
})

const error = ref('')
const success = ref('')
const loading = ref(false)

const roleOptions = [
  { label: 'Operator', value: 'Operator' },
  { label: 'Manager', value: 'Manager' },
  { label: 'Lab Tech', value: 'Lab_Tech' }
]

// Load tenants on mount
onMounted(async () => {
  await loadTenants()
})

const loadTenants = async () => {
  loadingTenants.value = true
  try {
    const response = await $api.get('/tenants/')
    tenantOptions.value = response.data.map((t: any) => ({
      label: t.name + (t.domain ? ` (${t.domain})` : ''),
      value: t.id
    }))
  } catch (e) {
    console.error('Failed to load tenants', e)
  } finally {
    loadingTenants.value = false
  }
}

// Validation functions
const validateUsername = () => {
  if (!form.username) {
    errors.username = 'Username is required'
  } else if (form.username.length < 3) {
    errors.username = 'Username must be at least 3 characters'
  } else if (form.username.length > 50) {
    errors.username = 'Username cannot exceed 50 characters'
  } else if (!/^[a-zA-Z0-9_]+$/.test(form.username)) {
    errors.username = 'Username can only contain letters, numbers, and underscores'
  } else {
    errors.username = ''
  }
}

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email) {
    errors.email = 'Email is required'
  } else if (!emailRegex.test(form.email)) {
    errors.email = 'Please enter a valid email address'
  } else {
    errors.email = ''
  }
}

const validatePassword = () => {
  if (!form.password) {
    errors.password = 'Password is required'
  } else if (form.password.length < 6) {
    errors.password = 'Password must be at least 6 characters'
  } else if (form.password.length > 72) {
    errors.password = 'Password cannot exceed 72 characters'
  } else {
    errors.password = ''
  }
  if (form.confirmPassword) {
    validateConfirmPassword()
  }
}

const validateConfirmPassword = () => {
  if (!form.confirmPassword) {
    errors.confirmPassword = 'Please confirm your password'
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
  } else {
    errors.confirmPassword = ''
  }
}

const validateTenant = () => {
  if (tenantMode.value === 'existing' && !form.tenantId) {
    errors.tenant = 'Please select an organization'
    return false
  }
  if (tenantMode.value === 'new' && !newTenant.name) {
    errors.tenant = 'Please enter organization name'
    return false
  }
  errors.tenant = ''
  return true
}

const handleRegister = async () => {
  // Validate all fields before submit
  validateUsername()
  validateEmail()
  validatePassword()
  validateConfirmPassword()
  
  if (!validateTenant()) {
    return
  }
  
  if (errors.username || errors.email || errors.password || errors.confirmPassword) {
    return
  }

  error.value = ''
  success.value = ''
  loading.value = true
  
  try {
    let tenantId = form.tenantId
    
    // Create new tenant if needed
    if (tenantMode.value === 'new') {
      const tenantResponse = await $api.post('/tenants/', {
        name: newTenant.name,
        domain: newTenant.domain || null
      })
      tenantId = tenantResponse.data.id
    }
    
    // Register user
    await $api.post('/auth/register', {
      username: form.username,
      email: form.email,
      password: form.password,
      role: form.role,
      tenant_id: tenantId || null
    })
    
    success.value = 'Account created! Please check your email for verification code.'
    
    setTimeout(() => {
      navigateTo(`/auth/verify?email=${encodeURIComponent(form.email)}`)
    }, 1500)
    
  } catch (e: any) {
    console.error(e)
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (Array.isArray(detail)) {
        error.value = detail.map((d: any) => d.msg).join(', ')
      } else {
        error.value = detail
      }
    } else {
      error.value = 'Registration failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
