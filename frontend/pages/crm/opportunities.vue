<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Opportunities</h2>
        <p class="text-gray-500">Leads with potential to become deals</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Opportunity</UButton>
      </div>
    </div>

    <!-- Pipeline Summary -->
    <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
      <UCard v-for="stage in stages" :key="stage.value" :ui="{ body: { padding: 'p-3' } }" class="cursor-pointer hover:shadow-md transition-shadow" @click="filterByStage(stage.value)">
        <div class="text-center">
          <p class="text-lg font-bold" :class="stage.color">{{ getStageCount(stage.value) }}</p>
          <p class="text-xs text-gray-500">{{ stage.label }}</p>
          <p class="text-xs font-medium">{{ formatCurrency(getStageValue(stage.value)) }}</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="filteredOpportunities" 
        :loading="loading"
        searchable
        :search-keys="['name', 'customer_name', 'lead_name']"
        empty-message="No opportunities yet. Create new or convert from a lead."
      >
        <template #name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.name }}</p>
            <p class="text-xs text-gray-400">{{ row.description?.slice(0, 50) || '' }}</p>
          </div>
        </template>
        <template #customer-data="{ row }">
          <p>{{ row.customer_name || row.lead_name || '-' }}</p>
        </template>
        <template #stage-data="{ row }">
          <UBadge :color="getStageColor(row.stage)" variant="subtle">{{ row.stage }}</UBadge>
        </template>
        <template #probability-data="{ row }">
          <div class="flex items-center gap-2">
            <div class="w-12 bg-gray-200 rounded-full h-2">
              <div class="bg-green-500 h-2 rounded-full" :style="{ width: `${row.probability}%` }"></div>
            </div>
            <span class="text-xs">{{ row.probability }}%</span>
          </div>
        </template>
        <template #expected_value-data="{ row }">
          <span class="font-medium">{{ formatCurrency(row.expected_value) }}</span>
        </template>
        <template #expected_close_date-data="{ row }">
          <span :class="isOverdue(row.expected_close_date) ? 'text-red-500' : ''">
            {{ formatDate(row.expected_close_date) }}
          </span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UDropdown :items="getStageActions(row)" :popper="{ placement: 'bottom-end' }">
              <UButton icon="i-heroicons-arrows-right-left" size="xs" color="blue" variant="ghost" title="Change Stage" />
            </UDropdown>
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEditing ? 'Edit Opportunity' : 'Add Opportunity'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">An opportunity is a qualified lead with potential to become a deal.</p>
        
        <UFormGroup label="Opportunity Name" required hint="Short title/description" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g., Project ABC - Phase 1" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Opportunity details" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" placeholder="Full description..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Stage" hint="Current progress" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.stage" :options="stageOptions" />
          </UFormGroup>
          <UFormGroup label="Probability (%)" hint="Close probability" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.probability" type="number" min="0" max="100" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Expected Value" hint="Estimated deal value" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.expected_value" type="number" />
          </UFormGroup>
          <UFormGroup label="Expected Close Date" hint="Target closing" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.expected_close_date" type="date" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Customer" hint="Select related customer" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.customer_id" :options="customerOptions" placeholder="Select customer..." searchable />
        </UFormGroup>
        
        <UFormGroup label="Lead" hint="Select source lead (optional)" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.lead_id" :options="leadOptions" placeholder="Select lead..." searchable />
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
const submitting = ref(false)
const isOpen = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const selectedStage = ref<string | null>(null)

const opportunities = ref<any[]>([])
const customers = ref<any[]>([])
const leads = ref<any[]>([])

const columns = [
  { key: 'name', label: 'Opportunity', sortable: true },
  { key: 'customer', label: 'Customer/Lead' },
  { key: 'stage', label: 'Stage', sortable: true },
  { key: 'probability', label: 'Probability' },
  { key: 'expected_value', label: 'Value', sortable: true },
  { key: 'expected_close_date', label: 'Close Date', sortable: true },
  { key: 'actions', label: '' }
]

const stages = [
  { label: 'Qualification', value: 'Qualification', color: 'text-gray-600' },
  { label: 'Needs Analysis', value: 'Needs Analysis', color: 'text-blue-600' },
  { label: 'Proposal', value: 'Proposal', color: 'text-yellow-600' },
  { label: 'Negotiation', value: 'Negotiation', color: 'text-orange-600' },
  { label: 'Won', value: 'Closed Won', color: 'text-green-600' },
  { label: 'Lost', value: 'Closed Lost', color: 'text-red-600' }
]

