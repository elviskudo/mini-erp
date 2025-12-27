<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Courier Management</h2>
        <p class="text-gray-500">Manage shipping providers and delivery settings</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Courier</UButton>
      </div>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="couriers" 
        :loading="loading"
        searchable
        :search-keys="['code', 'name']"
        empty-message="No couriers yet. Add one to start tracking shipments."
      >
        <template #code-data="{ row }">
          <span class="font-mono font-medium">{{ row.code }}</span>
        </template>
        <template #name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.name }}</p>
            <p class="text-xs text-gray-400">{{ row.description }}</p>
          </div>
        </template>
        <template #service_types-data="{ row }">
          <div class="flex flex-wrap gap-1">
            <UBadge v-for="s in (row.service_types || '').split(',')" :key="s" size="xs" variant="subtle" color="blue">{{ s.trim() }}</UBadge>
          </div>
        </template>
        <template #lead_days-data="{ row }">
          <div class="text-sm">
            <span class="text-gray-500">Standard:</span> {{ row.standard_lead_days }}d
            <span class="mx-1">|</span>
            <span class="text-gray-500">Express:</span> {{ row.express_lead_days }}d
          </div>
        </template>
        <template #cost-data="{ row }">
          <div class="text-sm">
            <span>Rp {{ formatNumber(row.base_cost || 0) }}</span>
            <span class="text-gray-400"> + Rp {{ formatNumber(row.cost_per_kg || 0) }}/kg</span>
          </div>
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">{{ row.is_active ? 'Active' : 'Inactive' }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Modal -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEditing ? 'Edit Courier' : 'Add Courier'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Configure courier/shipping provider details and pricing.</p>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Code" required hint="Short unique identifier" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="e.g., JNE" />
          </UFormGroup>
          <UFormGroup label="Name" required hint="Full courier name" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.name" placeholder="e.g., JNE Express" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Description" hint="Brief description of services" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" placeholder="e.g., National courier service..." />
        </UFormGroup>
        
        <div class="grid grid-cols-3 gap-4">
          <UFormGroup label="Phone" hint="Contact number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.phone" placeholder="+62..." />
          </UFormGroup>
          <UFormGroup label="Email" hint="Support email" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.email" type="email" placeholder="support@..." />
          </UFormGroup>
          <UFormGroup label="Website" hint="Tracking website" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.website" placeholder="https://..." />
          </UFormGroup>
        </div>
        
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3">Service Settings</h4>
          
          <UFormGroup label="Available Services" hint="Comma-separated list of service types" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.service_types" placeholder="Regular,Express,Same Day,Next Day" />
          </UFormGroup>
          
          <div class="grid grid-cols-3 gap-4 mt-4">
            <UFormGroup label="Default Service" hint="Default selected" :ui="{ hint: 'text-xs text-gray-400' }">
              <USelect v-model="form.default_service" :options="serviceOptions" />
            </UFormGroup>
            <UFormGroup label="Standard Lead (days)" hint="Days for standard" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.standard_lead_days" type="number" min="1" />
            </UFormGroup>
            <UFormGroup label="Express Lead (days)" hint="Days for express" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.express_lead_days" type="number" min="1" />
            </UFormGroup>
          </div>
        </div>
        
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3">Pricing</h4>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Base Cost (Rp)" hint="Minimum shipping fee" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.base_cost" type="number" min="0" />
            </UFormGroup>
            <UFormGroup label="Cost per Kg (Rp)" hint="Additional cost by weight" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.cost_per_kg" type="number" min="0" />
            </UFormGroup>
          </div>
        </div>
        
        <UCheckbox v-model="form.is_active" label="Active" />
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)

const couriers = ref<any[]>([])

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Name' },
  { key: 'service_types', label: 'Services' },
  { key: 'lead_days', label: 'Lead Time' },
  { key: 'cost', label: 'Pricing' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const form = reactive({
  code: '',
  name: '',
  description: '',
  phone: '',
  email: '',
  website: '',
  service_types: 'Regular,Express,Same Day,Next Day',
  default_service: 'Regular',
  standard_lead_days: 3,
  express_lead_days: 1,
  base_cost: 10000,
  cost_per_kg: 5000,
  is_active: true
})

const serviceOptions = computed(() => {
  return (form.service_types || '').split(',').map((s: string) => s.trim()).filter((s: string) => s)
})

const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/logistics/couriers')
    couriers.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, {
    code: '', name: '', description: '', phone: '', email: '', website: '',
    service_types: 'Regular,Express,Same Day,Next Day', default_service: 'Regular',
    standard_lead_days: 3, express_lead_days: 1, base_cost: 10000, cost_per_kg: 5000, is_active: true
  })
  isOpen.value = true
}

const openEdit = (row: any) => {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, row)
  isOpen.value = true
}

const save = async () => {
  if (!form.code || !form.name) {
    toast.add({ title: 'Validation Error', description: 'Code and Name are required', color: 'red' })
    return
  }
  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      await $api.put(`/logistics/couriers/${editingId.value}`, form)
      toast.add({ title: 'Updated', description: 'Courier updated successfully', color: 'green' })
    } else {
      await $api.post('/logistics/couriers', form)
      toast.add({ title: 'Created', description: 'Courier created successfully', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const confirmDelete = async (row: any) => {
  if (!confirm(`Delete courier "${row.name}"?`)) return
  try {
    await $api.delete(`/logistics/couriers/${row.id}`)
    toast.add({ title: 'Deleted', description: 'Courier deleted', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to delete', color: 'red' })
  }
}

onMounted(() => { fetchData() })
</script>
