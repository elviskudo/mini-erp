<template>
  <div class="flex min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-6">
      <h1 class="text-xl font-bold text-gray-900 mb-2">Settings</h1>
      <p class="text-sm text-gray-500 mb-6">Configure your company</p>
      
      <nav class="space-y-1">
        <button
          v-for="(item, idx) in menuItems"
          :key="idx"
          @click="activeSection = item.key"
          class="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors"
          :class="[
            activeSection === item.key 
              ? 'bg-primary-50 text-primary-700 font-medium' 
              : 'text-gray-600 hover:bg-gray-50'
          ]"
        >
          <UIcon :name="item.icon" class="w-5 h-5" />
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </div>

    <!-- Content -->
    <div class="flex-1 p-8">
      <UCard class="max-w-3xl">
        <!-- Company Info Section -->
        <div v-if="activeSection === 'company'" class="space-y-6">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Company Information</h2>
            <p class="text-sm text-gray-500">Basic company details</p>
          </div>
          
          <UFormGroup label="Company Name" required>
            <UInput v-model="settings.company_name" placeholder="Enter company name" />
          </UFormGroup>
          
          <UFormGroup label="Company Logo">
            <div 
              class="relative border-2 border-dashed rounded-lg p-6 transition-colors"
              :class="[isDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400']"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleDrop"
            >
              <div v-if="logoPreview" class="flex items-center gap-4">
                <img :src="logoPreview" alt="Logo preview" class="w-20 h-20 object-contain rounded-lg border" />
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900">{{ logoFile?.name }}</p>
                  <p class="text-xs text-gray-500">{{ formatFileSize(logoFile?.size || 0) }}</p>
                </div>
                <UButton icon="i-heroicons-trash" color="red" variant="ghost" @click="removeLogo" />
              </div>
              <div v-else class="text-center">
                <UIcon name="i-heroicons-cloud-arrow-up" class="w-10 h-10 text-gray-400 mx-auto mb-2" />
                <p class="text-sm text-gray-600 mb-1">
                  <span class="text-primary-600 font-medium cursor-pointer" @click="triggerFileInput">Click to upload</span>
                  or drag and drop
                </p>
                <p class="text-xs text-gray-500">PNG, JPG up to 2MB</p>
              </div>
              <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/jpg" class="hidden" @change="handleFileSelect" />
            </div>
          </UFormGroup>
          
          <UFormGroup label="Industry">
            <USelect v-model="settings.industry" :options="industries" placeholder="Select industry" />
          </UFormGroup>
          
          <div class="flex justify-end pt-4 border-t">
            <UButton :loading="saving" @click="saveSettings">Save Changes</UButton>
          </div>
        </div>

        <!-- Regional Section -->
        <div v-if="activeSection === 'regional'" class="space-y-6">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Regional Settings</h2>
            <p class="text-sm text-gray-500">Timezone and date format preferences</p>
          </div>
          
          <UFormGroup label="Timezone">
            <USelect v-model="settings.timezone" :options="timezones" />
          </UFormGroup>
          
          <UFormGroup label="Date Format">
            <USelect v-model="settings.date_format" :options="dateFormats" />
          </UFormGroup>
          
          <div class="flex justify-end pt-4 border-t">
            <UButton :loading="saving" @click="saveSettings">Save Changes</UButton>
          </div>
        </div>

        <!-- Currency Section -->
        <div v-if="activeSection === 'currency'" class="space-y-6">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Currency Settings</h2>
            <p class="text-sm text-gray-500">Configure how currency is displayed throughout the system</p>
          </div>
          
          <UFormGroup label="Currency">
            <USelect 
              v-model="settings.currency_code" 
              :options="currencyOptions"
              option-attribute="label"
              value-attribute="code"
              @change="onCurrencyChange"
            />
          </UFormGroup>
          
          <UFormGroup label="Currency Symbol">
            <UInput v-model="settings.currency_symbol" placeholder="e.g. Rp, $, €" />
          </UFormGroup>
          
          <UFormGroup label="Symbol Position">
            <USelect v-model="settings.currency_position" :options="positionOptions" />
          </UFormGroup>
          
          <div class="grid grid-cols-3 gap-4">
            <UFormGroup label="Thousand Separator">
              <USelect v-model="settings.thousand_separator" :options="['.', ',', ' ']" />
            </UFormGroup>
            <UFormGroup label="Decimal Separator">
              <USelect v-model="settings.decimal_separator" :options="[',', '.']" />
            </UFormGroup>
            <UFormGroup label="Decimal Places">
              <USelect v-model="settings.decimal_places" :options="['0', '2', '3']" />
            </UFormGroup>
          </div>
          
          <UCard class="bg-gray-50">
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-1">Preview</p>
              <p class="text-2xl font-bold text-gray-900">{{ currencyPreview }}</p>
            </div>
          </UCard>
          
          <div class="flex justify-end pt-4 border-t">
            <UButton :loading="saving" @click="saveSettings">Save Changes</UButton>
          </div>
        </div>

        <!-- Payment Gateways Section -->
        <div v-if="activeSection === 'payment'" class="space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">Payment Gateways</h2>
              <p class="text-sm text-gray-500">Configure payment integrations</p>
            </div>
            <UButton icon="i-heroicons-plus" @click="openAddGateway">Add Gateway</UButton>
          </div>
          
          <div v-if="gateways.length === 0" class="text-center py-12 text-gray-500">
            <UIcon name="i-heroicons-credit-card" class="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No payment gateways configured</p>
            <p class="text-sm">Click "Add Gateway" to get started</p>
          </div>
          
          <div v-else class="space-y-4">
            <UCard v-for="gateway in gateways" :key="gateway.id" :ui="{ body: { padding: 'p-4' } }">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                    <UIcon :name="getGatewayIcon(gateway.gateway_type)" class="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <p class="font-medium text-gray-900">{{ gateway.name }}</p>
                    <p class="text-sm text-gray-500">{{ gateway.gateway_type }} · API Key: {{ gateway.api_key }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <UBadge :color="gateway.is_active ? 'green' : 'gray'">
                    {{ gateway.is_active ? 'Active' : 'Inactive' }}
                  </UBadge>
                  <UBadge v-if="gateway.is_sandbox" color="yellow">Sandbox</UBadge>
                  <UDropdown :items="[[
                    { label: 'Edit', icon: 'i-heroicons-pencil', click: () => editGateway(gateway) },
                    { label: 'Delete', icon: 'i-heroicons-trash', click: () => deleteGateway(gateway.id) }
                  ]]">
                    <UButton icon="i-heroicons-ellipsis-vertical" variant="ghost" color="gray" />
                  </UDropdown>
                </div>
              </div>
            </UCard>
          </div>
        </div>

        <!-- Storage Section -->
        <div v-if="activeSection === 'storage'" class="space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">Cloud Storage</h2>
              <p class="text-sm text-gray-500">Configure file storage providers (Cloudinary, AWS S3, etc.)</p>
            </div>
            <UButton icon="i-heroicons-plus" @click="openAddStorage">Add Provider</UButton>
          </div>
          
          <div v-if="storageProviders.length === 0" class="text-center py-12 text-gray-500">
            <UIcon name="i-heroicons-cloud" class="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No storage providers configured</p>
            <p class="text-sm">Click "Add Provider" to configure cloud storage</p>
          </div>
          
          <div v-else class="space-y-4">
            <UCard v-for="provider in storageProviders" :key="provider.id" :ui="{ body: { padding: 'p-4' } }">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <UIcon :name="getStorageIcon(provider.storage_type)" class="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p class="font-medium text-gray-900">{{ provider.name }}</p>
                    <p class="text-sm text-gray-500">{{ provider.storage_type }} · {{ provider.bucket_name || provider.cloud_name || 'Local' }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <UBadge :color="provider.is_active ? 'green' : 'gray'">
                    {{ provider.is_active ? 'Active' : 'Inactive' }}
                  </UBadge>
                  <UBadge v-if="provider.is_default" color="blue">Default</UBadge>
                  <UDropdown :items="[[
                    { label: 'Edit', icon: 'i-heroicons-pencil', click: () => editStorage(provider) },
                    { label: 'Delete', icon: 'i-heroicons-trash', click: () => deleteStorage(provider.id) }
                  ]]">
                    <UButton icon="i-heroicons-ellipsis-vertical" variant="ghost" color="gray" />
                  </UDropdown>
                </div>
              </div>
            </UCard>
          </div>
        </div>

        <!-- Warehouse Section -->
        <div v-if="activeSection === 'warehouse'" class="space-y-6">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Default Warehouse</h2>
            <p class="text-sm text-gray-500">Set up your primary warehouse location</p>
          </div>
          
          <UFormGroup label="Warehouse Name" required>
            <UInput v-model="warehouseSettings.name" placeholder="e.g. Main Warehouse" />
          </UFormGroup>
          
          <UFormGroup label="Location (Click map to set)">
            <ClientOnly>
              <div class="relative rounded-lg overflow-hidden border border-gray-300">
                <div id="warehouse-map" class="h-64 w-full"></div>
                <div v-if="mapLoading" class="absolute inset-0 flex items-center justify-center bg-gray-100">
                  <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-gray-500" />
                </div>
              </div>
              <template #fallback>
                <div class="h-64 w-full bg-gray-100 rounded-lg flex items-center justify-center">
                  <span class="text-gray-500">Loading map...</span>
                </div>
              </template>
            </ClientOnly>
            <p v-if="warehouseSettings.lat && warehouseSettings.lng" class="text-xs text-gray-500 mt-1">
              📍 Lat: {{ warehouseSettings.lat.toFixed(6) }}, Lng: {{ warehouseSettings.lng.toFixed(6) }}
            </p>
          </UFormGroup>
          
          <UFormGroup label="Address">
            <UTextarea v-model="warehouseSettings.address" placeholder="Address will be filled when you click on the map" rows="3" readonly />
          </UFormGroup>
          
          <div class="flex justify-end pt-4 border-t">
            <UButton :loading="saving" @click="saveWarehouse">Save Warehouse</UButton>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Add/Edit Gateway Modal -->
    <UModal v-model="showGatewayModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">{{ editingGateway ? 'Edit' : 'Add' }} Payment Gateway</h3>
        </template>
        
        <div class="space-y-4">
          <UFormGroup label="Name" required>
            <UInput v-model="gatewayForm.name" placeholder="e.g. Stripe Production" />
          </UFormGroup>
          
          <UFormGroup label="Gateway Type">
            <USelect v-model="gatewayForm.gateway_type" :options="gatewayTypes" />
          </UFormGroup>
          
          <UFormGroup label="API Key">
            <UInput v-model="gatewayForm.api_key" placeholder="pk_live_xxx or similar" />
          </UFormGroup>
          
          <UFormGroup label="API Secret">
            <UInput v-model="gatewayForm.api_secret" type="password" placeholder="sk_live_xxx or similar" />
          </UFormGroup>
          
          <UFormGroup label="Webhook Secret">
            <UInput v-model="gatewayForm.webhook_secret" type="password" placeholder="whsec_xxx (optional)" />
          </UFormGroup>
          
          <div class="flex items-center gap-6">
            <UCheckbox v-model="gatewayForm.is_active" label="Active" />
            <UCheckbox v-model="gatewayForm.is_sandbox" label="Sandbox/Test Mode" />
          </div>
          
          <UFormGroup label="Notes">
            <UTextarea v-model="gatewayForm.notes" placeholder="Optional notes" rows="2" />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showGatewayModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="saveGateway">
              {{ editingGateway ? 'Update' : 'Add' }} Gateway
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Add/Edit Storage Modal -->
    <UModal v-model="showStorageModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">{{ editingStorage ? 'Edit' : 'Add' }} Storage Provider</h3>
        </template>
        
        <div class="space-y-4">
          <UFormGroup label="Name" required>
            <UInput v-model="storageForm.name" placeholder="e.g. Cloudinary Production" />
          </UFormGroup>
          
          <UFormGroup label="Storage Type">
            <USelect v-model="storageForm.storage_type" :options="storageTypes" />
          </UFormGroup>
          
          <!-- Cloudinary Fields -->
          <template v-if="storageForm.storage_type === 'Cloudinary'">
            <UFormGroup label="Cloud Name">
              <UInput v-model="storageForm.cloud_name" placeholder="your-cloud-name" />
            </UFormGroup>
            <UFormGroup label="API Key">
              <UInput v-model="storageForm.api_key" placeholder="123456789012345" />
            </UFormGroup>
            <UFormGroup label="API Secret">
              <UInput v-model="storageForm.api_secret" type="password" placeholder="your-api-secret" />
            </UFormGroup>
          </template>
          
          <!-- AWS S3 Fields -->
          <template v-if="storageForm.storage_type === 'AWS S3'">
            <UFormGroup label="Bucket Name">
              <UInput v-model="storageForm.bucket_name" placeholder="my-bucket" />
            </UFormGroup>
            <UFormGroup label="Region">
              <USelect v-model="storageForm.region" :options="awsRegions" />
            </UFormGroup>
            <UFormGroup label="Access Key ID">
              <UInput v-model="storageForm.access_key_id" placeholder="AKIAIOSFODNN7EXAMPLE" />
            </UFormGroup>
            <UFormGroup label="Secret Access Key">
              <UInput v-model="storageForm.secret_access_key" type="password" placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" />
            </UFormGroup>
          </template>
          
          <UFormGroup label="Base URL (CDN)">
            <UInput v-model="storageForm.base_url" placeholder="https://cdn.example.com (optional)" />
          </UFormGroup>
          
          <div class="flex items-center gap-6">
            <UCheckbox v-model="storageForm.is_active" label="Active" />
            <UCheckbox v-model="storageForm.is_default" label="Set as Default" />
          </div>
          
          <UFormGroup label="Notes">
            <UTextarea v-model="storageForm.notes" placeholder="Optional notes" rows="2" />
          </UFormGroup>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showStorageModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="saveStorage">
              {{ editingStorage ? 'Update' : 'Add' }} Provider
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth',
  layout: 'default'
})

