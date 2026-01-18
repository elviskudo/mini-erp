<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Production Orders</h1>
        <p class="text-gray-500">Manage manufacturing production orders</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-table-cells" variant="outline" size="sm" @click="exportData('csv')">CSV</UButton>
        <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm" @click="exportData('xlsx')">XLS</UButton>
        <UButton icon="i-heroicons-document" variant="outline" size="sm" @click="exportData('pdf')">PDF</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Production Order</UButton>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ stats.draft }}</p>
          <p class="text-sm text-gray-500">Draft</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ stats.inProgress }}</p>
          <p class="text-sm text-gray-500">In Progress</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.completed }}</p>
          <p class="text-sm text-gray-500">Completed</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ stats.cancelled }}</p>
          <p class="text-sm text-gray-500">Cancelled</p>
        </div>
      </UCard>
    </div>

    <!-- Data Table -->
    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable 
        :columns="columns" 
        :rows="orders" 
        :loading="loading"
        search-placeholder="Search orders..."
      >
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">
            {{ row.status }}
          </UBadge>
        </template>
        <template #progress-data="{ row }">
          <div class="w-24">
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  class="bg-primary-500 h-2 rounded-full" 
                  :style="{ width: `${row.progress}%` }"
                ></div>
              </div>
              <span class="text-xs text-gray-500">{{ row.progress }}%</span>
            </div>
          </div>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="viewOrder(row)" />
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="editOrder(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Form Slideover -->
    <FormSlideover 
      v-model="showModal" 
      :title="editMode ? 'Edit Production Order' : 'New Production Order'"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="saveOrder"
    >
      <div class="space-y-4">
        <!-- Products Multi-Select Autocomplete -->
        <UFormGroup label="Products" required hint="Select products to manufacture" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu
            v-model="selectedProducts"
            :options="productOptions"
            multiple
            searchable
            searchable-placeholder="Search products..."
            placeholder="Select products..."
            :ui-menu="{ option: { base: 'cursor-pointer' } }"
          >
            <template #label>
              <span v-if="selectedProducts.length === 0" class="text-gray-400">Select products...</span>
              <span v-else>{{ selectedProducts.length }} product(s) selected</span>
            </template>
            <template #option="{ option }">
              <div class="flex flex-col">
                <span class="font-medium">{{ option.code }} - {{ option.name }}</span>
                <span class="text-xs text-gray-500">{{ option.type }} | {{ option.uom }}</span>
              </div>
            </template>
          </USelectMenu>
          <!-- Selected Products Display -->
          <div v-if="selectedProducts.length > 0" class="mt-2 flex flex-wrap gap-2">
            <UBadge 
              v-for="prod in selectedProducts" 
              :key="prod.id"
              color="primary"
              variant="soft"
              class="flex items-center gap-1"
            >
              {{ prod.code }} - {{ prod.name }}
              <UButton 
                icon="i-heroicons-x-mark" 
                size="2xs" 
                color="primary" 
                variant="link"
                @click="removeProduct(prod)"
              />
            </UBadge>
          </div>
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Quantity" required hint="Units to produce" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.quantity" type="number" min="1" />
          </UFormGroup>
          <UFormGroup label="Scheduled Date" hint="Production target date" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.scheduledDate" type="date" />
          </UFormGroup>
        </div>

        <!-- Work Centers Multi-Select Autocomplete -->
        <UFormGroup label="Work Centers">
          <USelectMenu
            v-model="selectedWorkCenters"
            :options="workCenterOptions"
            multiple
            searchable
            searchable-placeholder="Search work centers..."
            placeholder="Select work centers..."
          >
            <template #label>
              <span v-if="selectedWorkCenters.length === 0" class="text-gray-400">Select work centers...</span>
              <span v-else>{{ selectedWorkCenters.length }} work center(s) selected</span>
            </template>
            <template #option="{ option }">
              <div class="flex flex-col">
                <span class="font-medium">{{ option.code }} - {{ option.name }}</span>
              </div>
            </template>
          </USelectMenu>
          <!-- Selected Work Centers Display -->
          <div v-if="selectedWorkCenters.length > 0" class="mt-2 flex flex-wrap gap-2">
            <UBadge 
              v-for="wc in selectedWorkCenters" 
              :key="wc.id"
              color="gray"
              variant="soft"
              class="flex items-center gap-1"
            >
              {{ wc.code }} - {{ wc.name }}
              <UButton 
                icon="i-heroicons-x-mark" 
                size="2xs" 
                color="gray" 
                variant="link"
                @click="removeWorkCenter(wc)"
              />
            </UBadge>
          </div>
        </UFormGroup>
        
        <UFormGroup label="Notes">
          <UTextarea v-model="form.notes" rows="3" placeholder="Additional notes..." />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- View Order Modal with HPP and QC -->
    <UModal v-model="showViewModal" :ui="{ width: 'w-full sm:max-w-3xl' }">
      <UCard v-if="viewedOrder">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold">{{ viewedOrder.order_no }}</h3>
              <p class="text-sm text-gray-500">Production Order</p>
            </div>
            <UBadge :color="getStatusColor(viewedOrder.status)" variant="soft">{{ viewedOrder.status }}</UBadge>
          </div>
        </template>

        <!-- Tabs -->
        <UTabs :items="viewTabs" class="w-full">
          <template #item="{ item }">
            <div v-if="item.key === 'overview'" class="space-y-4 pt-4">
              <!-- Progress -->
              <div>
                <p class="text-sm text-gray-500 mb-1">Progress: {{ viewedOrder.completed_qty || 0 }} / {{ viewedOrder.quantity }}</p>
                <div class="flex items-center gap-3">
                  <div class="flex-1 bg-gray-200 rounded-full h-3">
                    <div class="bg-primary-500 h-3 rounded-full" :style="{ width: `${viewedOrder.progress}%` }"></div>
                  </div>
                  <span class="text-sm font-medium">{{ viewedOrder.progress }}%</span>
                </div>
              </div>

              <!-- Details Grid -->
              <div class="grid grid-cols-3 gap-4">
                <div>
                  <p class="text-sm text-gray-500">Target Qty</p>
                  <p class="font-medium">{{ viewedOrder.quantity }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">Completed</p>
                  <p class="font-medium text-green-600">{{ viewedOrder.completed_qty || 0 }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">Scheduled</p>
                  <p class="font-medium">{{ formatDate(viewedOrder.scheduled_date) }}</p>
                </div>
              </div>

              <!-- Products & Work Centers -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-500 mb-2">Products</p>
                  <div class="flex flex-wrap gap-1">
                    <UBadge v-for="p in viewedOrder.products" :key="p.id" color="primary" variant="soft" size="xs">
                      {{ p.product?.name }}
                    </UBadge>
                  </div>
                </div>
                <div>
                  <p class="text-sm text-gray-500 mb-2">Work Centers</p>
                  <div class="flex flex-wrap gap-1">
                    <UBadge v-for="wc in viewedOrder.work_centers" :key="wc.id" color="gray" variant="soft" size="xs">
                      {{ wc.work_center?.name }}
                    </UBadge>
                  </div>
                </div>
              </div>
            </div>

            <!-- HPP / Cost Tab -->
            <div v-else-if="item.key === 'cost'" class="space-y-4 pt-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="p-4 bg-blue-50 rounded-lg">
                  <p class="text-sm text-blue-600">Material Cost</p>
                  <p class="text-xl font-bold">Rp {{ formatNumber(viewedOrder.material_cost || 0) }}</p>
                </div>
                <div class="p-4 bg-green-50 rounded-lg">
                  <p class="text-sm text-green-600">Labor Cost</p>
                  <p class="text-xl font-bold">Rp {{ formatNumber(viewedOrder.labor_cost || 0) }}</p>
                </div>
                <div class="p-4 bg-yellow-50 rounded-lg">
                  <p class="text-sm text-yellow-600">Overhead Cost</p>
                  <p class="text-xl font-bold">Rp {{ formatNumber(viewedOrder.overhead_cost || 0) }}</p>
                </div>
                <div class="p-4 bg-purple-50 rounded-lg">
                  <p class="text-sm text-purple-600">HPP per Unit</p>
                  <p class="text-xl font-bold">Rp {{ formatNumber(viewedOrder.hpp_per_unit || 0) }}</p>
                </div>
              </div>
              
              <div class="p-4 bg-gray-100 rounded-lg">
                <p class="text-sm text-gray-600">Total HPP (COGM)</p>
                <p class="text-2xl font-bold text-primary-600">Rp {{ formatNumber(viewedOrder.total_hpp || 0) }}</p>
              </div>

              <!-- Calculate HPP Button -->
              <UButton v-if="!viewedOrder.total_hpp" color="primary" block @click="showHppModal = true">
                Calculate HPP
              </UButton>
            </div>

            <!-- QC Results Tab -->
            <div v-else-if="item.key === 'qc'" class="space-y-4 pt-4">
              <div class="grid grid-cols-4 gap-3">
                <div class="text-center p-3 bg-green-50 rounded-lg">
                  <p class="text-2xl font-bold text-green-600">{{ qcTotals.good }}</p>
                  <p class="text-xs text-gray-500">Good</p>
                </div>
                <div class="text-center p-3 bg-yellow-50 rounded-lg">
                  <p class="text-2xl font-bold text-yellow-600">{{ qcTotals.defect }}</p>
                  <p class="text-xs text-gray-500">Defect</p>
                </div>
                <div class="text-center p-3 bg-red-50 rounded-lg">
                  <p class="text-2xl font-bold text-red-600">{{ qcTotals.scrap }}</p>
                  <p class="text-xs text-gray-500">Scrap</p>
                </div>
                <div class="text-center p-3 bg-gray-100 rounded-lg">
                  <p class="text-2xl font-bold">{{ qcTotals.defect_rate }}%</p>
                  <p class="text-xs text-gray-500">Defect Rate</p>
                </div>
              </div>

              <UButton color="primary" block @click="showQcModal = true">
                Record QC Result
              </UButton>
            </div>
          </template>
        </UTabs>

        <template #footer>
          <div class="flex justify-between">
            <div class="flex gap-2">
              <UButton v-if="viewedOrder.status === 'Draft'" color="yellow" @click="startProduction">
                Start Production
              </UButton>
              <UButton v-if="viewedOrder.status === 'In Progress'" color="green" @click="showProgressModal = true">
                Record Progress
              </UButton>
              <UButton v-if="viewedOrder.status === 'In Progress'" color="blue" variant="outline" @click="showQcModal = true">
                Record QC
              </UButton>
              <UButton v-if="viewedOrder.status === 'Completed'" color="primary" icon="i-heroicons-archive-box-arrow-down" @click="transferToStock">
                Transfer to Stock
              </UButton>
            </div>
            <UButton color="gray" variant="ghost" @click="showViewModal = false">Close</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- HPP Calculator Modal -->
    <UModal v-model="showHppModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Calculate HPP</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Labor Hours" hint="Total work hours" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="hppForm.labor_hours" type="number" step="0.5" placeholder="e.g. 8" />
          </UFormGroup>
          <UFormGroup label="Hourly Rate" hint="Cost per labor hour" :ui="{ hint: 'text-xs text-gray-400' }">
            <CurrencyInput v-model="hppForm.hourly_rate" :currency="currencyCode" />
          </UFormGroup>
          <UFormGroup label="Overhead Rate (%)" hint="Factory overhead %" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="hppForm.overhead_rate" type="number" step="1" placeholder="15" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showHppModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="calculateHpp">Calculate</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- QC Recording Modal -->
    <UModal v-model="showQcModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Record QC Result</h3>
        </template>
        <div class="space-y-4">
          <div class="grid grid-cols-3 gap-4">
            <UFormGroup label="Good Qty" hint="Units passed QC" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model="qcForm.good_qty" type="number" min="0" />
            </UFormGroup>
            <UFormGroup label="Defect Qty" hint="Needs rework" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model="qcForm.defect_qty" type="number" min="0" />
            </UFormGroup>
            <UFormGroup label="Scrap Qty" hint="Unsalvageable" :ui="{ hint: 'text-xs text-gray-400' }">
              <UInput v-model="qcForm.scrap_qty" type="number" min="0" />
            </UFormGroup>
          </div>
          
          <UFormGroup v-if="qcForm.scrap_qty > 0" label="Scrap Type" hint="Classification" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="qcForm.scrap_type" :options="scrapTypeOptions" />
          </UFormGroup>
          
          <UFormGroup v-if="qcForm.scrap_qty > 0" label="Scrap Reason" hint="Root cause" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="qcForm.scrap_reason" placeholder="e.g. Oven temperature unstable" />
          </UFormGroup>
          
          <UFormGroup v-if="qcForm.scrap_type === 'Total Loss'" label="Spoilage Expense" hint="Loss amount" :ui="{ hint: 'text-xs text-gray-400' }">
            <CurrencyInput v-model="qcForm.spoilage_expense" :currency="currencyCode" />
          </UFormGroup>
          
          <UFormGroup label="Notes" hint="Additional info" :ui="{ hint: 'text-xs text-gray-400' }">
            <UTextarea v-model="qcForm.notes" rows="2" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showQcModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="recordQc">Save QC Result</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Progress Recording Modal -->
    <UModal v-model="showProgressModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Record Production Progress</h3>
        </template>
        <div class="space-y-4">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="grid grid-cols-3 gap-4 text-center">
              <div>
                <p class="text-sm text-gray-500">Target Qty</p>
                <p class="text-xl font-bold">{{ viewedOrder?.quantity || 0 }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">Completed</p>
                <p class="text-xl font-bold text-green-600">{{ viewedOrder?.completed_qty || 0 }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">Remaining</p>
                <p class="text-xl font-bold text-orange-600">{{ Math.max(0, (viewedOrder?.quantity || 0) - (viewedOrder?.completed_qty || 0)) }}</p>
              </div>
            </div>
            <div class="mt-3">
              <div class="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span>{{ viewedOrder?.progress || 0 }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-green-500 h-2 rounded-full transition-all" :style="{ width: (viewedOrder?.progress || 0) + '%' }"></div>
              </div>
            </div>
          </div>
          
          <UFormGroup label="Completed Quantity" hint="Units completed in this batch" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="progressForm.completed_qty" type="number" min="0" placeholder="e.g. 100" />
          </UFormGroup>
          
          <UFormGroup label="Notes (Optional)" hint="Any notes for this progress entry" :ui="{ hint: 'text-xs text-gray-400' }">
            <UTextarea v-model="progressForm.notes" rows="2" placeholder="e.g. Batch completed without issues" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" @click="showProgressModal = false">Cancel</UButton>
            <UButton :loading="submitting" @click="recordProgress">Save Progress</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const { currencyCode, formatCurrency } = useCurrency()
const toast = useToast()
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const editMode = ref(false)

// Data
const orders = ref<any[]>([])
const products = ref<any[]>([])
const workCenters = ref<any[]>([])

// Selected items for multi-select
const selectedProducts = ref<any[]>([])
const selectedWorkCenters = ref<any[]>([])

const form = reactive({
  id: '',
  quantity: 1,
  scheduledDate: '',
  notes: ''
})

// Form validation - button enabled only when required fields are filled
const isFormValid = computed(() => {
    return selectedProducts.value.length > 0 && form.quantity > 0
})

// View modal state
const showViewModal = ref(false)
const viewedOrder = ref<any>(null)

// HPP Modal state
const showHppModal = ref(false)
const hppForm = reactive({
  labor_hours: 0,
  hourly_rate: 25000,
  overhead_rate: 15
})

// QC Modal state
const showQcModal = ref(false)
const qcForm = reactive({
  good_qty: 0,
  defect_qty: 0,
  scrap_qty: 0,
  scrap_type: '',
  scrap_reason: '',
  spoilage_expense: 0,
  notes: ''
})

const qcTotals = ref({
  good: 0,
  defect: 0,
  scrap: 0,
  defect_rate: 0
})

// Progress Modal state
const showProgressModal = ref(false)
const progressForm = reactive({
  completed_qty: 0,
  notes: ''
})

const scrapTypeOptions = [
  { label: 'Total Loss (Disposed)', value: 'Total Loss' },
  { label: 'Grade B (Sell at lower price)', value: 'Grade B' },
  { label: 'Rework (Reprocess)', value: 'Rework' }
]

const viewTabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'cost', label: 'HPP/Cost' },
  { key: 'qc', label: 'QC Results' }
]

const stats = reactive({
  draft: 0,
  inProgress: 0,
  completed: 0,
  cancelled: 0
})

const columns = [
  { key: 'orderNo', label: 'Order No' },
  { key: 'product', label: 'Product' },
  { key: 'quantity', label: 'Qty' },
  { key: 'status', label: 'Status' },
  { key: 'progress', label: 'Progress' },
  { key: 'scheduledDate', label: 'Scheduled' },
  { key: 'actions', label: '' }
]

// Computed options for autocomplete
const productOptions = computed(() => {
  return products.value.map(p => ({
    ...p,
    label: `${p.code} - ${p.name} (${p.type}, ${p.uom})`
  }))
})

const workCenterOptions = computed(() => {
  return workCenters.value.map(wc => ({
    ...wc,
    label: `${wc.code} - ${wc.name}`
  }))
})

const resetForm = () => {
  Object.assign(form, {
    id: '',
    quantity: 1,
    scheduledDate: '',
    notes: ''
  })
  selectedProducts.value = []
  selectedWorkCenters.value = []
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'Draft': return 'gray'
    case 'In Progress': return 'yellow'
    case 'Completed': return 'green'
    case 'Cancelled': return 'red'
    default: return 'gray'
  }
}

// Helper to safely extract array from API response
const extractArray = (res: any): any[] => {
  if (Array.isArray(res)) return res
  if (res?.data && Array.isArray(res.data)) return res.data
  if (res?.data?.data && Array.isArray(res.data.data)) return res.data.data
  return []
}

// Fetch data
const fetchData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    
    // Fetch products
    const productsRes: any = await $fetch('/api/manufacturing/products', { headers })
    products.value = extractArray(productsRes)
    
    // Fetch work centers
    const wcRes: any = await $fetch('/api/manufacturing/work-centers', { headers })
    workCenters.value = extractArray(wcRes)
    
    // Fetch production orders
    const ordersRes: any = await $fetch('/api/manufacturing/production-orders', { headers })
    const ordersData = extractArray(ordersRes)
    // Transform data for table display
    orders.value = ordersData.map((o: any) => ({
      ...o,
      orderNo: o.order_no,
      product: o.products?.map((p: any) => p.product?.name).join(', ') || 'N/A',
      scheduledDate: o.scheduled_date ? new Date(o.scheduled_date).toLocaleDateString() : 'N/A'
    }))
    
    // Calculate stats
    stats.draft = orders.value.filter((o: any) => o.status === 'Draft').length
    stats.inProgress = orders.value.filter((o: any) => o.status === 'In Progress').length
    stats.completed = orders.value.filter((o: any) => o.status === 'Completed').length
    stats.cancelled = orders.value.filter((o: any) => o.status === 'Cancelled').length
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  resetForm()
  editMode.value = false
  showModal.value = true
}

