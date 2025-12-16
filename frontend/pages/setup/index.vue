<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Initial Setup</h1>
        <p class="text-gray-500">Configure your company settings to get started</p>
      </div>
    </div>

    <!-- Setup Progress -->
    <UCard>
      <div class="flex items-center gap-4 mb-6">
        <div v-for="(step, idx) in steps" :key="idx" class="flex items-center">
          <div 
            class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            :class="[
              currentStep > idx ? 'bg-green-500 text-white' :
              currentStep === idx ? 'bg-primary-500 text-white' :
              'bg-gray-200 text-gray-500'
            ]"
          >
            <UIcon v-if="currentStep > idx" name="i-heroicons-check" class="w-5 h-5" />
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <span class="ml-2 text-sm font-medium" :class="currentStep >= idx ? 'text-gray-900' : 'text-gray-400'">
            {{ step.title }}
          </span>
          <div v-if="idx < steps.length - 1" class="w-12 h-0.5 mx-3 bg-gray-200"></div>
        </div>
      </div>
    </UCard>

    <!-- Step Content -->
    <UCard>
      <!-- Step 1: Company Info -->
      <div v-if="currentStep === 0" class="space-y-4">
        <h2 class="text-lg font-semibold">Company Information</h2>
        
        <UFormGroup label="Company Name" required>
          <UInput v-model="settings.companyName" placeholder="Enter company name" />
        </UFormGroup>
        
        <UFormGroup label="Company Logo">
          <div class="flex items-center gap-4">
            <div class="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
              <UIcon name="i-heroicons-photo" class="w-8 h-8 text-gray-400" />
            </div>
            <UButton variant="outline">Upload Logo</UButton>
          </div>
        </UFormGroup>
        
        <UFormGroup label="Industry">
          <USelect v-model="settings.industry" :options="industries" placeholder="Select industry" />
        </UFormGroup>
      </div>

      <!-- Step 2: Regional Settings -->
      <div v-if="currentStep === 1" class="space-y-4">
        <h2 class="text-lg font-semibold">Regional Settings</h2>
        
        <UFormGroup label="Default Currency" required>
          <USelect v-model="settings.currency" :options="currencies" />
        </UFormGroup>
        
        <UFormGroup label="Timezone" required>
          <USelect v-model="settings.timezone" :options="timezones" />
        </UFormGroup>
        
        <UFormGroup label="Date Format">
          <USelect v-model="settings.dateFormat" :options="dateFormats" />
        </UFormGroup>
      </div>

      <!-- Step 3: Warehouse -->
      <div v-if="currentStep === 2" class="space-y-4">
        <h2 class="text-lg font-semibold">Default Warehouse</h2>
        <p class="text-sm text-gray-500">Set up your primary warehouse location</p>
        
        <UFormGroup label="Warehouse Name" required>
          <UInput v-model="settings.warehouseName" placeholder="e.g. Main Warehouse" />
        </UFormGroup>
        
        <UFormGroup label="Address">
          <UTextarea v-model="settings.warehouseAddress" placeholder="Enter warehouse address" rows="3" />
        </UFormGroup>
      </div>

      <!-- Step 4: Complete -->
      <div v-if="currentStep === 3" class="text-center py-8">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <UIcon name="i-heroicons-check" class="w-8 h-8 text-green-600" />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Setup Complete!</h2>
        <p class="text-gray-500 mb-6">Your company is ready to use Mini ERP</p>
        <UButton @click="navigateTo('/')">Go to Dashboard</UButton>
      </div>

      <!-- Navigation -->
      <div v-if="currentStep < 3" class="flex justify-between mt-8 pt-6 border-t">
        <UButton 
          v-if="currentStep > 0" 
          variant="ghost" 
          @click="currentStep--"
        >
          Back
        </UButton>
        <div v-else></div>
        
        <UButton @click="nextStep">
          {{ currentStep === 2 ? 'Complete Setup' : 'Next' }}
        </UButton>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const currentStep = ref(0)

const steps = [
  { title: 'Company Info' },
  { title: 'Regional' },
  { title: 'Warehouse' },
  { title: 'Complete' }
]

const settings = reactive({
  companyName: '',
  industry: '',
  currency: 'IDR',
  timezone: 'Asia/Jakarta',
  dateFormat: 'DD/MM/YYYY',
  warehouseName: '',
  warehouseAddress: ''
})

const industries = [
  'Manufacturing',
  'Retail',
  'Wholesale',
  'Services',
  'Technology',
  'Food & Beverage',
  'Other'
]

const currencies = [
  { label: 'IDR - Indonesian Rupiah', value: 'IDR' },
  { label: 'USD - US Dollar', value: 'USD' },
  { label: 'EUR - Euro', value: 'EUR' },
  { label: 'SGD - Singapore Dollar', value: 'SGD' }
]

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

const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}
</script>