const authStore = useAuthStore()
const toast = useToast()

const activeSection = ref('company')
const saving = ref(false)

const menuItems = [
  { key: 'company', label: 'Company Info', icon: 'i-heroicons-building-office' },
  { key: 'regional', label: 'Regional', icon: 'i-heroicons-globe-alt' },
  { key: 'currency', label: 'Currency', icon: 'i-heroicons-currency-dollar' },
  { key: 'payment', label: 'Payment', icon: 'i-heroicons-credit-card' },
  { key: 'storage', label: 'Storage', icon: 'i-heroicons-cloud' },
  { key: 'warehouse', label: 'Warehouse', icon: 'i-heroicons-building-storefront' }
]

// Settings state
const settings = reactive({
  company_name: '',
  company_logo_url: '',
  industry: '',
  currency_code: 'IDR',
  currency_symbol: 'Rp',
  currency_position: 'before',
  decimal_separator: ',',
  thousand_separator: '.',
  decimal_places: '0',
  timezone: 'Asia/Jakarta',
  date_format: 'DD/MM/YYYY'
})

// Options
const industries = ['Manufacturing', 'Retail', 'Wholesale', 'Services', 'Technology', 'Food & Beverage', 'Other']

const timezones = [
  { label: 'Asia/Jakarta (WIB)', value: 'Asia/Jakarta' },
  { label: 'Asia/Makassar (WITA)', value: 'Asia/Makassar' },
  { label: 'Asia/Jayapura (WIT)', value: 'Asia/Jayapura' },
  { label: 'Asia/Singapore', value: 'Asia/Singapore' }
]