const editOrder = (row: any) => {
  // Populate form with existing data
  form.id = row.id
  form.quantity = row.quantity
  form.scheduledDate = row.scheduled_date ? row.scheduled_date.split('T')[0] : ''
  form.notes = row.notes || ''
  
  // Populate selected products
  if (row.products && row.products.length > 0) {
    selectedProducts.value = row.products.map((p: any) => {
      const product = p.product
      return {
        ...product,
        label: `${product.code} - ${product.name} (${product.type}, ${product.uom})`
      }
    })
  } else {
    selectedProducts.value = []
  }
  
  // Populate selected work centers
  if (row.work_centers && row.work_centers.length > 0) {
    selectedWorkCenters.value = row.work_centers.map((wc: any) => {
      const workCenter = wc.work_center
      return {
        ...workCenter,
        label: `${workCenter.code} - ${workCenter.name}`
      }
    })
  } else {
    selectedWorkCenters.value = []
  }
  
  editMode.value = true
  showModal.value = true
}

const viewOrder = (row: any) => {
  viewedOrder.value = row
  showViewModal.value = true
}

const updateStatus = async (status: string, progress: number) => {
  if (!viewedOrder.value) return
  
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/status?status=${status}&progress=${progress}`, {
      method: 'PUT',
      headers
    })
    toast.add({ title: 'Success', description: `Order status updated to ${status}`, color: 'green' })
    showViewModal.value = false
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to update status', color: 'red' })
  }
}

const removeProduct = (prod: any) => {
  selectedProducts.value = selectedProducts.value.filter(p => p.id !== prod.id)
}

const removeWorkCenter = (wc: any) => {
  selectedWorkCenters.value = selectedWorkCenters.value.filter(w => w.id !== wc.id)
}

const saveOrder = async () => {
  if (selectedProducts.value.length === 0) {
    toast.add({ title: 'Error', description: 'Please select at least one product', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const payload = {
      product_ids: selectedProducts.value.map((p: any) => p.id),
      work_center_ids: selectedWorkCenters.value.map((wc: any) => wc.id),
      quantity: form.quantity,
      scheduled_date: form.scheduledDate || null,
      notes: form.notes || null
    }
    
    if (editMode.value && form.id) {
      await $fetch(`/api/manufacturing/production-orders/${form.id}`, {
        method: 'PUT',
        body: payload,
        headers
      })
      toast.add({ title: 'Success', description: 'Production order updated successfully', color: 'green' })
    } else {
      await $fetch('/api/manufacturing/production-orders', {
        method: 'POST',
        body: payload,
        headers
      })
      toast.add({ title: 'Success', description: 'Production order created successfully', color: 'green' })
    }
    
    showModal.value = false
    resetForm()
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to save order', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Helper functions
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('id-ID').format(num)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID')
}

// HPP Calculation
const calculateHpp = async () => {
  if (!viewedOrder.value) return
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const result: any = await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/calculate-hpp`, {
      method: 'POST',
      headers,
      body: {
        labor_hours: hppForm.labor_hours,
        hourly_rate: hppForm.hourly_rate,
        overhead_rate: hppForm.overhead_rate / 100
      }
    })
    
    // Update viewed order with HPP data
    viewedOrder.value = {
      ...viewedOrder.value,
      material_cost: result.material_cost,
      labor_cost: result.labor_cost,
      overhead_cost: result.overhead_cost,
      total_hpp: result.total_hpp,
      hpp_per_unit: result.hpp_per_unit
    }
    
    showHppModal.value = false
    toast.add({ title: 'Success', description: 'HPP calculated successfully', color: 'green' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to calculate HPP', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Record QC Result
const recordQc = async () => {
  if (!viewedOrder.value) return
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/record-qc`, {
      method: 'POST',
      headers,
      body: qcForm
    })
    
    toast.add({ title: 'Success', description: 'QC result recorded', color: 'green' })
    showQcModal.value = false
    
    // Reset form
    Object.assign(qcForm, {
      good_qty: 0, defect_qty: 0, scrap_qty: 0,
      scrap_type: '', scrap_reason: '', spoilage_expense: 0, notes: ''
    })
    
    // Refresh data
    await fetchQcResults()
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to record QC', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Fetch QC Results for current order
const fetchQcResults = async () => {
  if (!viewedOrder.value) return
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const result: any = await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/qc-results`, { headers })
    qcTotals.value = result.totals || { good: 0, defect: 0, scrap: 0, defect_rate: 0 }
  } catch (e) {
    console.error('Failed to fetch QC results', e)
  }
}

