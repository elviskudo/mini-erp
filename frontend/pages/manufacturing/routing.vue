<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Production Routing</h2>
        <p class="text-gray-500">Define step-by-step processes for manufacturing products</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">Add Routing</UButton>
    </div>

    <!-- Routing List -->
    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="routings" 
        :loading="loading"
        searchable
        :search-keys="['name', 'product_name']"
        empty-message="No routings defined yet. Create one to define production steps."
      >
        <template #product_name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.product_name || 'Unknown' }}</p>
            <p class="text-xs text-gray-400">{{ row.product_code }}</p>
          </div>
        </template>
        <template #is_active-data="{ row }">
          <UBadge :color="row.is_active ? 'green' : 'gray'" variant="subtle">
            {{ row.is_active ? 'Active' : 'Inactive' }}
          </UBadge>
        </template>
        <template #steps_count-data="{ row }">
          {{ row.steps?.length || 0 }} steps
        </template>
        <template #total_time-data="{ row }">
          {{ formatTime(row.total_time_hours || 0) }}
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" title="View Steps" />
            <UButton icon="i-heroicons-pencil" size="xs" color="gray" variant="ghost" @click="openEdit(row)" title="Edit" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="deleteRouting(row)" title="Delete" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Routing' : 'Create Routing'"
      :loading="submitting"
      :disabled="!form.product_id || !form.name"
      @submit="save"
    >
      <div class="space-y-4">
        <UFormGroup label="Product" required hint="Select product for this routing" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.product_id" :options="productOptions" placeholder="Select product..." />
        </UFormGroup>
        
        <UFormGroup label="Routing Name" required hint="Descriptive name for this routing" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g. Standard Assembly Process" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Version" hint="e.g. 1.0, 2.0" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.version" placeholder="1.0" />
          </UFormGroup>
          <UFormGroup label="Status">
            <USelect v-model="form.is_active" :options="[{label:'Active',value:true},{label:'Inactive',value:false}]" />
          </UFormGroup>
        </div>
        
        <!-- Steps Section -->
        <div class="border-t pt-4 mt-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium">Steps</h4>
            <UButton size="xs" icon="i-heroicons-plus" @click="addStep">Add Step</UButton>
          </div>
          
          <div v-if="form.steps.length" class="space-y-3">
            <div v-for="(step, idx) in form.steps" :key="idx" class="p-3 bg-gray-50 rounded-lg border">
              <div class="flex justify-between items-start mb-2">
                <span class="text-xs font-medium bg-primary-100 text-primary-700 px-2 py-1 rounded">Step {{ step.sequence }}</span>
                <UButton icon="i-heroicons-trash" size="2xs" color="red" variant="ghost" @click="removeStep(idx)" />
              </div>
              <div class="grid grid-cols-2 gap-2">
                <UFormGroup label="Operation">
                  <UInput v-model="step.operation_name" placeholder="e.g. Cutting" size="sm" />
                </UFormGroup>
                <UFormGroup label="Work Center">
                  <USelect v-model="step.work_center_id" :options="workCenterOptions" size="sm" />
                </UFormGroup>
                <UFormGroup label="Setup Time (min)">
                  <UInput v-model.number="step.setup_time_mins" type="number" size="sm" />
                </UFormGroup>
                <UFormGroup label="Run Time (min)">
                  <UInput v-model.number="step.run_time_mins" type="number" size="sm" />
                </UFormGroup>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400 text-center py-4">No steps added yet</p>
        </div>
      </div>
    </FormSlideover>

    <!-- View Details Modal -->
    <UModal v-model="showDetailsModal" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedRouting">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedRouting.name }}</h3>
              <p class="text-sm text-gray-500">{{ selectedRouting.product_name }}</p>
            </div>
            <UBadge :color="selectedRouting.is_active ? 'green' : 'gray'" variant="subtle">
              {{ selectedRouting.is_active ? 'Active' : 'Inactive' }}
            </UBadge>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-3 bg-gray-50 rounded">
              <p class="text-lg font-bold">{{ selectedRouting.steps?.length || 0 }}</p>
              <p class="text-xs text-gray-500">Steps</p>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <p class="text-lg font-bold text-blue-600">{{ formatTime(selectedRouting.total_time_hours || 0) }}</p>
              <p class="text-xs text-gray-500">Total Time</p>
            </div>
            <div class="p-3 bg-green-50 rounded">
              <p class="text-lg font-bold text-green-600">v{{ selectedRouting.version }}</p>
              <p class="text-xs text-gray-500">Version</p>
            </div>
          </div>
          
          <!-- Steps Timeline -->
          <div class="border-t pt-4">
            <h4 class="font-medium mb-3">Production Steps</h4>
            <div class="space-y-2">
              <div v-for="step in (selectedRouting.steps || [])" :key="step.id" class="flex items-center gap-3 p-3 border rounded-lg">
                <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm">
                  {{ step.sequence }}
                </div>
                <div class="flex-1">
                  <p class="font-medium">{{ step.operation_name }}</p>
                  <p class="text-xs text-gray-500">{{ step.work_center_name || 'Work Center' }}</p>
                </div>
                <div class="text-right text-sm">
                  <p>Setup: {{ step.setup_time_mins || 0 }} min</p>
                  <p>Run: {{ step.run_time_mins || 0 }} min</p>
                </div>
              </div>
              <p v-if="!selectedRouting.steps?.length" class="text-center text-gray-400 py-4">No steps defined</p>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDetailsModal = false">Close</UButton>
            <UButton @click="openEdit(selectedRouting); showDetailsModal = false">Edit Routing</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)