const dateFormats = [
  { label: 'DD/MM/YYYY', value: 'DD/MM/YYYY' },
  { label: 'MM/DD/YYYY', value: 'MM/DD/YYYY' },
  { label: 'YYYY-MM-DD', value: 'YYYY-MM-DD' }
]

const currencyOptions = [
  { code: 'IDR', symbol: 'Rp', label: 'IDR - Indonesian Rupiah' },
  { code: 'USD', symbol: '$', label: 'USD - US Dollar' },
  { code: 'EUR', symbol: '€', label: 'EUR - Euro' },
  { code: 'GBP', symbol: '£', label: 'GBP - British Pound' },
  { code: 'SGD', symbol: 'S$', label: 'SGD - Singapore Dollar' },
  { code: 'MYR', symbol: 'RM', label: 'MYR - Malaysian Ringgit' }
]

const positionOptions = [
  { label: 'Before amount (e.g. Rp 10.000)', value: 'before' },
  { label: 'After amount (e.g. 10.000 Rp)', value: 'after' }
]

const gatewayTypes = ['Stripe', 'Midtrans', 'Xendit', 'PayPal', 'Manual']

// Currency preview
const currencyPreview = computed(() => {
  const num = 30000
  const dec = parseInt(settings.decimal_places) || 0
  let formatted = num.toFixed(dec)
  const parts = formatted.split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, settings.thousand_separator)
  formatted = dec > 0 ? parts.join(settings.decimal_separator) : parts[0]
  return settings.currency_position === 'before' 
    ? `${settings.currency_symbol} ${formatted}` 
    : `${formatted} ${settings.currency_symbol}`
})

