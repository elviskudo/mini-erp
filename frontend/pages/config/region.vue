<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Regional Settings</h1>
        <p class="text-xs text-gray-500">Configure currency, timezone, and locale for your organization</p>
      </div>
      <UButton v-if="!regions.length" icon="i-heroicons-arrow-path" size="sm" @click="seedRegions" :loading="seeding">
        Initialize Regions
      </UButton>
    </div>

    <!-- Current Settings Card -->
    <UCard>
      <template #header>
        <h3 class="font-semibold text-sm">Current Configuration</h3>
      </template>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-2">Region <span class="text-red-500">*</span></label>
          <USelectMenu v-model="selectedRegion" :options="regionOptions" size="sm" placeholder="Select region" 
                       @change="onRegionChange" />
          <p class="text-xs text-gray-400 mt-1">Determines default currency, timezone, and locale</p>
        </div>
        
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-2">Current Timezone</label>
          <div class="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm">
            <UIcon name="i-heroicons-clock" class="w-4 h-4 text-gray-400" />
            <span>{{ currentSettings.timezone || 'Asia/Jakarta' }}</span>
            <UBadge variant="soft" size="xs">{{ currentSettings.gmt_offset || 'GMT+7' }}</UBadge>
          </div>
        </div>
        
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-2">Currency</label>
          <div class="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm">
            <UIcon name="i-heroicons-currency-dollar" class="w-4 h-4 text-gray-400" />
            <span class="font-semibold">{{ currentSettings.currency_symbol || 'Rp' }}</span>
            <span class="text-gray-500">({{ currentSettings.currency_code || 'IDR' }})</span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="outline" size="sm" :disabled="!hasChanges" @click="resetChanges">Cancel</UButton>
          <UButton size="sm" :loading="saving" :disabled="!hasChanges" @click="saveSettings">Save Changes</UButton>
        </div>
      </template>
    </UCard>

    <!-- Available Regions -->
    <UCard :ui="{ body: { padding: 'p-0' } }">
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="font-semibold text-sm">Available Regions</h3>
          <span class="text-xs text-gray-500">{{ regions.length }} regions configured</span>
        </div>
      </template>

      <UTable :columns="columns" :rows="regions" :loading="loading">
        <template #code-data="{ row }">
          <UBadge color="primary" variant="soft">{{ row.code }}</UBadge>
        </template>
        <template #name-data="{ row }">
          <span class="font-medium text-sm">{{ row.name }}</span>
        </template>
        <template #currency-data="{ row }">
          <div class="text-xs">
            <span class="font-semibold">{{ row.currency_symbol }}</span>
            <span class="text-gray-500 ml-1">({{ row.currency_code }})</span>
          </div>
        </template>
        <template #timezone-data="{ row }">
          <div class="text-xs">
            <span>{{ row.timezone }}</span>
            <UBadge class="ml-1" variant="soft" size="xs">{{ row.gmt_offset }}</UBadge>
          </div>
        </template>
        <template #locale-data="{ row }">
          <span class="text-xs font-mono">{{ row.locale }}</span>
        </template>
        <template #is_active-data="{ row }">
          <UIcon :name="row.is_active ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'" 
                 :class="row.is_active ? 'text-green-500' : 'text-gray-400'" class="w-4 h-4" />
        </template>
      </UTable>
    </UCard>

    <!-- Time Display Example -->
    <UCard>
      <template #header>
        <h3 class="font-semibold text-sm">Time Display Preview</h3>
      </template>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div class="p-3 bg-gray-50 rounded">
          <p class="text-xs text-gray-500 mb-1">Current Time (Local)</p>
          <p class="font-mono font-semibold">{{ formattedCurrentTime }}</p>
        </div>
        <div class="p-3 bg-gray-50 rounded">
          <p class="text-xs text-gray-500 mb-1">Example: Employee Check-in Time</p>
          <p class="font-mono font-semibold">08:30 ({{ currentSettings.gmt_offset || 'GMT+7' }})</p>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const { $api } = useNuxtApp()
const toast = useToast()
const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const seeding = ref(false)
const regions = ref<any[]>([])
const currentSettings = ref<any>({})
const originalRegion = ref('')
const selectedRegion = ref('')

const columns = [
  { key: 'code', label: 'Code' },
  { key: 'name', label: 'Country/Region' },
  { key: 'currency', label: 'Currency' },
  { key: 'timezone', label: 'Timezone' },
  { key: 'locale', label: 'Locale' },
  { key: 'is_active', label: 'Active' }
]

const regionOptions = computed(() => 
  regions.value.map(r => ({ label: `${r.name} (${r.currency_symbol} ${r.currency_code})`, value: r.code }))
)

const hasChanges = computed(() => selectedRegion.value !== originalRegion.value)

const formattedCurrentTime = computed(() => {
  const tz = currentSettings.value.timezone || 'Asia/Jakarta'
  const locale = currentSettings.value.locale || 'id-ID'
  return new Date().toLocaleString(locale, { 
    timeZone: tz, 
    dateStyle: 'medium', 
    timeStyle: 'short' 
  }) + ` (${currentSettings.value.gmt_offset || 'GMT+7'})`
})

const fetchRegions = async () => {
  loading.value = true
  try {
    const res = await $api.get('/config/regions', { params: { active_only: false } })
    regions.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchSettings = async () => {
  try {
    const res = await $api.get('/config/tenant-settings')
    currentSettings.value = res.data
    selectedRegion.value = res.data.region_code || ''
    originalRegion.value = res.data.region_code || ''
  } catch (e) {
    console.error(e)
  }
}

const seedRegions = async () => {
  seeding.value = true
  try {
    await $api.post('/config/regions/seed')
    toast.add({ title: 'Regions initialized successfully', color: 'green' })
    await fetchRegions()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to seed regions', color: 'red' })
  } finally {
    seeding.value = false
  }
}

const onRegionChange = () => {
  // Preview what settings will look like when saving
  const region = regions.value.find(r => r.code === selectedRegion.value)
  if (region) {
    currentSettings.value = {
      ...currentSettings.value,
      region_code: region.code,
      currency_code: region.currency_code,
      currency_symbol: region.currency_symbol,
      timezone: region.timezone,
      gmt_offset: region.gmt_offset,
      locale: region.locale
    }
  }
}

const saveSettings = async () => {
  if (!selectedRegion.value) {
    toast.add({ title: 'Please select a region', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const res = await $api.put('/config/tenant-settings', { region_code: selectedRegion.value })
    
    // Update auth store with new settings
    authStore.updateTenantSettings({
      region_code: currentSettings.value.region_code,
      locale: currentSettings.value.locale,
      timezone: currentSettings.value.timezone,
      gmt_offset: currentSettings.value.gmt_offset,
      currency: currentSettings.value.currency_code,
      currency_symbol: currentSettings.value.currency_symbol
    })
    
    toast.add({ title: 'Settings saved successfully', color: 'green' })
    originalRegion.value = selectedRegion.value
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Failed to save settings', color: 'red' })
  } finally {
    saving.value = false
  }
}

const resetChanges = () => {
  selectedRegion.value = originalRegion.value
  fetchSettings()
}

onMounted(() => {
  fetchRegions()
  fetchSettings()
})
</script>