const stageOptions = stages.map(s => ({ label: s.label, value: s.value }))

const form = reactive({
  name: '',
  description: '',
  stage: 'Qualification',
  probability: 10,
  expected_value: 0,
  expected_close_date: '',
  customer_id: '',
  lead_id: ''
})

const filteredOpportunities = computed(() => {
  if (!selectedStage.value) return opportunities.value
  return opportunities.value.filter(o => o.stage === selectedStage.value)
})

const customerOptions = computed(() => customers.value.map(c => ({ label: c.name, value: c.id })))
const leadOptions = computed(() => leads.value.map(l => ({ label: `${l.name} (${l.company || 'Individual'})`, value: l.id })))

const getStageCount = (stage: string) => opportunities.value.filter(o => o.stage === stage).length
const getStageValue = (stage: string) => opportunities.value.filter(o => o.stage === stage).reduce((sum, o) => sum + (o.expected_value || 0), 0)

const getStageColor = (stage: string) => {
  const colors: Record<string, string> = { 'Qualification': 'gray', 'Needs Analysis': 'blue', 'Proposal': 'yellow', 'Negotiation': 'orange', 'Closed Won': 'green', 'Closed Lost': 'red' }
  return colors[stage] || 'gray'
}

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val || 0)
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const isOverdue = (date: string) => date && new Date(date) < new Date()

const filterByStage = (stage: string) => {
  selectedStage.value = selectedStage.value === stage ? null : stage
}

const getStageActions = (row: any) => {
  return [stages.filter(s => s.value !== row.stage).map(s => ({
    label: `Move to ${s.label}`,
    click: () => moveToStage(row, s.value)
  }))]
}

const fetchData = async () => {
  loading.value = true
  try {
    const [oppRes, custRes, leadRes] = await Promise.all([
      $api.get('/crm/opportunities').catch(() => ({ data: { data: [] } })),
      $api.get('/crm/customers').catch(() => ({ data: { data: [] } })),
      $api.get('/crm/leads').catch(() => ({ data: { data: [] } }))
    ])
    // Handle both {data: [...]} and {data: {data: [...]}} response formats
    opportunities.value = Array.isArray(oppRes.data?.data) ? oppRes.data.data : (Array.isArray(oppRes.data) ? oppRes.data : [])
    customers.value = Array.isArray(custRes.data?.data) ? custRes.data.data : (Array.isArray(custRes.data) ? custRes.data : [])
    leads.value = Array.isArray(leadRes.data?.data) ? leadRes.data.data : (Array.isArray(leadRes.data) ? leadRes.data : [])
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, { name: '', description: '', stage: 'Qualification', probability: 10, expected_value: 0, expected_close_date: '', customer_id: '', lead_id: '' })
  isOpen.value = true
}

const openEdit = (row: any) => {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    ...row,
    expected_close_date: row.expected_close_date ? row.expected_close_date.split('T')[0] : ''
  })
  isOpen.value = true
}

const save = async () => {
  if (!form.name) {
    toast.add({ title: 'Error', description: 'Name is required', color: 'red' })
    return
  }
  submitting.value = true
  try {
    const payload = { ...form, expected_close_date: form.expected_close_date ? new Date(form.expected_close_date).toISOString() : null }
    if (isEditing.value && editingId.value) {
      await $api.put(`/crm/opportunities/${editingId.value}`, payload)
      toast.add({ title: 'Updated', description: 'Opportunity updated successfully', color: 'green' })
    } else {
      await $api.post('/crm/opportunities', payload)
      toast.add({ title: 'Created', description: 'Opportunity created successfully', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const moveToStage = async (row: any, newStage: string) => {
  try {
    await $api.put(`/crm/opportunities/${row.id}/stage?stage=${encodeURIComponent(newStage)}`)
    toast.add({ title: 'Moved', description: `Moved to ${newStage}`, color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const confirmDelete = async (row: any) => {
  if (!confirm(`Delete opportunity "${row.name}"?`)) return
  try {
    await $api.delete(`/crm/opportunities/${row.id}`)
    toast.add({ title: 'Deleted', description: 'Opportunity deleted successfully', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

onMounted(() => { fetchData() })
</script>
