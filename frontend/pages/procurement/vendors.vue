<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Vendors</h2>
        <p class="text-gray-500">Manage supplier and vendor records</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Add Vendor</UButton>
    </div>

    <UCard :ui="{ body: { padding: '' } }">
      <UTable :columns="columns" :rows="vendors" :loading="loading">
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
        </template>
      </UTable>
    </UCard>

    <!-- Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Vendor' : 'Add Vendor'"
      :loading="submitting"
      @submit="saveVendor"
    >
      <div class="space-y-4">
        <UFormGroup label="Name" required>
          <UInput v-model="form.name" placeholder="Vendor Name" />
        </UFormGroup>
        
        <UFormGroup label="Code" required>
          <UInput v-model="form.code" placeholder="V-001" />
        </UFormGroup>

        <UFormGroup label="Email">
          <UInput v-model="form.email" type="email" placeholder="contact@vendor.com" />
        </UFormGroup>
        
        <UFormGroup label="Phone">
          <UInput v-model="form.phone" placeholder="+62..." />
        </UFormGroup>
        
        <UFormGroup label="Address">
          <UTextarea v-model="form.address" rows="3" placeholder="Vendor address" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const toast = useToast()
const isOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)
const editMode = ref(false)
const vendors = ref<any[]>([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { key: 'phone', label: 'Phone' },
  { key: 'actions', label: '' }
]

const form = reactive({
    id: '',
    name: '',
    code: '',
    email: '',
    phone: '',
    address: ''
})

const resetForm = () => {
    Object.assign(form, {
        id: '',
        name: '',
        code: '',
        email: '',
        phone: '',
        address: ''
    })
}

const fetchVendors = async () => {
    loading.value = true
    try {
        const res: any = await $fetch('/api/procurement/vendors')
        vendors.value = res
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const openCreate = () => {
    resetForm()
    editMode.value = false
    isOpen.value = true
}

const openEdit = (row: any) => {
    Object.assign(form, row)
    editMode.value = true
    isOpen.value = true
}

const saveVendor = async () => {
    submitting.value = true
    try {
        if (editMode.value) {
            await $fetch(`/api/procurement/vendors/${form.id}`, {
                method: 'PUT',
                body: form
            })
            toast.add({ title: 'Updated', description: 'Vendor updated.' })
        } else {
            await $fetch('/api/procurement/vendors', {
                method: 'POST', 
                body: form
            })
            toast.add({ title: 'Created', description: 'Vendor created.' })
        }
        isOpen.value = false
        fetchVendors()
        resetForm()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to save vendor.', color: 'red' })
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchVendors()
})
</script>
