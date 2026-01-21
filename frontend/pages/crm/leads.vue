<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Leads</h2>
        <p class="text-gray-500">Manage prospects and potential customers</p>
      </div>
      <div class="flex gap-2">
        <UButtonGroup size="sm">
          <UButton :variant="viewMode === 'grid' ? 'solid' : 'ghost'" icon="i-heroicons-table-cells" @click="viewMode = 'grid'" />
          <UButton :variant="viewMode === 'list' ? 'solid' : 'ghost'" icon="i-heroicons-view-columns" @click="viewMode = 'list'" />
        </UButtonGroup>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Lead</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ leads.length }}</p>
          <p class="text-sm text-gray-500">Total Leads</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ newLeads }}</p>
          <p class="text-sm text-gray-500">New</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ contactedLeads }}</p>
          <p class="text-sm text-gray-500">Contacted</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ qualifiedLeads }}</p>
          <p class="text-sm text-gray-500">Qualified</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-purple-600">{{ convertedLeads }}</p>
          <p class="text-sm text-gray-500">Converted</p>
        </div>
      </UCard>
    </div>

    <!-- Grid View (DataTable) -->
    <UCard v-if="viewMode === 'grid'">
      <DataTable 
        :columns="columns" 
        :rows="leads" 
        :loading="loading"
        searchable
        :search-keys="['name', 'company', 'email', 'phone', 'industry']"
        empty-message="No leads yet. Add a new lead to start tracking."
      >
        <template #name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.name }}</p>
            <p class="text-xs text-gray-400">{{ row.company || 'Individual' }}</p>
          </div>
        </template>
        <template #contact-data="{ row }">
          <div class="text-sm">
            <p v-if="row.email"><UIcon name="i-heroicons-envelope" class="w-3 h-3 mr-1" />{{ row.email }}</p>
            <p v-if="row.phone"><UIcon name="i-heroicons-phone" class="w-3 h-3 mr-1" />{{ row.phone }}</p>
          </div>
        </template>
        <template #source-data="{ row }">
          <UBadge :color="getSourceColor(row.source)" variant="subtle" size="xs">{{ row.source }}</UBadge>
        </template>
        <template #industry-data="{ row }">
          <span class="text-sm">{{ row.industry || '-' }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #score-data="{ row }">
          <div class="flex items-center gap-2">
            <div class="w-16 bg-gray-200 rounded-full h-2">
              <div class="bg-blue-600 h-2 rounded-full" :style="{ width: `${row.score}%` }"></div>
            </div>
            <span class="text-xs">{{ row.score }}</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UButton v-if="row.status !== 'Converted'" icon="i-heroicons-arrow-right-circle" size="xs" color="green" variant="ghost" @click="convertLead(row)" title="Convert" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- List View (Cards) -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-if="loading" class="col-span-full text-center py-8 text-gray-400">Loading...</div>
      <UCard v-for="lead in leads" :key="lead.id" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h4 class="font-semibold">{{ lead.name }}</h4>
            <p class="text-sm text-gray-500">{{ lead.company || 'Individual' }}</p>
          </div>
          <UBadge :color="getStatusColor(lead.status)" variant="subtle">{{ lead.status }}</UBadge>
        </div>
        
        <div class="space-y-2 text-sm">
          <p v-if="lead.email" class="flex items-center gap-2">
            <UIcon name="i-heroicons-envelope" class="text-gray-400" />
            {{ lead.email }}
          </p>
          <p v-if="lead.phone" class="flex items-center gap-2">
            <UIcon name="i-heroicons-phone" class="text-gray-400" />
            {{ lead.phone }}
          </p>
          <p v-if="lead.industry" class="flex items-center gap-2">
            <UIcon name="i-heroicons-building-office" class="text-gray-400" />
            {{ lead.industry }}
          </p>
          <div class="flex items-center gap-2">
            <UBadge :color="getSourceColor(lead.source)" variant="subtle" size="xs">{{ lead.source }}</UBadge>
            <span class="text-gray-400">•</span>
            <span class="text-gray-500">Score: {{ lead.score }}</span>
          </div>
        </div>
        
        <div class="flex justify-end gap-1 mt-4 pt-3 border-t">
          <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(lead)" />
          <UButton v-if="lead.status !== 'Converted'" icon="i-heroicons-arrow-right-circle" size="xs" color="green" variant="ghost" @click="convertLead(lead)" title="Convert to Opportunity" />
          <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(lead)" />
        </div>
      </UCard>
    </div>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEditing ? 'Edit Lead' : 'Add Lead'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Add a new prospect. Fields marked with * are required.</p>
        
        <UFormGroup label="Contact Name *" required hint="Person in charge name" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g., John Doe" />
        </UFormGroup>
        
        <UFormGroup label="Company" hint="Company name (leave empty for individual)" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.company" placeholder="e.g., ABC Corp" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Email *" required hint="Contact email" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.email" type="email" placeholder="email@example.com" />
          </UFormGroup>
          <UFormGroup label="Phone *" required hint="Phone number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.phone" placeholder="+1..." />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Source *" required hint="Where the lead came from" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.source" :options="sourceOptions" />
          </UFormGroup>
          <UFormGroup label="Industry *" required hint="Business sector" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.industry" placeholder="e.g., Manufacturing" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Website" hint="Company website" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.website" placeholder="https://..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Company Size" hint="Number of employees" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.company_size" :options="sizeOptions" />
          </UFormGroup>
          <UFormGroup label="Lead Score" hint="Potential score (0-100)" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.score" type="number" min="0" max="100" />
          </UFormGroup>
        </div>
        
        <!-- Address with OpenStreetMap -->
        <div class="border-t pt-4">
          <h4 class="font-medium mb-3">Location</h4>
          
          <UFormGroup label="Address Search" hint="Search for address using OpenStreetMap" :ui="{ hint: 'text-xs text-gray-400' }">
            <div class="relative">
              <UInput 
                v-model="addressSearch" 
                placeholder="Type address to search..." 
                @input="debounceSearch"
              />
              <div v-if="searchingAddress" class="absolute right-3 top-2">
                <UIcon name="i-heroicons-arrow-path" class="animate-spin w-5 h-5 text-gray-400" />
              </div>
            </div>
          </UFormGroup>
          
          <!-- Search Results -->
          <div v-if="addressResults.length > 0" class="mt-2 border rounded-lg max-h-40 overflow-y-auto">
            <div 
              v-for="(result, idx) in addressResults" 
              :key="idx"
              class="p-2 hover:bg-gray-50 cursor-pointer text-sm border-b last:border-b-0"
              @click="selectAddress(result)"
            >
              {{ result.display_name }}
            </div>
          </div>
          
          <UFormGroup label="Address" hint="Full address" :ui="{ hint: 'text-xs text-gray-400' }" class="mt-3">
            <UTextarea v-model="form.address" rows="2" placeholder="Full address..." />
          </UFormGroup>
          
          <div class="grid grid-cols-2 gap-4 mt-3">
            <UFormGroup label="Latitude" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.latitude" type="number" step="any" readonly />
            </UFormGroup>
            <UFormGroup label="Longitude" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model.number="form.longitude" type="number" step="any" readonly />
            </UFormGroup>
          </div>
          
          <!-- Map Preview -->
          <div v-if="form.latitude && form.longitude" class="mt-3 rounded-lg overflow-hidden border h-40">
            <iframe 
              :src="`https://www.openstreetmap.org/export/embed.html?bbox=${form.longitude-0.01},${form.latitude-0.01},${form.longitude+0.01},${form.latitude+0.01}&layer=mapnik&marker=${form.latitude},${form.longitude}`"
              class="w-full h-full border-0"
            ></iframe>
          </div>
        </div>
        
        <UFormGroup label="Notes" hint="Additional notes about this lead" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="3" placeholder="e.g., Interested in product X, request follow-up next week..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Convert Lead Modal -->
    <UModal v-model="showConvert">
      <UCard>
        <template #header>
          <h3 class="font-semibold">Convert Lead</h3>
        </template>
        <div class="space-y-4">
          <p class="text-sm text-gray-500">Convert lead "{{ selectedLead?.name }}" into:</p>
          <UCheckbox v-model="convertOptions.createCustomer" label="Create new Customer" />
          <UCheckbox v-model="convertOptions.createOpportunity" label="Create new Opportunity" />
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showConvert = false">Cancel</UButton>
            <UButton color="green" :loading="converting" @click="doConvert">Convert</UButton>
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
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const showConvert = ref(false)
const converting = ref(false)
const selectedLead = ref<any>(null)

const viewMode = ref<'grid' | 'list'>('grid')
const leads = ref<any[]>([])

// Address search
const addressSearch = ref('')
const addressResults = ref<any[]>([])
const searchingAddress = ref(false)
let searchTimeout: any = null

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'contact', label: 'Contact' },
  { key: 'source', label: 'Source' },
  { key: 'industry', label: 'Industry' },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'score', label: 'Score', sortable: true },
  { key: 'actions', label: '' }
]

