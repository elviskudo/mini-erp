<template>
  <div class="min-h-screen bg-gradient-to-br from-pink-50 via-white to-purple-50 flex items-center justify-center p-4">
    <div class="max-w-md w-full">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Select Tenant</h1>
        <p class="text-gray-600 mt-2">Choose which organization to access</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-pink-500 border-t-transparent"></div>
      </div>

      <!-- Tenant List -->
      <div v-else-if="tenants.length > 0" class="space-y-4">
        <div
          v-for="tenant in tenants"
          :key="tenant.id"
          @click="selectTenant(tenant)"
          class="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all cursor-pointer border-2 border-transparent hover:border-pink-500"
          :class="{ 'opacity-50 cursor-not-allowed': !tenant.is_active }"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-full bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center">
                <span class="text-white font-bold text-lg">{{ tenant.name.charAt(0).toUpperCase() }}</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900">{{ tenant.name }}</h3>
                <p class="text-sm text-gray-500">{{ getRoleDisplay(tenant.role) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span
                v-if="!tenant.is_active"
                class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full"
              >
                Inactive
              </span>
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- No Tenants -->
      <div v-else class="text-center py-12">
        <div class="text-6xl mb-4">🏢</div>
        <h3 class="text-lg font-semibold text-gray-900">No Organizations Found</h3>
        <p class="text-gray-500 mt-2">You don't have access to any organization.</p>
        <button
          @click="logout"
          class="mt-6 px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
        >
          Back to Login
        </button>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-600 rounded-lg text-center">
        {{ error }}
      </div>

      <!-- Register New Company Link -->
      <div class="mt-8 text-center border-t pt-6">
        <p class="text-gray-500 text-sm mb-3">Want to create a new organization?</p>
        <NuxtLink 
          to="/auth/register-company" 
          class="inline-flex items-center gap-2 text-pink-600 hover:text-pink-700 font-medium"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Register New Company
        </NuxtLink>
      </div>

      <!-- Switching State -->
      <div v-if="switching" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl p-8 text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-pink-500 border-t-transparent mx-auto"></div>
          <p class="mt-4 text-gray-600">Switching to {{ selectedTenant?.name }}...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'blank',
  middleware: 'auth'
})

interface TenantWithRole {
  id: string
  name: string
  slug?: string
  role: string
  is_active: boolean
}

const authStore = useAuthStore()
const router = useRouter()

const tenants = ref<TenantWithRole[]>([])
const loading = ref(true)
const switching = ref(false)
const error = ref('')
const selectedTenant = ref<TenantWithRole | null>(null)

onMounted(async () => {
  await loadTenants()
})

async function loadTenants() {
  loading.value = true
  error.value = ''
  try {
    tenants.value = await authStore.fetchUserTenants()
    
    // If only 1 tenant, auto-select it
    if (tenants.value.length === 1 && tenants.value[0].is_active) {
      await selectTenant(tenants.value[0])
    }
  } catch (e) {
    error.value = 'Failed to load organizations'
  } finally {
    loading.value = false
  }
}

async function selectTenant(tenant: TenantWithRole) {
  if (!tenant.is_active) {
    error.value = 'This organization is inactive. Please contact your administrator.'
    return
  }
  
  switching.value = true
  selectedTenant.value = tenant
  error.value = ''
  
  try {
    const success = await authStore.switchTenant(tenant.id)
    if (success) {
      await router.push('/')
    } else {
      error.value = 'Failed to switch organization'
    }
  } catch (e) {
    error.value = 'Failed to switch organization'
  } finally {
    switching.value = false
  }
}

function getRoleDisplay(role: string) {
  const roleMap: Record<string, string> = {
    OWNER: 'Owner',
    ADMIN: 'Administrator',
    MANAGER: 'Manager',
    MEMBER: 'Member',
    VIEWER: 'Viewer'
  }
  return roleMap[role] || role
}

function logout() {
  authStore.logout()
}
</script>