const onCurrencyChange = (code: string) => {
  const currency = currencyOptions.find(c => c.code === code)
  if (currency) {
    settings.currency_symbol = currency.symbol
  }
}

// Payment gateways
const gateways = ref<any[]>([])
const showGatewayModal = ref(false)
const editingGateway = ref<any>(null)
const gatewayForm = reactive({
  name: '',
  gateway_type: 'Stripe',
  api_key: '',
  api_secret: '',
  webhook_secret: '',
  is_active: true,
  is_sandbox: false,
  notes: ''
})

const getGatewayIcon = (type: string) => {
  const icons: Record<string, string> = {
    'Stripe': 'i-heroicons-credit-card',
    'Midtrans': 'i-heroicons-banknotes',
    'Xendit': 'i-heroicons-currency-dollar',
    'PayPal': 'i-heroicons-wallet',
    'Manual': 'i-heroicons-document-text'
  }
  return icons[type] || 'i-heroicons-credit-card'
}

const openAddGateway = () => {
  editingGateway.value = null
  Object.assign(gatewayForm, {
    name: '', gateway_type: 'Stripe', api_key: '', api_secret: '',
    webhook_secret: '', is_active: true, is_sandbox: false, notes: ''
  })
  showGatewayModal.value = true
}

const editGateway = async (gateway: any) => {
  editingGateway.value = gateway
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const data = await $fetch(`/api/settings/payment-gateways/${gateway.id}`, { headers })
    Object.assign(gatewayForm, data)
    showGatewayModal.value = true
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load gateway details', color: 'red' })
  }
}

