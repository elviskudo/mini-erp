<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Sign in to NAIKIN
      </h2>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <div v-if="$route.query.registered" class="mb-4 bg-green-50 p-4 rounded-md text-green-700 text-sm">
          Registration successful! Please sign in.
        </div>

        <form class="space-y-6" @submit.prevent="handleLogin">
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
            <div class="mt-1">
              <input id="username" v-model="form.username" type="text" required class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-pink-500 focus:border-pink-500 sm:text-sm" />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
            <div class="mt-1">
              <input id="password" v-model="form.password" type="password" required class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-pink-500 focus:border-pink-500 sm:text-sm" />
            </div>
          </div>

          <div>
            <button type="submit" :disabled="loading" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-pink-600 hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500">
              <span v-if="loading">Signing in...</span>
              <span v-else>Sign in</span>
            </button>
          </div>

          <div v-if="error" class="text-red-500 text-sm">
            {{ error }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'blank'
})

const { $api } = useNuxtApp()
const authStore = useAuthStore()
const router = useRouter()

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('username', form.username)
    formData.append('password', form.password)

    const res: any = await $api.post('/auth/token', formData)
    authStore.setToken(res.data.access_token)
    
    // Fetch tenants and switch to NAIKIN
    const tenants = await authStore.fetchUserTenants()
    const naikinTenant = tenants.find((t: any) => t.slug === 'naikin')
    
    if (naikinTenant) {
      await authStore.switchTenant(naikinTenant.id)
      router.push('/naikin/dashboard')
    } else {
      error.value = 'You are not a member of NAIKIN service'
    }
  } catch (e: any) {
    console.error(e)
    error.value = 'Invalid credentials or login failed'
  } finally {
    loading.value = false
  }
}
</script>