// Start Production
const startProduction = async () => {
  if (!viewedOrder.value) return
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/record-progress`, {
      method: 'POST',
      headers,
      body: { completed_qty: 0 }  // Just to trigger status change
    })
    toast.add({ title: 'Started', description: 'Production started', color: 'green' })
    showViewModal.value = false
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to start production', color: 'red' })
  }
}

// Record Progress
const recordProgress = async () => {
  if (!viewedOrder.value) return
  
  const qty = Number(progressForm.completed_qty)
  if (qty <= 0) {
    toast.add({ title: 'Error', description: 'Please enter a valid quantity', color: 'red' })
    return
  }
  
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const result: any = await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/record-progress`, {
      method: 'POST',
      headers,
      body: { 
        completed_qty: qty,
        notes: progressForm.notes
      }
    })
    
    // Update viewed order with new values
    viewedOrder.value.completed_qty = result.completed_qty
    viewedOrder.value.progress = result.progress
    viewedOrder.value.status = result.status
    
    toast.add({ 
      title: 'Progress Recorded', 
      description: `Added ${qty} units. Progress: ${result.progress}%`, 
      color: 'green' 
    })
    
    // Reset form
    progressForm.completed_qty = 0
    progressForm.notes = ''
    showProgressModal.value = false
    
    // Refresh data
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to record progress', color: 'red' })
  } finally {
    submitting.value = false
  }
}

// Transfer to Stock
const transferToStock = async () => {
  if (!viewedOrder.value) return
  
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const result: any = await $fetch(`/api/manufacturing/production-orders/${viewedOrder.value.id}/transfer-to-stock`, {
      method: 'POST',
      headers,
      body: {}
    })
    
    toast.add({ 
      title: 'Transferred to Stock', 
      description: result.message, 
      color: 'green' 
    })
    
    showViewModal.value = false
    fetchData()
  } catch (e: any) {
    const errorMsg = e?.data?.detail || 'Failed to transfer to stock'
    toast.add({ title: 'Error', description: errorMsg, color: 'red' })
  }
}

const exportData = async (format: string) => {
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const res = await $fetch(`/api/export/production-orders?format=${format}`, { 
      headers,
      responseType: 'blob'
    })
    
    const blob = res as Blob
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `production_orders_${new Date().toISOString().split('T')[0]}.${format}`
    a.click()
    window.URL.revokeObjectURL(url)
    toast.add({ title: 'Exported', description: `Data exported to ${format.toUpperCase()}`, color: 'green' })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to export data', color: 'red' })
  }
}

onMounted(() => {
  fetchData()
})
</script>