const saveGateway = async () => {
  if (!gatewayForm.name) {
    toast.add({ title: 'Error', description: 'Name is required', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    if (editingGateway.value) {
      await $fetch(`/api/settings/payment-gateways/${editingGateway.value.id}`, {
        method: 'PUT', headers, body: gatewayForm
      })
      toast.add({ title: 'Success', description: 'Gateway updated' })
    } else {
      await $fetch('/api/settings/payment-gateways', {
        method: 'POST', headers, body: gatewayForm
      })
      toast.add({ title: 'Success', description: 'Gateway added' })
    }
    showGatewayModal.value = false
    fetchGateways()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.data?.detail || 'Failed to save gateway', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteGateway = async (id: string) => {
  if (!confirm('Delete this payment gateway?')) return
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/settings/payment-gateways/${id}`, { method: 'DELETE', headers })
    toast.add({ title: 'Deleted', description: 'Gateway removed' })
    fetchGateways()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' })
  }
}

const fetchGateways = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    gateways.value = await $fetch('/api/settings/payment-gateways', { headers })
  } catch (e) {
    console.error('Failed to fetch gateways', e)
  }
}

// Storage providers
const storageProviders = ref<any[]>([])
const showStorageModal = ref(false)
const editingStorage = ref<any>(null)
const storageForm = reactive({
  name: '',
  storage_type: 'Cloudinary',
  bucket_name: '',
  region: '',
  base_url: '',
  api_key: '',
  api_secret: '',
  cloud_name: '',
  access_key_id: '',
  secret_access_key: '',
  is_active: true,
  is_default: false,
  notes: ''
})

const storageTypes = ['Local', 'Cloudinary', 'AWS S3', 'Google Cloud Storage', 'Azure Blob Storage']

const awsRegions = [
  'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
  'eu-west-1', 'eu-west-2', 'eu-central-1',
  'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
]

const getStorageIcon = (type: string) => {
  const icons: Record<string, string> = {
    'Local': 'i-heroicons-server',
    'Cloudinary': 'i-heroicons-cloud',
    'AWS S3': 'i-heroicons-circle-stack',
    'Google Cloud Storage': 'i-heroicons-cloud',
    'Azure Blob Storage': 'i-heroicons-cloud'
  }
  return icons[type] || 'i-heroicons-cloud'
}

const openAddStorage = () => {
  editingStorage.value = null
  Object.assign(storageForm, {
    name: '', storage_type: 'Cloudinary', bucket_name: '', region: '',
    base_url: '', api_key: '', api_secret: '', cloud_name: '',
    access_key_id: '', secret_access_key: '', is_active: true, is_default: false, notes: ''
  })
  showStorageModal.value = true
}

const editStorage = async (provider: any) => {
  editingStorage.value = provider
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const data = await $fetch(`/api/settings/storage-providers/${provider.id}`, { headers })
    Object.assign(storageForm, data)
    showStorageModal.value = true
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load provider details', color: 'red' })
  }
}

const saveStorage = async () => {
  if (!storageForm.name) {
    toast.add({ title: 'Error', description: 'Name is required', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    if (editingStorage.value) {
      await $fetch(`/api/settings/storage-providers/${editingStorage.value.id}`, {
        method: 'PUT', headers, body: storageForm
      })
      toast.add({ title: 'Success', description: 'Storage provider updated' })
    } else {
      await $fetch('/api/settings/storage-providers', {
        method: 'POST', headers, body: storageForm
      })
      toast.add({ title: 'Success', description: 'Storage provider added' })
    }
    showStorageModal.value = false
    fetchStorageProviders()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.data?.detail || 'Failed to save provider', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteStorage = async (id: string) => {
  if (!confirm('Delete this storage provider?')) return
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/settings/storage-providers/${id}`, { method: 'DELETE', headers })
    toast.add({ title: 'Deleted', description: 'Provider removed' })
    fetchStorageProviders()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' })
  }
}

const fetchStorageProviders = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // First sync storage from env (will only create if not exists)
    await $fetch('/api/settings/storage-sync-env', { method: 'POST', headers }).catch(() => {})
    
    // Then fetch all providers
    storageProviders.value = await $fetch('/api/settings/storage-providers', { headers })
  } catch (e) {
    console.error('Failed to fetch storage providers', e)
  }
}

