<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Payroll Management</h2>
        <p class="text-gray-500 text-sm">Process salaries, generate payslips, and manage payroll periods</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/hr">
          <UButton variant="ghost" icon="i-heroicons-arrow-left">Back</UButton>
        </NuxtLink>
        <UDropdown :items="exportItems">
          <UButton variant="soft" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-plus" @click="showPeriodModal = true">New Period</UButton>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-primary-600">{{ periods.length }}</p>
          <p class="text-sm text-gray-500">Payroll Periods</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ formatCurrency(totalPaidThisMonth) }}</p>
          <p class="text-sm text-gray-500">Paid This Month</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ pendingPeriods }}</p>
          <p class="text-sm text-gray-500">Pending Runs</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ employeeCount }}</p>
          <p class="text-sm text-gray-500">Active Employees</p>
        </div>
      </UCard>
    </div>

    <!-- Tabs -->
    <UTabs :items="tabs" v-model="activeTab">
      <template #default="{ item, selected }">
        <span :class="selected ? 'text-primary-600' : 'text-gray-500'">{{ item.label }}</span>
      </template>
    </UTabs>

    <!-- Payroll Periods -->
    <UCard v-if="activeTab === 0">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Payroll Periods</h3>
          <USelect v-model="filterYear" :options="yearOptions" class="w-32" />
        </div>
      </template>

      <div class="space-y-4">
        <div 
          v-for="period in filteredPeriods" 
          :key="period.id" 
          class="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div 
                class="w-12 h-12 rounded-lg flex items-center justify-center"
                :class="getStatusBgColor(period.status)"
              >
                <UIcon 
                  :name="period.is_closed ? 'i-heroicons-check-circle' : 'i-heroicons-clock'" 
                  :class="getStatusTextColor(period.status)"
                  class="w-6 h-6"
                />
              </div>
              <div>
                <h4 class="font-semibold">{{ period.name }}</h4>
                <p class="text-sm text-gray-500">
                  {{ formatDate(period.start_date) }} - {{ formatDate(period.end_date) }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <UBadge :color="getStatusColor(period.status)" variant="subtle">
                {{ period.status }}
              </UBadge>
              <div class="flex gap-2">
                <UButton 
                  v-if="!period.is_closed"
                  size="sm" 
                  color="green"
                  @click="runPayroll(period)"
                  :loading="runningPayroll === period.id"
                  icon="i-heroicons-play"
                >
                  Run Payroll
                </UButton>
                <UButton 
                  size="sm" 
                  variant="soft"
                  @click="viewPeriod(period)"
                  icon="i-heroicons-eye"
                >
                  View
                </UButton>
              </div>
            </div>
          </div>
        </div>

        <div v-if="filteredPeriods.length === 0" class="text-center py-8 text-gray-500">
          No payroll periods found for {{ filterYear }}
        </div>
      </div>
    </UCard>

    <!-- Payslips -->
    <UCard v-if="activeTab === 1">
      <template #header>
        <div class="flex items-center justify-between flex-wrap gap-4">
          <h3 class="font-semibold">Payslips</h3>
          <div class="flex gap-2">
            <USelectMenu 
              v-model="selectedEmployeeForSlip" 
              :options="employeeOptions"
              searchable
              placeholder="Select employee"
              class="w-64"
              @update:modelValue="fetchPayslips"
            />
          </div>
        </div>
      </template>

      <div v-if="!selectedEmployeeForSlip" class="text-center py-8 text-gray-500">
        Select an employee to view their payslips
      </div>
      
      <div v-else-if="payslips.length === 0" class="text-center py-8 text-gray-500">
        No payslips found for this employee
      </div>

      <div v-else class="space-y-3">
        <div 
          v-for="slip in payslips" 
          :key="slip.id"
          class="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
          @click="viewPayslip(slip)"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium">{{ formatCurrency(slip.net_pay) }}</p>
              <p class="text-sm text-gray-500">{{ formatDateTime(slip.created_at) }}</p>
            </div>
            <div class="text-right">
              <UBadge :color="slip.is_paid ? 'green' : 'yellow'" size="sm">
                {{ slip.is_paid ? 'Paid' : 'Pending' }}
              </UBadge>
              <p class="text-xs text-gray-500 mt-1">
                Gross: {{ formatCurrency(slip.gross_pay) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Salary Components -->
    <UCard v-if="activeTab === 2">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Salary Components</h3>
          <UButton size="sm" icon="i-heroicons-plus" @click="showComponentModal = true">
            Add Component
          </UButton>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <UCard 
          v-for="comp in salaryComponents" 
          :key="comp.id" 
          :ui="{ body: { padding: 'p-4' } }"
        >
          <div class="flex items-center justify-between mb-2">
            <UBadge :color="comp.component_type === 'EARNING' ? 'green' : 'red'" size="xs">
              {{ comp.component_type }}
            </UBadge>
            <UBadge v-if="comp.is_taxable" color="gray" size="xs">Taxable</UBadge>
          </div>
          <h4 class="font-semibold">{{ comp.name }}</h4>
          <p class="text-sm text-gray-500">Code: {{ comp.code }}</p>
          <p class="text-sm text-gray-500" v-if="comp.default_amount > 0">
            Default: {{ formatCurrency(comp.default_amount) }}
          </p>
        </UCard>
      </div>
    </UCard>

    <!-- Period Detail Modal -->
    <UModal v-model="showPeriodDetail" :ui="{ width: 'max-w-4xl' }">
      <UCard v-if="selectedPeriod">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{{ selectedPeriod.name }}</h3>
            <UBadge :color="getStatusColor(selectedPeriod.status)">{{ selectedPeriod.status }}</UBadge>
          </div>
        </template>

        <div v-if="selectedPayrollRun" class="space-y-6">
          <!-- Summary -->
          <div class="grid grid-cols-4 gap-4">
            <div class="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p class="text-2xl font-bold text-primary-600">{{ selectedPayrollRun.total_employees }}</p>
              <p class="text-sm text-gray-500">Employees</p>
            </div>
            <div class="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p class="text-2xl font-bold text-green-600">{{ formatCurrency(selectedPayrollRun.total_gross) }}</p>
              <p class="text-sm text-gray-500">Total Gross</p>
            </div>
            <div class="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p class="text-2xl font-bold text-red-600">{{ formatCurrency(selectedPayrollRun.total_deductions) }}</p>
              <p class="text-sm text-gray-500">Total Deductions</p>
            </div>
            <div class="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p class="text-2xl font-bold text-blue-600">{{ formatCurrency(selectedPayrollRun.total_net) }}</p>
              <p class="text-sm text-gray-500">Total Net Pay</p>
            </div>
          </div>

          <!-- Payslips List -->
          <div>
            <h4 class="font-semibold mb-3">Employee Payslips</h4>
            <UTable :columns="payslipColumns" :rows="periodPayslips" :loading="loadingPayslips">
              <template #employee_name-data="{ row }">
                <span class="font-medium">{{ row.employee_name || 'Unknown' }}</span>
              </template>
              <template #gross_pay-data="{ row }">
                {{ formatCurrency(row.gross_pay) }}
              </template>
              <template #total_deductions-data="{ row }">
                <span class="text-red-600">{{ formatCurrency(row.total_deductions) }}</span>
              </template>
              <template #net_pay-data="{ row }">
                <span class="font-semibold text-green-600">{{ formatCurrency(row.net_pay) }}</span>
              </template>
              <template #is_paid-data="{ row }">
                <UBadge :color="row.is_paid ? 'green' : 'yellow'" size="sm">
                  {{ row.is_paid ? 'Paid' : 'Pending' }}
                </UBadge>
              </template>
            </UTable>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
          No payroll run data available. Run payroll to generate payslips.
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showPeriodDetail = false">Close</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Payslip Detail Modal -->
    <UModal v-model="showPayslipDetail">
      <UCard v-if="selectedPayslip">
        <template #header>
          <h3 class="font-semibold">Payslip Details</h3>
        </template>

        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-gray-500">Employee</p>
              <p class="font-medium">{{ selectedPayslip.employee_name }}</p>
            </div>
            <div>
              <p class="text-gray-500">Employee Code</p>
              <p class="font-medium">{{ selectedPayslip.employee_code }}</p>
            </div>
          </div>

          <UDivider label="Earnings" />
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span>Base Salary</span>
              <span class="font-medium">{{ formatCurrency(selectedPayslip.base_salary) }}</span>
            </div>
            <div class="flex justify-between">
              <span>Allowances</span>
              <span class="font-medium">{{ formatCurrency(selectedPayslip.allowances) }}</span>
            </div>
            <div class="flex justify-between">
              <span>Overtime</span>
              <span class="font-medium">{{ formatCurrency(selectedPayslip.overtime_pay) }}</span>
            </div>
            <div class="flex justify-between">
              <span>Bonus</span>
              <span class="font-medium">{{ formatCurrency(selectedPayslip.bonus) }}</span>
            </div>
            <div class="flex justify-between font-semibold text-green-600 pt-2 border-t">
              <span>Gross Pay</span>
              <span>{{ formatCurrency(selectedPayslip.gross_pay) }}</span>
            </div>
          </div>

          <UDivider label="Deductions" />
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span>Tax (PPh 21)</span>
              <span class="text-red-600">{{ formatCurrency(selectedPayslip.tax_deduction) }}</span>
            </div>
            <div class="flex justify-between">
              <span>BPJS Kesehatan</span>
              <span class="text-red-600">{{ formatCurrency(selectedPayslip.bpjs_kes_deduction) }}</span>
            </div>
            <div class="flex justify-between">
              <span>BPJS Ketenagakerjaan</span>
              <span class="text-red-600">{{ formatCurrency(selectedPayslip.bpjs_tk_deduction) }}</span>
            </div>
            <div class="flex justify-between">
              <span>Other Deductions</span>
              <span class="text-red-600">{{ formatCurrency(selectedPayslip.other_deductions) }}</span>
            </div>
            <div class="flex justify-between font-semibold text-red-600 pt-2 border-t">
              <span>Total Deductions</span>
              <span>{{ formatCurrency(selectedPayslip.total_deductions) }}</span>
            </div>
          </div>

          <div class="bg-primary-50 dark:bg-primary-900 p-4 rounded-lg">
            <div class="flex justify-between items-center">
              <span class="font-semibold text-lg">Net Pay</span>
              <span class="font-bold text-2xl text-primary-600">{{ formatCurrency(selectedPayslip.net_pay) }}</span>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showPayslipDetail = false">Close</UButton>
            <UButton icon="i-heroicons-printer">Print</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- New Period Slideover -->
    <USlideover v-model="showPeriodModal" :ui="{ width: 'max-w-md' }">
      <UCard class="h-full flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Create Payroll Period</h3>
            <UButton icon="i-heroicons-x-mark" variant="ghost" @click="showPeriodModal = false" />
          </div>
        </template>
        <div class="flex-1 overflow-y-auto space-y-4 p-1">
          <UFormGroup label="Period Name" required>
            <UInput v-model="periodForm.name" placeholder="e.g. January 2024" />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Month" required>
              <USelect v-model="periodForm.period_month" :options="monthOptions" />
            </UFormGroup>
            <UFormGroup label="Year" required>
              <USelect v-model="periodForm.period_year" :options="yearOptions" />
            </UFormGroup>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Start Date" required>
              <UInput v-model="periodForm.start_date" type="date" />
            </UFormGroup>
            <UFormGroup label="End Date" required>
              <UInput v-model="periodForm.end_date" type="date" />
            </UFormGroup>
          </div>
          <UFormGroup label="Payment Date">
            <UInput v-model="periodForm.payment_date" type="date" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showPeriodModal = false">Cancel</UButton>
            <UButton @click="createPeriod" :loading="saving">Create</UButton>
          </div>
        </template>
      </UCard>
    </USlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ layout: 'default' })

const tabs = [
  { label: 'Payroll Periods', key: 'periods' },
  { label: 'Payslips', key: 'payslips' },
  { label: 'Salary Components', key: 'components' }
]
const activeTab = ref(0)

const periods = ref<any[]>([])
const payslips = ref<any[]>([])
const periodPayslips = ref<any[]>([])
const salaryComponents = ref<any[]>([])
const employees = ref<any[]>([])

const loading = ref(false)
const saving = ref(false)
const loadingPayslips = ref(false)
const runningPayroll = ref<string | null>(null)

const filterYear = ref(new Date().getFullYear().toString())
const selectedEmployeeForSlip = ref<string | null>(null)

const exportItems = [[
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') },
  { label: 'Export as XLS', icon: 'i-heroicons-table-cells', click: () => exportData('xls') },
  { label: 'Export as CSV', icon: 'i-heroicons-document-text', click: () => exportData('csv') }
]]

const exportData = (format: string) => {
  const url = `/api/hr/export/payroll?format=${format}&year=${filterYear.value}`
  window.open(url, '_blank')
}

const showPeriodModal = ref(false)
const showPeriodDetail = ref(false)
const showPayslipDetail = ref(false)
const showComponentModal = ref(false)

const selectedPeriod = ref<any>(null)
const selectedPayrollRun = ref<any>(null)
const selectedPayslip = ref<any>(null)

const periodForm = ref({
  name: '',
  period_month: new Date().getMonth() + 1,
  period_year: new Date().getFullYear(),
  start_date: '',
  end_date: '',
  payment_date: ''
})

const payslipColumns = [
  { key: 'employee_name', label: 'Employee' },
  { key: 'gross_pay', label: 'Gross Pay' },
  { key: 'total_deductions', label: 'Deductions' },
  { key: 'net_pay', label: 'Net Pay' },
  { key: 'is_paid', label: 'Status' }
]

const monthOptions = [
  { label: 'January', value: 1 },
  { label: 'February', value: 2 },
  { label: 'March', value: 3 },
  { label: 'April', value: 4 },
  { label: 'May', value: 5 },
  { label: 'June', value: 6 },
  { label: 'July', value: 7 },
  { label: 'August', value: 8 },
  { label: 'September', value: 9 },
  { label: 'October', value: 10 },
  { label: 'November', value: 11 },
  { label: 'December', value: 12 }
]

const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  return [currentYear - 1, currentYear, currentYear + 1].map(y => ({ label: y.toString(), value: y.toString() }))
})

