<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Vehicle Expenses</h2>
        <p class="text-gray-500">Track operational costs and miscellaneous expenses</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchExpenses">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">Add Expense</UButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard>
        <p class="text-sm text-gray-500">Total Expenses</p>
        <p class="text-2xl font-bold">Rp{{ formatNumber(totalExpenses) }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-gray-500">This Month</p>
        <p class="text-2xl font-bold">Rp{{ formatNumber(thisMonthExpenses) }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-gray-500">Fuel Expenses</p>
        <p class="text-2xl font-bold text-blue-500">Rp{{ formatNumber(fuelExpenses) }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-gray-500">Other Expenses</p>
        <p class="text-2xl font-bold text-orange-500">Rp{{ formatNumber(otherExpenses) }}</p>
      </UCard>
    </div>

    <UCard>
      <DataTable :columns="columns" :rows="expenses" :loading="loading" searchable :search-keys="['description']" empty-message="No expenses yet.">
        <template #vehicle_id-data="{ row }">
          <p class="font-medium">{{ getVehicleName(row.vehicle_id) }}</p>
        </template>
        <template #date-data="{ row }">
          <p>{{ formatDate(row.date) }}</p>
        </template>
        <template #category-data="{ row }">
          <UBadge :color="getCategoryColor(row.category)" variant="subtle" size="sm">{{ row.category }}</UBadge>
        </template>
        <template #description-data="{ row }">
          <p class="truncate max-w-48">{{ row.description }}</p>
        </template>
        <template #amount-data="{ row }">
          <p class="font-medium">Rp{{ formatNumber(row.amount) }}</p>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" icon="i-heroicons-pencil" variant="ghost" @click="openEdit(row)" />
            <UButton size="xs" icon="i-heroicons-trash" variant="ghost" color="red" @click="deleteExpense(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create/Edit Slideover -->
    <FormSlideover v-model="isSlideoverOpen" :title="editingExpense ? 'Edit Expense' : 'Add Expense'" :loading="saving" @submit="saveExpense">
      <UFormGroup label="Vehicle" required hint="Select the vehicle this expense belongs to">
        <USelect v-model="form.vehicle_id" :options="vehicleOptions" placeholder="Select vehicle..." />
      </UFormGroup>

      <UFormGroup label="Date" required hint="Date of the expense">
        <UInput v-model="form.date" type="date" />
      </UFormGroup>

      <UFormGroup label="Category" required hint="Type of expense">
        <USelect v-model="form.category" :options="categoryOptions" />
      </UFormGroup>

      <UFormGroup label="Description" required hint="Brief description of the expense">
        <UInput v-model="form.description" placeholder="e.g. Toll fee Jakarta - Bandung" />
      </UFormGroup>

      <UFormGroup label="Amount (Rp)" required hint="Total expense amount in Rupiah">
        <UInput v-model.number="form.amount" type="number" placeholder="e.g. 150000" />
      </UFormGroup>

      <UFormGroup label="Linked Booking" hint="Optional: link to a vehicle booking">
        <USelect v-model="form.booking_id" :options="bookingOptions" placeholder="Select booking (optional)..." />
      </UFormGroup>

      <UFormGroup label="Receipt URL" hint="URL or path to receipt image">
        <UInput v-model="form.receipt_url" placeholder="https://..." />
      </UFormGroup>

      <UFormGroup label="Notes" hint="Additional notes or details">
        <UTextarea v-model="form.notes" :rows="2" placeholder="Any additional information..." />
      </UFormGroup>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const loading = ref(true)
const saving = ref(false)
const isSlideoverOpen = ref(false)
const editingExpense = ref<any>(null)
const expenses = ref<any[]>([])
const vehicles = ref<any[]>([])
const bookings = ref<any[]>([])

const columns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'date', label: 'Date' },
  { key: 'category', label: 'Category' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' },
  { key: 'actions', label: '' }
]

const categoryOptions = [
  { label: 'Fuel', value: 'FUEL' },
  { label: 'Toll', value: 'TOLL' },
  { label: 'Parking', value: 'PARKING' },
  { label: 'Service', value: 'SERVICE' },
  { label: 'Tax', value: 'TAX' },
  { label: 'Insurance', value: 'INSURANCE' },
  { label: 'KIR', value: 'KIR' },
  { label: 'Other', value: 'OTHER' }
]

const vehicleOptions = computed(() => 
  vehicles.value.map((v: any) => ({ label: `${v.plate_number} - ${v.brand} ${v.model}`, value: v.id }))
)

const bookingOptions = computed(() => [
  { label: 'None', value: '' },
  ...bookings.value.map((b: any) => ({ label: `${b.code} - ${b.destination}`, value: b.id }))
])

const totalExpenses = computed(() => expenses.value.reduce((sum, e) => sum + (e.amount || 0), 0))
const thisMonthExpenses = computed(() => {
  const now = new Date()
  return expenses.value
    .filter(e => {
      const d = new Date(e.date)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .reduce((sum, e) => sum + (e.amount || 0), 0)
})
const fuelExpenses = computed(() => expenses.value.filter(e => e.category === 'FUEL').reduce((sum, e) => sum + (e.amount || 0), 0))
const otherExpenses = computed(() => expenses.value.filter(e => e.category !== 'FUEL').reduce((sum, e) => sum + (e.amount || 0), 0))

const form = reactive({
  vehicle_id: '',
  date: '',
  category: 'OTHER',
  description: '',
  amount: 0,
  booking_id: '',
  receipt_url: '',
  notes: ''
})

const fetchExpenses = async () => {
  loading.value = true
  try {
    const res = await $api.get('/fleet/expenses')
    expenses.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchVehicles = async () => {
  try {
    const res = await $api.get('/fleet/vehicles')
    vehicles.value = res.data
  } catch (e) { console.error(e) }
}

const fetchBookings = async () => {
  try {
    const res = await $api.get('/fleet/bookings')
    bookings.value = res.data
  } catch (e) { console.error(e) }
}

const getVehicleName = (id: string) => {
  const v = vehicles.value.find((v: any) => v.id === id)
  return v ? v.plate_number : '-'
}

const openCreate = () => {
  editingExpense.value = null
  Object.assign(form, {
    vehicle_id: '', date: new Date().toISOString().slice(0, 10),
    category: 'OTHER', description: '', amount: 0,
    booking_id: '', receipt_url: '', notes: ''
  })
  isSlideoverOpen.value = true
}

const openEdit = (expense: any) => {
  editingExpense.value = expense
  Object.assign(form, {
    vehicle_id: expense.vehicle_id,
    date: expense.date,
    category: expense.category,
    description: expense.description,
    amount: expense.amount,
    booking_id: expense.booking_id || '',
    receipt_url: expense.receipt_url || '',
    notes: expense.notes || ''
  })
  isSlideoverOpen.value = true
}

const saveExpense = async () => {
  if (!form.vehicle_id || !form.description || !form.amount) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.booking_id) delete payload.booking_id
    
    if (editingExpense.value) {
      await $api.put(`/fleet/expenses/${editingExpense.value.id}`, payload)
      toast.add({ title: 'Expense updated!' })
    } else {
      await $api.post('/fleet/expenses', payload)
      toast.add({ title: 'Expense added!' })
    }
    isSlideoverOpen.value = false
    fetchExpenses()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    saving.value = false
  }
}

const deleteExpense = async (expense: any) => {
  if (!confirm(`Delete expense "${expense.description}"?`)) return
  try {
    await $api.delete(`/fleet/expenses/${expense.id}`)
    toast.add({ title: 'Expense deleted!' })
    fetchExpenses()
  } catch (e) {
    toast.add({ title: 'Error', color: 'red' })
  }
}

const getCategoryColor = (cat: string) => {
  const colors: Record<string, string> = {
    FUEL: 'blue', TOLL: 'green', PARKING: 'yellow', SERVICE: 'purple',
    TAX: 'red', INSURANCE: 'cyan', KIR: 'orange'
  }
  return colors[cat] || 'gray'
}

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID') : '-'
const formatNumber = (n: number) => n?.toLocaleString('id-ID') || '0'

onMounted(() => {
  fetchExpenses()
  fetchVehicles()
  fetchBookings()
})
</script>