const fetchWarehouse = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const data = await $fetch('/api/settings/warehouse', { headers }) as any
    if (data) {
      warehouseSettings.name = data.name || ''
      warehouseSettings.address = data.address || ''
    }
  } catch (e) {
    console.error('Failed to fetch warehouse', e)
  }
}

// Logo handling
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const logoFile = ref<File | null>(null)
const logoPreview = ref<string | null>(null)

const triggerFileInput = () => fileInput.value?.click()

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) processFile(file)
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) processFile(file)
}

const processFile = (file: File) => {
  if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
    toast.add({ title: 'Error', description: 'Please upload a PNG or JPG image', color: 'red' })
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    toast.add({ title: 'Error', description: 'File size must be less than 2MB', color: 'red' })
    return
  }
  logoFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => { logoPreview.value = e.target?.result as string }
  reader.readAsDataURL(file)
}

const removeLogo = () => {
  logoFile.value = null
  logoPreview.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Warehouse
const warehouseSettings = reactive({
  name: '',
  address: '',
  lat: null as number | null,
  lng: null as number | null
})

const mapLoading = ref(true)
let map: any = null
let marker: any = null

watch(activeSection, async (section) => {
  if (section === 'warehouse') {
    await nextTick()
    setTimeout(() => initMap(), 100)
  }
})

const initMap = async () => {
  if (typeof window === 'undefined') return
  const mapContainer = document.getElementById('warehouse-map')
  if (!mapContainer || map) return
  
  const L = await import('leaflet')
  if (!document.querySelector('link[href*="leaflet.css"]')) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
  }
  
  let defaultLat = -6.2088, defaultLng = 106.8456
  map = L.map('warehouse-map').setView([defaultLat, defaultLng], 13)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map)
  mapLoading.value = false
  
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(async (position) => {
      const { latitude, longitude } = position.coords
      map.setView([latitude, longitude], 15)
      if (marker) marker.setLatLng([latitude, longitude])
      else marker = L.marker([latitude, longitude]).addTo(map)
      warehouseSettings.lat = latitude
      warehouseSettings.lng = longitude
      await reverseGeocode(latitude, longitude)
    }, () => {}, { enableHighAccuracy: true, timeout: 10000 })
  }
  
  map.on('click', async (e: any) => {
    const { lat, lng } = e.latlng
    if (marker) marker.setLatLng([lat, lng])
    else marker = L.marker([lat, lng]).addTo(map)
    warehouseSettings.lat = lat
    warehouseSettings.lng = lng
    await reverseGeocode(lat, lng)
  })
}

