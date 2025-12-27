<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Customers</h2>
        <p class="text-gray-500">Customer database and contacts</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Customer</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ customers.length }}</p>
          <p class="text-sm text-gray-500">Total Customers</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ formatCurrency(totalBalance) }}</p>
          <p class="text-sm text-gray-500">Total Balance</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ formatCurrency(totalCreditLimit) }}</p>
          <p class="text-sm text-gray-500">Total Credit Limit</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ overdueCustomers }}</p>
          <p class="text-sm text-gray-500">Near Limit</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="customers" 
        :loading="loading"
        searchable
        :search-keys="['name', 'email', 'phone']"
        empty-message="No customers yet. Add new or convert from a Lead."
      >
        <template #name-data="{ row }">
          <div>
            <p class="font-medium">{{ row.name }}</p>
            <p class="text-xs text-gray-400">{{ row.email || 'No email' }}</p>
          </div>
        </template>
        <template #phone-data="{ row }">
          <span>{{ row.phone || '-' }}</span>
        </template>
        <template #credit_limit-data="{ row }">
          <span>{{ formatCurrency(row.credit_limit) }}</span>
        </template>
        <template #current_balance-data="{ row }">
          <span :class="row.current_balance > row.credit_limit * 0.8 ? 'text-red-500 font-medium' : ''">
            {{ formatCurrency(row.current_balance) }}
          </span>
        </template>
        <template #utilization-data="{ row }">
          <div v-if="row.credit_limit > 0" class="flex items-center gap-2">
            <div class="w-16 bg-gray-200 rounded-full h-2">
              <div 
                class="h-2 rounded-full" 
                :class="getUtilizationColor(row.current_balance / row.credit_limit * 100)"
                :style="{ width: `${Math.min((row.current_balance / row.credit_limit * 100), 100)}%` }"
              ></div>
            </div>
            <span class="text-xs">{{ Math.round(row.current_balance / row.credit_limit * 100) }}%</span>
          </div>
          <span v-else class="text-gray-400 text-xs">No limit</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewCustomer(row)" />
            <UButton icon="i-heroicons-pencil-square" size="xs" color="gray" variant="ghost" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="isEditing ? 'Edit Customer' : 'Add Customer'"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Customer data for transactions and AR tracking.</p>
        
        <UFormGroup label="Customer Name" required hint="Company or individual name" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="e.g., ABC Corp" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Email" hint="Primary email" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.email" type="email" placeholder="email@example.com" />
          </UFormGroup>
          <UFormGroup label="Phone" hint="Contact number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.phone" placeholder="+1..." />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Address" hint="Full address" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.address" rows="2" placeholder="Full address..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Credit Limit" hint="Credit limit amount" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.credit_limit" type="number" />
          </UFormGroup>
          <UFormGroup label="Current Balance" hint="Current balance" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model.number="form.current_balance" type="number" disabled />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>

    <!-- View Customer Modal -->
    <UModal v-model="showView" :ui="{ width: 'max-w-2xl' }">
      <UCard v-if="selectedCustomer">
        <template #header>
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedCustomer.name }}</h3>
              <p class="text-sm text-gray-500">{{ selectedCustomer.email || 'No email' }}</p>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500">Phone</p>
              <p class="font-medium">{{ selectedCustomer.phone || '-' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Credit Limit</p>
              <p class="font-medium">{{ formatCurrency(selectedCustomer.credit_limit) }}</p>
            </div>
          </div>
          
          <div>
            <p class="text-sm text-gray-500">Address</p>
            <p>{{ selectedCustomer.address || '-' }}</p>
          </div>
          
          <div class="border-t pt-4">
            <div class="flex justify-between items-center">
              <span>Current Balance</span>
              <span class="text-xl font-bold" :class="selectedCustomer.current_balance > selectedCustomer.credit_limit * 0.8 ? 'text-red-500' : 'text-green-600'">
                {{ formatCurrency(selectedCustomer.current_balance) }}
              </span>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showView = false">Close</UButton>
            <UButton icon="i-heroicons-pencil-square" @click="showView = false; openEdit(selectedCustomer)">Edit</UButton>
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
const showView = ref(false)
const selectedCustomer = ref<any>(null)

const customers = ref<any[]>([])

const columns = [
  { key: 'name', label: 'Customer', sortable: true },
  { key: 'phone', label: 'Phone' },
  { key: 'credit_limit', label: 'Credit Limit', sortable: true },
  { key: 'current_balance', label: 'Balance', sortable: true },
  { key: 'utilization', label: 'Utilization' },
  { key: 'actions', label: '' }
]

const form = reactive({
  name: '',
  email: '',
  phone: '',
  address: '',
  credit_limit: 0,
  current_balance: 0
})

const totalBalance = computed(() => customers.value.reduce((sum, c) => sum + (c.current_balance || 0), 0))
const totalCreditLimit = computed(() => customers.value.reduce((sum, c) => sum + (c.credit_limit || 0), 0))
const overdueCustomers = computed(() => customers.value.filter(c => c.credit_limit > 0 && c.current_balance > c.credit_limit * 0.8).length)

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val || 0)

const getUtilizationColor = (percent: number) => {
  if (percent >= 90) return 'bg-red-500'
  if (percent >= 70) return 'bg-yellow-500'
  return 'bg-green-500'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await $api.get('/ar/customers')
    customers.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, { name: '', email: '', phone: '', address: '', credit_limit: 0, current_balance: 0 })
  isOpen.value = true
}

const openEdit = (row: any) => {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, row)
  isOpen.value = true
}

const viewCustomer = (row: any) => {
  selectedCustomer.value = row
  showView.value = true
}

const save = async () => {
  if (!form.name) {
    toast.add({ title: 'Error', description: 'Name is required', color: 'red' })
    return
  }
  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      await $api.put(`/ar/customers/${editingId.value}`, form)
      toast.add({ title: 'Updated', description: 'Customer updated successfully', color: 'green' })
    } else {
      await $api.post('/ar/customers', form)
      toast.add({ title: 'Created', description: 'Customer created successfully', color: 'green' })
    }
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const confirmDelete = async (row: any) => {
  if (!confirm(`Delete customer "${row.name}"?`)) return
  try {
    await $api.delete(`/ar/customers/${row.id}`)
    toast.add({ title: 'Deleted', description: 'Customer deleted successfully', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

onMounted(() => { fetchData() })
</script>
