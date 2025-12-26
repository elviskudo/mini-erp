<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/inventory/opname" />
      <div>
        <h2 class="text-xl font-bold">Variance Analysis</h2>
        <p class="text-gray-500">Compare system vs counted quantities</p>
      </div>
    </div>

    <!-- Opname Selector -->
    <UCard>
      <div class="flex gap-4 items-end">
        <UFormGroup label="Select Opname" class="flex-1">
          <USelect v-model="selectedOpnameId" :options="opnameOptions" placeholder="Select opname to analyze..." @change="loadOpname" />
        </UFormGroup>
        <UButton v-if="selectedOpname" icon="i-heroicons-arrow-path" variant="outline" @click="loadOpname">Refresh</UButton>
      </div>
    </UCard>

    <!-- Variance Summary -->
    <div v-if="selectedOpname" class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold">{{ selectedOpname.total_items || 0 }}</p>
          <p class="text-sm text-gray-500">Total Items</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ itemsMatch }}</p>
          <p class="text-sm text-gray-500">Match</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ selectedOpname.items_with_variance || 0 }}</p>
          <p class="text-sm text-gray-500">With Variance</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold" :class="selectedOpname.total_variance_value < 0 ? 'text-red-600' : 'text-green-600'">
            {{ formatCurrency(selectedOpname.total_variance_value || 0) }}
          </p>
          <p class="text-sm text-gray-500">Total Variance</p>
        </div>
      </UCard>
    </div>

    <!-- Variance Items -->
    <UCard v-if="selectedOpname">
      <template #header>
        <div class="flex items-center justify-between">
          <span>Items with Variance</span>
          <div class="flex gap-2">
            <UButton size="xs" variant="outline" icon="i-heroicons-funnel" @click="showOnlyVariance = !showOnlyVariance">
              {{ showOnlyVariance ? 'Show All' : 'Show Variance Only' }}
            </UButton>
          </div>
        </div>
      </template>
      
      <UTable :columns="columns" :rows="displayItems" :loading="loading">
        <template #product-data="{ row }">
          <div>
            <p class="font-medium">{{ row.product?.name || 'Unknown' }}</p>
            <p class="text-xs text-gray-400">{{ row.product?.code }}</p>
          </div>
        </template>
        <template #location-data="{ row }">
          {{ row.location?.name || '-' }}
        </template>
        <template #system_qty-data="{ row }">
          <span class="font-mono">{{ row.system_qty }}</span>
        </template>
        <template #counted_qty-data="{ row }">
          <span class="font-mono">{{ row.counted_qty ?? '-' }}</span>
        </template>
        <template #variance-data="{ row }">
          <span v-if="row.variance !== 0" class="font-mono font-bold" :class="row.variance < 0 ? 'text-red-600' : 'text-green-600'">
            {{ row.variance > 0 ? '+' : '' }}{{ row.variance }}
          </span>
          <span v-else class="text-gray-400">0</span>
        </template>
        <template #variance_value-data="{ row }">
          <span v-if="row.variance_value !== 0" :class="row.variance_value < 0 ? 'text-red-600' : 'text-green-600'">
            {{ formatCurrency(row.variance_value) }}
          </span>
        </template>
        <template #reason-data="{ row }">
          <USelect 
            v-if="canEditReason && row.variance !== 0"
            v-model="row.variance_reason"
            :options="varianceReasons"
            size="xs"
            placeholder="Select..."
            @change="updateReason(row)"
          />
          <span v-else>{{ row.variance_reason || '-' }}</span>
        </template>
      </UTable>
    </UCard>

    <!-- Actions -->
    <div v-if="selectedOpname && canSubmitReview" class="flex justify-end gap-2">
      <UButton color="primary" icon="i-heroicons-check" @click="submitForReview" :loading="submitting">
        Submit for Review
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const submitting = ref(false)
const opnames = ref<any[]>([])
const selectedOpnameId = ref('')
const selectedOpname = ref<any>(null)
const showOnlyVariance = ref(true)

const varianceReasons = [
  'Theft', 'Damage', 'Input Error', 'Return Not Recorded', 
  'Receiving Error', 'Expired', 'Shrinkage', 'System Error', 'Unknown', 'Other'
]

const columns = [
  { key: 'product', label: 'Product' },
  { key: 'location', label: 'Location' },
  { key: 'system_qty', label: 'System' },
  { key: 'counted_qty', label: 'Counted' },
  { key: 'variance', label: 'Variance' },
  { key: 'variance_value', label: 'Value' },
  { key: 'reason', label: 'Reason' }
]

const opnameOptions = computed(() => 
  opnames.value.map(o => ({
    value: o.id,
    label: `${o.opname_number || o.id.substring(0, 8)} - ${o.warehouse?.name || '-'} (${o.status})`
  }))
)

const displayItems = computed(() => {
  if (!selectedOpname.value?.details) return []
  const items = selectedOpname.value.details.map((d: any) => ({
    ...d,
    variance: d.counted_qty != null ? d.counted_qty - d.system_qty : 0,
    variance_value: d.variance_value || 0
  }))
  
  return showOnlyVariance.value ? items.filter((i: any) => i.variance !== 0) : items
})

const itemsMatch = computed(() => {
  if (!selectedOpname.value?.details) return 0
  return selectedOpname.value.details.filter((d: any) => 
    d.counted_qty != null && d.counted_qty === d.system_qty
  ).length
})

const canEditReason = computed(() => 
  selectedOpname.value && ['Counting Done', 'In Progress'].includes(selectedOpname.value.status)
)

const canSubmitReview = computed(() =>
  selectedOpname.value && selectedOpname.value.status === 'Counting Done'
)

const formatCurrency = (value: number) => 
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)

const fetchOpnames = async () => {
  loading.value = true
  try {
    const res = await $api.get('/opname/list')
    opnames.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const loadOpname = async () => {
  if (!selectedOpnameId.value) return
  loading.value = true
  try {
    const res = await $api.get(`/opname/${selectedOpnameId.value}`)
    selectedOpname.value = res.data
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load', color: 'red' })
  } finally {
    loading.value = false
  }
}

const updateReason = async (row: any) => {
  try {
    await $api.post('/opname/update-count', {
      opname_id: selectedOpname.value.id,
      items: [{
        detail_id: row.id,
        counted_qty: row.counted_qty,
        variance_reason: row.variance_reason
      }]
    })
    toast.add({ title: 'Updated', color: 'green', timeout: 1500 })
  } catch (e) {
    console.error(e)
  }
}

const submitForReview = async () => {
  submitting.value = true
  try {
    await $api.post('/opname/review', { opname_id: selectedOpname.value.id })
    toast.add({ title: 'Submitted', description: 'Sent for review', color: 'green' })
    await loadOpname()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchOpnames()
})
</script>
