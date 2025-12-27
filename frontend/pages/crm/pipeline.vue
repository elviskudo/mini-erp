<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Sales Pipeline</h2>
        <p class="text-gray-500">Visual progress of opportunities in Kanban view</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="$router.push('/crm/opportunities')">Add Opportunity</UButton>
      </div>
    </div>

    <!-- Pipeline Summary -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ opportunities.length }}</p>
          <p class="text-sm text-gray-500">Total Opportunities</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ formatCurrency(totalPipelineValue) }}</p>
          <p class="text-sm text-gray-500">Pipeline Value</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ formatCurrency(wonValue) }}</p>
          <p class="text-sm text-gray-500">Won Value</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-purple-600">{{ avgProbability }}%</p>
          <p class="text-sm text-gray-500">Avg Probability</p>
        </div>
      </UCard>
    </div>

    <!-- Kanban Board -->
    <div class="overflow-x-auto pb-4">
      <div class="flex gap-4 min-w-max">
        <div 
          v-for="stage in stages" 
          :key="stage.value" 
          class="w-72 flex-shrink-0"
        >
          <!-- Stage Header -->
          <div class="rounded-t-lg p-3" :class="stage.bgColor">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold text-white">{{ stage.label }}</h3>
              <div class="flex items-center gap-2">
                <span class="bg-white/20 text-white text-xs px-2 py-1 rounded-full">
                  {{ getStageOpportunities(stage.value).length }}
                </span>
              </div>
            </div>
            <p class="text-white/80 text-sm mt-1">{{ formatCurrency(getStageValue(stage.value)) }}</p>
          </div>
          
          <!-- Cards Container -->
          <div 
            class="bg-gray-100 rounded-b-lg p-2 min-h-[400px] space-y-2"
            @dragover.prevent
            @drop="handleDrop($event, stage.value)"
          >
            <div 
              v-for="opp in getStageOpportunities(stage.value)" 
              :key="opp.id"
              class="bg-white rounded-lg p-3 shadow-sm cursor-move hover:shadow-md transition-shadow"
              draggable="true"
              @dragstart="handleDragStart($event, opp)"
            >
              <div class="flex justify-between items-start mb-2">
                <h4 class="font-medium text-sm line-clamp-2">{{ opp.name }}</h4>
                <UBadge size="xs" color="green" variant="subtle">{{ opp.probability }}%</UBadge>
              </div>
              
              <p v-if="opp.customer_name || opp.lead_name" class="text-xs text-gray-500 mb-2">
                <UIcon name="i-heroicons-user" class="w-3 h-3 mr-1" />
                {{ opp.customer_name || opp.lead_name }}
              </p>
              
              <div class="flex justify-between items-center">
                <span class="font-semibold text-sm text-green-600">{{ formatCurrency(opp.expected_value) }}</span>
                <span v-if="opp.expected_close_date" class="text-xs text-gray-400" :class="isOverdue(opp.expected_close_date) ? 'text-red-500' : ''">
                  {{ formatDate(opp.expected_close_date) }}
                </span>
              </div>
              
              <!-- Quick Actions -->
              <div class="flex justify-end gap-1 mt-2 pt-2 border-t">
                <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="editOpportunity(opp)" />
                <UDropdown :items="getQuickActions(opp)" :popper="{ placement: 'bottom-end' }">
                  <UButton icon="i-heroicons-ellipsis-vertical" size="xs" color="gray" variant="ghost" />
                </UDropdown>
              </div>
            </div>
            
            <!-- Empty State -->
            <div v-if="getStageOpportunities(stage.value).length === 0" class="text-center py-8 text-gray-400 text-sm">
              <UIcon name="i-heroicons-inbox" class="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No opportunities</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <UCard :ui="{ body: { padding: 'p-4' } }">
      <div class="flex flex-wrap gap-4 justify-center">
        <div v-for="stage in stages" :key="stage.value" class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full" :class="stage.bgColor"></div>
          <span class="text-sm text-gray-600">{{ stage.label }}</span>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const router = useRouter()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const opportunities = ref<any[]>([])
const draggedItem = ref<any>(null)

const stages = [
  { label: 'Qualification', value: 'Qualification', bgColor: 'bg-gray-500' },
  { label: 'Needs Analysis', value: 'Needs Analysis', bgColor: 'bg-blue-500' },
  { label: 'Proposal', value: 'Proposal', bgColor: 'bg-yellow-500' },
  { label: 'Negotiation', value: 'Negotiation', bgColor: 'bg-orange-500' },
  { label: 'Closed Won', value: 'Closed Won', bgColor: 'bg-green-500' },
  { label: 'Closed Lost', value: 'Closed Lost', bgColor: 'bg-red-500' }
]

const getStageOpportunities = (stage: string) => opportunities.value.filter(o => o.stage === stage)
const getStageValue = (stage: string) => opportunities.value.filter(o => o.stage === stage).reduce((sum, o) => sum + (o.expected_value || 0), 0)

const totalPipelineValue = computed(() => 
  opportunities.value
    .filter(o => !['Closed Won', 'Closed Lost'].includes(o.stage))
    .reduce((sum, o) => sum + (o.expected_value || 0), 0)
)

const wonValue = computed(() => 
  opportunities.value
    .filter(o => o.stage === 'Closed Won')
    .reduce((sum, o) => sum + (o.actual_value || o.expected_value || 0), 0)
)

const avgProbability = computed(() => {
  const activeOpps = opportunities.value.filter(o => !['Closed Won', 'Closed Lost'].includes(o.stage))
  if (activeOpps.length === 0) return 0
  return Math.round(activeOpps.reduce((sum, o) => sum + (o.probability || 0), 0) / activeOpps.length)
})

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val || 0)
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'short' }) : ''
const isOverdue = (date: string) => date && new Date(date) < new Date()

const handleDragStart = (event: DragEvent, opp: any) => {
  draggedItem.value = opp
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

const handleDrop = async (event: DragEvent, newStage: string) => {
  event.preventDefault()
  if (!draggedItem.value || draggedItem.value.stage === newStage) return
  
  try {
    await $api.put(`/crm/opportunities/${draggedItem.value.id}/stage?stage=${encodeURIComponent(newStage)}`)
    toast.add({ title: 'Moved', description: `Opportunity moved to ${newStage}`, color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to move', color: 'red' })
  } finally {
    draggedItem.value = null
  }
}

const editOpportunity = (opp: any) => {
  router.push(`/crm/opportunities?edit=${opp.id}`)
}

const getQuickActions = (opp: any) => {
  return [[
    { label: 'View Details', icon: 'i-heroicons-eye', click: () => editOpportunity(opp) },
    { label: 'Add Activity', icon: 'i-heroicons-calendar', click: () => router.push(`/crm/activities?opportunity_id=${opp.id}`) }
  ]]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/crm/opportunities')
    opportunities.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchData() })
</script>
