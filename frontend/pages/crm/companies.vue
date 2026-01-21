<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Companies</h1>
        <p class="text-gray-500">Manage B2B companies and organizations</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Company</UButton>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable
        :columns="columns"
        :data="companies"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @limit-change="handleLimitChange"
      >
        <template #size-data="{ row }">
          <UBadge v-if="row.size" :color="getSizeColor(row.size)" variant="subtle">{{ row.size }}</UBadge>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="viewCompany(row)" />
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="confirmDelete(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <!-- Create/Edit Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Company' : 'New Company'"
      :loading="saving"
      @submit="save"
    >
      <div class="space-y-4">
        <UFormGroup label="Company Name" required>
          <UInput v-model="form.name" placeholder="PT Example Corp" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Industry">
            <USelectMenu v-model="form.industry" :options="industries" placeholder="Select..." />
          </UFormGroup>
          <UFormGroup label="Company Size">
            <USelectMenu v-model="form.size" :options="sizes" placeholder="Select..." />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Website">
          <UInput v-model="form.website" placeholder="https://example.com" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Phone">
            <UInput v-model="form.phone" placeholder="+62 21 1234567" />
          </UFormGroup>
          <UFormGroup label="Email">
            <UInput v-model="form.email" type="email" placeholder="info@example.com" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Address">
          <UTextarea v-model="form.address" placeholder="Full address..." rows="2" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="City">
            <UInput v-model="form.city" placeholder="Jakarta" />
          </UFormGroup>
          <UFormGroup label="Country">
            <UInput v-model="form.country" placeholder="Indonesia" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Tax ID (NPWP)">
          <UInput v-model="form.tax_id" placeholder="00.000.000.0-000.000" />
        </UFormGroup>
        
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" placeholder="Additional notes..." rows="3" />
        </UFormGroup>
        
        <UFormGroup label="Status">
          <UToggle v-model="form.is_active" label="Active" />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- View Company Detail Modal -->
    <UModal v-model="showDetail" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedCompany">
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">{{ selectedCompany.name }}</h3>
            <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="showDetail = false" />
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div><span class="text-gray-500">Industry:</span> {{ selectedCompany.industry || '-' }}</div>
            <div><span class="text-gray-500">Size:</span> {{ selectedCompany.size || '-' }}</div>
            <div><span class="text-gray-500">Website:</span> {{ selectedCompany.website || '-' }}</div>
            <div><span class="text-gray-500">Phone:</span> {{ selectedCompany.phone || '-' }}</div>
            <div><span class="text-gray-500">Email:</span> {{ selectedCompany.email || '-' }}</div>
            <div><span class="text-gray-500">Tax ID:</span> {{ selectedCompany.tax_id || '-' }}</div>
          </div>
          
          <div v-if="selectedCompany.address" class="text-sm">
            <span class="text-gray-500">Address:</span> {{ selectedCompany.address }}, {{ selectedCompany.city }}, {{ selectedCompany.country }}
          </div>
          
          <div v-if="selectedCompany.contacts && selectedCompany.contacts.length">
            <h4 class="font-medium mb-2">Contacts</h4>
            <div v-for="contact in selectedCompany.contacts" :key="contact.id" class="flex items-center gap-4 p-2 bg-gray-50 rounded mb-2">
              <div class="flex-1">
                <div class="font-medium">{{ contact.first_name }} {{ contact.last_name }}</div>
                <div class="text-sm text-gray-500">{{ contact.position }}</div>
              </div>
              <div class="text-sm">{{ contact.email }}</div>
            </div>
          </div>
        </div>
      </UCard>
    </UModal>
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
const showDetail = ref(false)
const selectedCompany = ref<any>(null)

const companies = ref([])
const pagination = ref(null)
const currentPage = ref(1)
const currentLimit = ref(10)

// Options
const industries = ['Technology', 'Manufacturing', 'Retail', 'Finance', 'Healthcare', 'Education', 'Construction', 'Other']
const sizes = ['SMALL', 'MEDIUM', 'LARGE', 'ENTERPRISE']

const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'industry', label: 'Industry' },
    { key: 'size', label: 'Size' },
    { key: 'phone', label: 'Phone' },
    { key: 'is_active', label: 'Status' },
    { key: 'actions', label: '' }
]

const getSizeColor = (size: string) => {
    const map: Record<string, string> = { 'SMALL': 'gray', 'MEDIUM': 'blue', 'LARGE': 'green', 'ENTERPRISE': 'purple' }
    return map[size] || 'gray'
}

// Form
const form = reactive({
    id: '',
    name: '',
    industry: '',
    website: '',
    size: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    country: '',
    tax_id: '',
    notes: '',
    is_active: true
})

// Actions
const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/crm/companies', { params: { page: currentPage.value, limit: currentLimit.value } })
        if (res.data?.success || Array.isArray(res.data?.data)) {
            companies.value = res.data.data || []
            pagination.value = res.data.meta?.pagination
        }
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to load companies', color: 'red' })
    } finally {
        loading.value = false
    }
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const handleLimitChange = (l: number) => { currentLimit.value = l; fetchData() }

const openCreate = () => {
    resetForm()
    editMode.value = false
    isOpen.value = true
}

const openEdit = (row: any) => {
    resetForm()
    editMode.value = true
    Object.assign(form, row)
    isOpen.value = true
}

const viewCompany = async (row: any) => {
    try {
        const res = await $api.get(`/crm/companies/${row.id}`)
        selectedCompany.value = res.data?.data || row
        showDetail.value = true
    } catch(e) {
        selectedCompany.value = row
        showDetail.value = true
    }
}

const resetForm = () => {
    Object.assign(form, {
        id: '', name: '', industry: '', website: '', size: '', phone: '', email: '',
        address: '', city: '', country: '', tax_id: '', notes: '', is_active: true
    })
}

const save = async () => {
    if (!form.name) return toast.add({ title: 'Validation', description: 'Company name is required', color: 'red' })

    saving.value = true
    try {
        if (editMode.value) {
            await $api.put(`/crm/companies/${form.id}`, form)
            toast.add({ title: 'Updated', description: 'Company updated successfully.' })
        } else {
            await $api.post('/crm/companies', form)
            toast.add({ title: 'Created', description: 'Company created successfully.' })
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
    if (!confirm(`Delete company "${row.name}"?`)) return
    try {
        await $api.delete(`/crm/companies/${row.id}`)
        toast.add({ title: 'Deleted', description: 'Company deleted.' })
        fetchData()
    } catch(e) {
        toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' })
    }
}

onMounted(() => fetchData())
</script>
