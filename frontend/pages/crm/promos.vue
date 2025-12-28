<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Promos</h2>
        <p class="text-gray-500">Manage promotional offers and discount codes</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchPromos">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Promo</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ promos.length }}</p>
          <p class="text-sm text-gray-500">Total Promos</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ activeCount }}</p>
          <p class="text-sm text-gray-500">Active</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-orange-600">{{ percentageCount }}</p>
          <p class="text-sm text-gray-500">Percentage</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-purple-600">{{ fixedCount }}</p>
          <p class="text-sm text-gray-500">Fixed Amount</p>
        </div>
      </UCard>
    </div>

    <!-- Data Table -->
    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="promos" 
        :loading="loading"
        searchable
        :search-keys="['code', 'name']"
        empty-message="No promos yet. Create your first promotional offer."
      >
        <template #code-data="{ row }">
          <span class="font-mono font-medium text-blue-600">{{ row.code }}</span>
        </template>
        
        <template #promo_type-data="{ row }">
          <UBadge :color="row.promo_type === 'PERCENTAGE' ? 'orange' : row.promo_type === 'FIXED' ? 'green' : 'purple'" variant="subtle">
            {{ row.promo_type }}
          </UBadge>
        </template>
        
        <template #value-data="{ row }">
          <span class="font-semibold">
            {{ row.promo_type === 'PERCENTAGE' ? `${row.value}%` : `$${row.value}` }}
          </span>
        </template>
        
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">
            {{ row.is_active ? 'Active' : 'Inactive' }}
          </UBadge>
        </template>

        <template #usage-data="{ row }">
          {{ row.usage_count || 0 }} / {{ row.usage_limit || '∞' }}
        </template>

        <template #dates-data="{ row }">
          <div class="text-sm">
            <p v-if="row.start_date">From: {{ formatDate(row.start_date) }}</p>
            <p v-if="row.end_date">To: {{ formatDate(row.end_date) }}</p>
            <p v-if="!row.start_date && !row.end_date" class="text-gray-400">No limit</p>
          </div>
        </template>
        
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="editPromo(row)" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEdit ? 'Edit Promo' : 'Add Promo'"
      :loading="saving"
      @submit="savePromo"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create promotional offers for your customers.</p>
        
        <UFormGroup label="Promo Code" required hint="Unique code customers enter at checkout (e.g., SUMMER20)">
          <UInput v-model="form.code" placeholder="e.g., SUMMER20" />
        </UFormGroup>

        <UFormGroup label="Promo Name" required hint="Display name for this promotion">
          <UInput v-model="form.name" placeholder="e.g., Summer Sale 20% Off" />
        </UFormGroup>

        <UFormGroup label="Description" hint="Optional details about this promo">
          <UTextarea v-model="form.description" rows="2" placeholder="Get 20% off all items..." />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Promo Type" required hint="Discount calculation method">
            <USelect v-model="form.promo_type" :options="promoTypeOptions" />
          </UFormGroup>
          <UFormGroup label="Value" required :hint="form.promo_type === 'PERCENTAGE' ? 'Percentage (e.g., 20)' : 'Fixed amount'">
            <UInput v-model.number="form.value" type="number" min="0" step="0.01" placeholder="20" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Min Order" hint="Minimum order amount required">
            <UInput v-model.number="form.min_order" type="number" min="0" placeholder="0" />
          </UFormGroup>
          <UFormGroup v-if="form.promo_type === 'PERCENTAGE'" label="Max Discount" hint="Maximum discount cap">
            <UInput v-model.number="form.max_discount" type="number" min="0" placeholder="No limit" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Start Date" hint="When promo becomes active">
            <UInput v-model="form.start_date" type="date" />
          </UFormGroup>
          <UFormGroup label="End Date" hint="When promo expires">
            <UInput v-model="form.end_date" type="date" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Usage Limit" hint="Total uses allowed (empty = unlimited)">
            <UInput v-model.number="form.usage_limit" type="number" min="0" placeholder="Unlimited" />
          </UFormGroup>
          <UFormGroup label="Per Customer" hint="Uses per customer">
            <UInput v-model.number="form.per_customer_limit" type="number" min="1" placeholder="1" />
          </UFormGroup>
        </div>

        <UFormGroup hint="Only active promos can be used">
          <UCheckbox v-model="form.is_active" label="Active" />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const isEdit = ref(false)
const editId = ref('')

const promos = ref<any[]>([])

const form = reactive({
  code: '',
  name: '',
  description: '',
  promo_type: 'PERCENTAGE',
  value: 0,
  min_order: 0,
  max_discount: null as number | null,
  start_date: '',
  end_date: '',
  is_active: true,
  usage_limit: null as number | null,
  per_customer_limit: 1
})

const columns = [
  { key: 'code', label: 'Code', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'promo_type', label: 'Type' },
  { key: 'value', label: 'Value' },
  { key: 'usage', label: 'Usage' },
  { key: 'dates', label: 'Period' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const promoTypeOptions = [
  { label: 'Percentage Off', value: 'PERCENTAGE' },
  { label: 'Fixed Amount', value: 'FIXED' },
  { label: 'Free Item', value: 'FREE_ITEM' }
]

const activeCount = computed(() => promos.value.filter((p: any) => p.is_active).length)
const percentageCount = computed(() => promos.value.filter((p: any) => p.promo_type === 'PERCENTAGE').length)
const fixedCount = computed(() => promos.value.filter((p: any) => p.promo_type === 'FIXED').length)

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''

const fetchPromos = async () => {
  loading.value = true
  try {
    const res = await $api.get('/crm/promos')
    promos.value = res.data || []
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to load', color: 'red' })
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.code = ''
  form.name = ''
  form.description = ''
  form.promo_type = 'PERCENTAGE'
  form.value = 0
  form.min_order = 0
  form.max_discount = null
  form.start_date = ''
  form.end_date = ''
  form.is_active = true
  form.usage_limit = null
  form.per_customer_limit = 1
  isEdit.value = false
  editId.value = ''
}

const openCreate = () => {
  resetForm()
  isOpen.value = true
}

const editPromo = (promo: any) => {
  isEdit.value = true
  editId.value = promo.id
  form.code = promo.code
  form.name = promo.name
  form.description = promo.description || ''
  form.promo_type = promo.promo_type
  form.value = promo.value
  form.min_order = promo.min_order || 0
  form.max_discount = promo.max_discount
  form.start_date = promo.start_date?.split('T')[0] || ''
  form.end_date = promo.end_date?.split('T')[0] || ''
  form.is_active = promo.is_active
  form.usage_limit = promo.usage_limit
  form.per_customer_limit = promo.per_customer_limit || 1
  isOpen.value = true
}

const savePromo = async () => {
  if (!form.code.trim() || !form.name.trim()) {
    toast.add({ title: 'Error', description: 'Code and Name are required', color: 'red' })
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await $api.put(`/crm/promos/${editId.value}`, form)
      toast.add({ title: 'Updated', description: 'Promo updated', color: 'green' })
    } else {
      await $api.post('/crm/promos', form)
      toast.add({ title: 'Created', description: 'Promo created', color: 'green' })
    }
    isOpen.value = false
    fetchPromos()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const confirmDelete = async (promo: any) => {
  if (!confirm(`Delete promo "${promo.code}"?\n\nThis action cannot be undone.`)) return
  
  try {
    await $api.delete(`/crm/promos/${promo.id}`)
    toast.add({ title: 'Deleted', description: 'Promo deleted', color: 'green' })
    fetchPromos()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to delete', color: 'red' })
  }
}

onMounted(() => fetchPromos())
</script>
