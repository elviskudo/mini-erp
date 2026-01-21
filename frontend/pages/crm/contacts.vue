<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Contacts</h1>
        <p class="text-gray-500">Manage contact persons at companies</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Contact</UButton>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable
        :columns="columns"
        :data="contacts"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @limit-change="handleLimitChange"
      >
        <template #name-data="{ row }">
          <div class="font-medium">{{ row.first_name }} {{ row.last_name || '' }}</div>
          <div class="text-xs text-gray-500">{{ row.position || '' }}</div>
        </template>
        <template #is_primary-data="{ row }">
          <UBadge v-if="row.is_primary" color="yellow" variant="subtle">Primary</UBadge>
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="confirmDelete(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <!-- Create/Edit Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Contact' : 'New Contact'"
      :loading="saving"
      @submit="save"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="First Name" required>
            <UInput v-model="form.first_name" placeholder="John" />
          </UFormGroup>
          <UFormGroup label="Last Name">
            <UInput v-model="form.last_name" placeholder="Doe" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Company">
          <USelectMenu 
            v-model="form.company_id" 
            :options="companyOptions" 
            value-attribute="value"
            option-attribute="label"
            searchable
            placeholder="Select Company..." 
          />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Position">
            <UInput v-model="form.position" placeholder="Sales Manager" />
          </UFormGroup>
          <UFormGroup label="Department">
            <UInput v-model="form.department" placeholder="Sales" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Email">
          <UInput v-model="form.email" type="email" placeholder="john.doe@example.com" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Phone">
            <UInput v-model="form.phone" placeholder="+62 21 1234567" />
          </UFormGroup>
          <UFormGroup label="Mobile">
            <UInput v-model="form.mobile" placeholder="+62 812 3456789" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="LinkedIn">
          <UInput v-model="form.linkedin" placeholder="https://linkedin.com/in/johndoe" />
        </UFormGroup>
        
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" placeholder="Additional notes..." rows="3" />
        </UFormGroup>
        
        <div class="flex gap-6">
          <UFormGroup>
            <UCheckbox v-model="form.is_primary" label="Primary Contact" />
          </UFormGroup>
          <UFormGroup>
            <UCheckbox v-model="form.is_active" label="Active" />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const { $api } = useNuxtApp()
const toast = useToast()
const authStore = useAuthStore()

definePageMeta({ middleware: 'auth' })

// State
const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const editMode = ref(false)

const contacts = ref([])
const companies = ref<any[]>([])
const pagination = ref(null)
const currentPage = ref(1)
const currentLimit = ref(10)

const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'is_primary', label: '' },
    { key: 'is_active', label: 'Status' },
    { key: 'actions', label: '' }
]

const companyOptions = computed(() => companies.value.map(c => ({ label: c.name, value: c.id })))

// Form
const form = reactive({
    id: '',
    first_name: '',
    last_name: '',
    company_id: '',
    position: '',
    department: '',
    email: '',
    phone: '',
    mobile: '',
    linkedin: '',
    notes: '',
    is_primary: false,
    is_active: true
})

// Actions
const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/crm/contacts', { params: { page: currentPage.value, limit: currentLimit.value } })
        if (res.data?.success || Array.isArray(res.data?.data)) {
            contacts.value = res.data.data || []
            pagination.value = res.data.meta?.pagination
        }
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to load contacts', color: 'red' })
    } finally {
        loading.value = false
    }
    loadCompanies()
}

const loadCompanies = async () => {
    try {
        const res = await $api.get('/crm/companies', { params: { limit: 100 } })
        companies.value = res.data?.data || []
    } catch(e) {
        console.error('Failed to load companies', e)
    }
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const handleLimitChange = (l: number) => { currentLimit.value = l; fetchData() }

const openCreate = () => {
    resetForm()
    editMode.value = false
    if (companies.value.length === 0) loadCompanies()
    isOpen.value = true
}

const openEdit = (row: any) => {
    resetForm()
    editMode.value = true
    Object.assign(form, row)
    isOpen.value = true
}

const resetForm = () => {
    Object.assign(form, {
        id: '', first_name: '', last_name: '', company_id: '', position: '', department: '',
        email: '', phone: '', mobile: '', linkedin: '', notes: '', is_primary: false, is_active: true
    })
}

const save = async () => {
    if (!form.first_name) return toast.add({ title: 'Validation', description: 'First name is required', color: 'red' })

    saving.value = true
    try {
        if (editMode.value) {
            await $api.put(`/crm/contacts/${form.id}`, form)
            toast.add({ title: 'Updated', description: 'Contact updated successfully.' })
        } else {
            await $api.post('/crm/contacts', form)
            toast.add({ title: 'Created', description: 'Contact created successfully.' })
        }
        isOpen.value = false
        fetchData()
        resetForm()
    } catch(e: any) {
        toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed to save', color: 'red' })
    } finally {
        saving.value = false
    }
}

const confirmDelete = async (row: any) => {
    if (!confirm(`Delete contact "${row.first_name} ${row.last_name || ''}"?`)) return
    try {
        await $api.delete(`/crm/contacts/${row.id}`)
        toast.add({ title: 'Deleted', description: 'Contact deleted.' })
        fetchData()
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' })
    }
}

onMounted(() => fetchData())
</script>