const editMode = ref(false)
const showDetailsModal = ref(false)

const routings = ref<any[]>([])
const products = ref<any[]>([])
const workCenters = ref<any[]>([])
const selectedRouting = ref<any>(null)

const columns = [
  { key: 'name', label: 'Routing Name', sortable: true },
  { key: 'product_name', label: 'Product' },
  { key: 'version', label: 'Version' },
  { key: 'steps_count', label: 'Steps' },
  { key: 'total_time', label: 'Total Time' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' }
]

const form = reactive({
  id: '',
  product_id: '',
  name: '',
  version: '1.0',
  is_active: true,
  steps: [] as any[]
})

const productOptions = computed(() => 
  products.value.map(p => ({ label: `${p.code} - ${p.name}`, value: p.id }))
)

const workCenterOptions = computed(() => 
  workCenters.value.map(w => ({ label: w.name, value: w.id }))
)

const formatTime = (hours: number) => {
  if (hours < 1) return `${Math.round(hours * 60)} min`
  return `${hours.toFixed(1)} hrs`
}

const resetForm = () => {
  Object.assign(form, { id: '', product_id: '', name: '', version: '1.0', is_active: true, steps: [] })
}

const addStep = () => {
  const seq = form.steps.length ? Math.max(...form.steps.map(s => s.sequence)) + 10 : 10
  form.steps.push({ sequence: seq, operation_name: '', work_center_id: '', setup_time_mins: 0, run_time_mins: 0 })
}

const removeStep = (idx: number) => {
  form.steps.splice(idx, 1)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [routingsRes, productsRes, wcRes] = await Promise.all([
      $api.get('/manufacturing/routings'),
      $api.get('/manufacturing/products'),
      $api.get('/manufacturing/work-centers')
    ])
    routings.value = routingsRes.data || []
    products.value = productsRes.data || []
    workCenters.value = wcRes.data || []
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
  Object.assign(form, { ...row, steps: [...(row.steps || [])] })
  editMode.value = true
  isOpen.value = true
}

const viewDetails = (row: any) => {
  selectedRouting.value = row
  showDetailsModal.value = true
}

const save = async () => {
  submitting.value = true
  try {
    if (editMode.value) {
      await $api.put(`/manufacturing/routings/${form.id}`, form)
      toast.add({ title: 'Updated', description: 'Routing updated', color: 'green' })
    } else {
      await $api.post('/manufacturing/routings', form)
      toast.add({ title: 'Created', description: 'Routing created', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const deleteRouting = async (row: any) => {
  if (!confirm(`Delete routing "${row.name}"?`)) return
  try {
    await $api.delete(`/manufacturing/routings/${row.id}`)
    toast.add({ title: 'Deleted', color: 'green' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' })
  }
}

onMounted(() => {
  fetchData()
})
</script>