const sourceOptions = [
  { label: 'Website', value: 'Website' },
  { label: 'Expo', value: 'Expo' },
  { label: 'Referral', value: 'Referral' },
  { label: 'Cold Call', value: 'Cold Call' },
  { label: 'Social Media', value: 'Social Media' },
  { label: 'Advertisement', value: 'Advertisement' },
  { label: 'Email Campaign', value: 'Email Campaign' },
  { label: 'Partner', value: 'Partner' },
  { label: 'Other', value: 'Other' }
]

const sizeOptions = [
  { label: '1-10 employees', value: '1-10' },
  { label: '10-50 employees', value: '10-50' },
  { label: '50-200 employees', value: '50-200' },
  { label: '200+ employees', value: '200+' }
]

const form = reactive({
  name: '',
  company: '',
  email: '',
  phone: '',
  website: '',
  source: 'Other',
  industry: '',
  company_size: '',
  address: '',
  latitude: null as number | null,
  longitude: null as number | null,
  notes: '',
  score: 0
})

const convertOptions = reactive({
  createCustomer: true,
  createOpportunity: true
})

const newLeads = computed(() => Array.isArray(leads.value) ? leads.value.filter(l => l.status === 'New').length : 0)
const contactedLeads = computed(() => Array.isArray(leads.value) ? leads.value.filter(l => l.status === 'Contacted').length : 0)
const qualifiedLeads = computed(() => Array.isArray(leads.value) ? leads.value.filter(l => l.status === 'Qualified').length : 0)
const convertedLeads = computed(() => Array.isArray(leads.value) ? leads.value.filter(l => l.status === 'Converted').length : 0)

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { New: 'blue', Contacted: 'yellow', Qualified: 'green', Converted: 'purple', Lost: 'red' }
  return colors[status] || 'gray'
}

