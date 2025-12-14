<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Vendors</h2>
      <UButton icon="i-heroicons-plus" color="primary" @click="isOpen = true">Add Vendor</UButton>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="vendors" :loading="loading" />
    </UCard>

    <!-- Create Modal -->
    <UModal v-model="isOpen">
      <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }">
        <template #header>
          <h3 class="text-base font-semibold leading-6 text-gray-900">
            Add Vendor
          </h3>
        </template>

        <form @submit.prevent="createVendor" class="space-y-4">
            <UFormGroup label="Name" name="name" required>
                <UInput v-model="form.name" placeholder="Vendor Name" />
            </UFormGroup>
            
            <UFormGroup label="Code" name="code" required>
                <UInput v-model="form.code" placeholder="V-001" />
            </UFormGroup>

            <UFormGroup label="Email" name="email">
                <UInput v-model="form.email" placeholder="contact@vendor.com" />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-4">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" :loading="submitting">Save</UButton>
            </div>
        </form>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const vendors = ref([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'email', label: 'Email' }
]

const form = reactive({
    name: '',
    code: '',
    email: ''
})

const fetchVendors = async () => {
    loading.value = true
    try {
        const res = await $api.get('/procurement/vendors')
        vendors.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const createVendor = async () => {
    submitting.value = true
    try {
        await $api.post('/procurement/vendors', form)
        isOpen.value = false
        form.name = ''
        form.code = ''
        form.email = ''
        fetchVendors()
    } catch (e) {
        alert('Failed to create vendor')
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchVendors()
})
</script>