const employeeOptions = computed(() =>
  employees.value.map(e => ({
    label: `${e.first_name} ${e.last_name}`,
    value: e.id
  }))
)

const filteredPeriods = computed(() =>
  periods.value.filter(p => p.period_year.toString() === filterYear.value)
)

const totalPaidThisMonth = computed(() => 0) // Calculate from data
const pendingPeriods = computed(() => periods.value.filter(p => !p.is_closed).length)
const employeeCount = computed(() => employees.value.length)

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'DRAFT': 'gray',
    'CALCULATED': 'yellow',
    'APPROVED': 'blue',
    'PAID': 'green',
    'CANCELLED': 'red'
  }
  return colors[status] || 'gray'
}

const getStatusBgColor = (status: string) => {
  const colors: Record<string, string> = {
    'DRAFT': 'bg-gray-100 dark:bg-gray-700',
    'CALCULATED': 'bg-yellow-100 dark:bg-yellow-900',
    'APPROVED': 'bg-blue-100 dark:bg-blue-900',
    'PAID': 'bg-green-100 dark:bg-green-900'
  }
  return colors[status] || 'bg-gray-100'
}

const getStatusTextColor = (status: string) => {
  const colors: Record<string, string> = {
    'DRAFT': 'text-gray-600',
    'CALCULATED': 'text-yellow-600',
    'APPROVED': 'text-blue-600',
    'PAID': 'text-green-600'
  }
  return colors[status] || 'text-gray-600'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(amount || 0)
}