const reverseGeocode = async (lat: number, lng: number) => {
  try {
    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`, { headers: { 'Accept-Language': 'en' } })
    const data = await response.json()
    if (data.display_name) warehouseSettings.address = data.display_name
  } catch (e) {
    warehouseSettings.address = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`
  }
}

// API calls
const fetchSettings = async () => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const data = await $fetch('/api/settings', { headers })
    Object.assign(settings, data)
    if (data.company_logo_url) {
      logoPreview.value = data.company_logo_url
    }
  } catch (e) {
    console.error('Failed to fetch settings', e)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // Upload logo if new file selected
    if (logoFile.value) {
      const formData = new FormData()
      formData.append('file', logoFile.value)
      
      const uploadResult = await $fetch('/api/settings/upload-logo', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authStore.token}` },
        body: formData
      }) as any
      
      if (uploadResult?.url) {
        settings.company_logo_url = uploadResult.url
        logoPreview.value = uploadResult.url
        logoFile.value = null // Clear file after upload
      }
    }
    
    // Save other settings
    await $fetch('/api/settings', { method: 'PUT', headers, body: settings })
    toast.add({ title: 'Success', description: 'Settings saved successfully' })
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.data?.detail || 'Failed to save settings', color: 'red' })
  } finally {
    saving.value = false
  }
}

const saveWarehouse = async () => {
  if (!warehouseSettings.name) {
    toast.add({ title: 'Error', description: 'Warehouse name is required', color: 'red' })
    return
  }
  saving.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // Try to update existing warehouse first
    try {
      await $fetch('/api/settings/warehouse', {
        method: 'PUT', headers,
        body: { name: warehouseSettings.name, address: warehouseSettings.address || '-' }
      })
      toast.add({ title: 'Success', description: 'Warehouse updated successfully' })
    } catch (updateErr: any) {
      // If no warehouse exists, create new one
      if (updateErr.status === 404) {
        const warehouseCode = warehouseSettings.name.toUpperCase().replace(/[^A-Z0-9]/g, '-').substring(0, 10) + '-WH'
        await $fetch('/api/inventory/warehouses', {
          method: 'POST', headers,
          body: { code: warehouseCode, name: warehouseSettings.name, address: warehouseSettings.address || '-' }
        })
        toast.add({ title: 'Success', description: 'Warehouse created successfully' })
      } else {
        throw updateErr
      }
    }
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.data?.detail || 'Failed to save warehouse', color: 'red' })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchSettings()
  fetchGateways()
  fetchStorageProviders()
  fetchWarehouse()
})
</script>