const getSourceColor = (source: string) => {
  const colors: Record<string, string> = { Website: 'blue', Expo: 'purple', Referral: 'green', 'Cold Call': 'yellow', 'Social Media': 'pink' }
  return colors[source] || 'gray'
}

// OpenStreetMap address search
const debounceSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => searchAddress(), 500)
}

const searchAddress = async () => {
  if (!addressSearch.value || addressSearch.value.length < 3) {
    addressResults.value = []
    return
  }
  
  searchingAddress.value = true
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(addressSearch.value)}&limit=5`,
      { headers: { 'Accept-Language': 'en' } }
    )
    addressResults.value = await response.json()
  } catch (e) {
    console.error('Address search error:', e)
    addressResults.value = []
  } finally {
    searchingAddress.value = false
  }
}

const selectAddress = (result: any) => {
  form.address = result.display_name
  form.latitude = parseFloat(result.lat)
  form.longitude = parseFloat(result.lon)
  addressSearch.value = result.display_name
  addressResults.value = []
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/crm/leads')
    leads.value = Array.isArray(res.data) ? res.data : (res.data?.data || [])
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Error', description: 'Failed to load leads', color: 'red' })
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEditing.value = false
  editingId.value = null
  addressSearch.value = ''
  addressResults.value = []
  Object.assign(form, { name: '', company: '', email: '', phone: '', website: '', source: 'Other', industry: '', company_size: '', address: '', latitude: null, longitude: null, notes: '', score: 0 })
  isOpen.value = true
}

const openEdit = (row: any) => {
  isEditing.value = true
  editingId.value = row.id
  addressSearch.value = row.address || ''
  addressResults.value = []
  Object.assign(form, row)
  isOpen.value = true
}

const validateForm = () => {
  const errors: string[] = []
  if (!form.name) errors.push('Contact Name is required')
  if (!form.email) errors.push('Email is required')
  if (!form.phone) errors.push('Phone is required')
  if (!form.source) errors.push('Source is required')
  if (!form.industry) errors.push('Industry is required')
  return errors
}

const save = async () => {
  const errors = validateForm()
  if (errors.length > 0) {
    toast.add({ title: 'Validation Error', description: errors.join(', '), color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      await $api.put(`/crm/leads/${editingId.value}`, form)
      toast.add({ title: 'Updated', description: 'Lead updated successfully', color: 'green' })
    } else {
      await $api.post('/crm/leads', form)
      toast.add({ title: 'Created', description: 'Lead created successfully', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save lead', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const confirmDelete = async (row: any) => {
  if (!confirm(`Delete lead "${row.name}"?`)) return
  try {
    await $api.delete(`/crm/leads/${row.id}`)
    toast.add({ title: 'Deleted', description: 'Lead deleted successfully', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const convertLead = (row: any) => {
  selectedLead.value = row
  convertOptions.createCustomer = true
  convertOptions.createOpportunity = true
  showConvert.value = true
}

const doConvert = async () => {
  if (!selectedLead.value) return
  converting.value = true
  try {
    await $api.post(`/crm/leads/${selectedLead.value.id}/convert?create_opportunity=${convertOptions.createOpportunity}&create_customer=${convertOptions.createCustomer}`)
    toast.add({ title: 'Converted', description: 'Lead converted successfully', color: 'green' })
    showConvert.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    converting.value = false
  }
}

onMounted(() => { fetchData() })
</script>