const fetchPeriods = async () => {
  loading.value = true
  try {
    const res = await $api.get('/hr/payroll/periods')
    periods.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchEmployees = async () => {
  try {
    const res = await $api.get('/hr/employees')
    employees.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchPayslips = async () => {
  if (!selectedEmployeeForSlip.value) return
  try {
    const res = await $api.get(`/hr/payslips/${selectedEmployeeForSlip.value}`)
    payslips.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const createPeriod = async () => {
  saving.value = true
  try {
    await $api.post('/hr/payroll/periods', periodForm.value)
    showPeriodModal.value = false
    periodForm.value = {
      name: '', period_month: new Date().getMonth() + 1,
      period_year: new Date().getFullYear(),
      start_date: '', end_date: '', payment_date: ''
    }
    toast.add({ title: 'Success', description: 'Payroll period created' })
    await fetchPeriods()
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

const runPayroll = async (period: any) => {
  runningPayroll.value = period.id
  try {
    const res = await $api.post(`/hr/payroll/run/${period.id}`)
    selectedPayrollRun.value = res.data
    toast.add({ title: 'Success', description: 'Payroll calculated successfully' })
    await fetchPeriods()
    viewPeriod(period)
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Payroll run failed', color: 'red' })
  } finally {
    runningPayroll.value = null
  }
}

const viewPeriod = async (period: any) => {
  selectedPeriod.value = period
  showPeriodDetail.value = true
  
  // Fetch payroll run and payslips for this period
  loadingPayslips.value = true
  try {
    // For now, just show the modal with available data
    periodPayslips.value = []
  } catch (e) {
    console.error(e)
  } finally {
    loadingPayslips.value = false
  }
}

const viewPayslip = (slip: any) => {
  selectedPayslip.value = slip
  showPayslipDetail.value = true
}

onMounted(() => {
  fetchPeriods()
  fetchEmployees()
})
</script>
