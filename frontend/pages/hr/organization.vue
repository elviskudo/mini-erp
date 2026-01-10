<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Organization Structure</h2>
        <p class="text-gray-500 text-sm">Manage departments and positions</p>
      </div>
      <NuxtLink to="/hr">
        <UButton variant="ghost" icon="i-heroicons-arrow-left">Back to Dashboard</UButton>
      </NuxtLink>
    </div>

    <!-- Tabs -->
    <UTabs v-model="activeTab" :items="tabItems" />

    <!-- Departments Tab Content -->
    <div v-show="activeTab === 0">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Departments</h3>
            <UButton icon="i-heroicons-plus" size="sm" @click="openDepartmentForm()">
              Add Department
            </UButton>
          </div>
        </template>
        <UTable :rows="departments" :columns="departmentColumns" :loading="loading">
          <template #manager_name-data="{ row }">
            {{ getManagerName(row.manager_id) || '-' }}
          </template>
          <template #employee_count-data="{ row }">
            <UBadge variant="soft" color="primary">{{ row.employee_count || 0 }}</UBadge>
          </template>
          <template #actions-data="{ row }">
            <div class="flex gap-1">
              <UButton icon="i-heroicons-pencil" variant="ghost" size="xs" @click="openDepartmentForm(row)" />
              <UButton icon="i-heroicons-trash" variant="ghost" size="xs" color="red" @click="confirmDeleteDepartment(row)" />
            </div>
          </template>
        </UTable>
      </UCard>
    </div>

    <!-- Positions Tab Content -->
    <div v-show="activeTab === 1">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Positions</h3>
            <UButton icon="i-heroicons-plus" size="sm" @click="openPositionForm()">
              Add Position
            </UButton>
          </div>
        </template>
        <div class="mb-4">
          <USelect 
            v-model="filterDepartmentId" 
            :options="departmentFilterOptions" 
            placeholder="Filter by Department"
            class="w-64"
          />
        </div>
        <UTable :rows="filteredPositions" :columns="positionColumns" :loading="loading">
          <template #department_name-data="{ row }">
            {{ getDepartmentName(row.department_id) }}
          </template>
          <template #level-data="{ row }">
            <UBadge variant="soft" :color="getLevelColor(row.level)">Level {{ row.level }}</UBadge>
          </template>
          <template #base_salary-data="{ row }">
            {{ formatCurrency(row.base_salary) }}
          </template>
          <template #actions-data="{ row }">
            <div class="flex gap-1">
              <UButton icon="i-heroicons-pencil" variant="ghost" size="xs" @click="openPositionForm(row)" />
              <UButton icon="i-heroicons-trash" variant="ghost" size="xs" color="red" @click="confirmDeletePosition(row)" />
            </div>
          </template>
        </UTable>
      </UCard>
    </div>

    <!-- Department Form Slideover -->
    <FormSlideover
      v-model="showDepartmentForm"
      :title="editingDepartment ? 'Edit Department' : 'Add New Department'"
      :loading="saving"
      @submit="saveDepartment"
    >
      <div class="space-y-4">
        <UFormGroup label="Department Name" required :error="deptFormSubmitted && !departmentForm.name ? 'Required' : ''">
          <UInput v-model="departmentForm.name" placeholder="e.g. Engineering" />
        </UFormGroup>
        <UFormGroup label="Code" required :error="deptFormSubmitted && !departmentForm.code ? 'Required' : ''">
          <UInput v-model="departmentForm.code" placeholder="e.g. ENG" />
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="departmentForm.description" placeholder="Department description" rows="3" />
        </UFormGroup>
        <UFormGroup label="Manager" required :error="deptFormSubmitted && !departmentForm.manager_id ? 'Required' : ''">
          <USelect 
            v-model="departmentForm.manager_id" 
            :options="managerOptions" 
            placeholder="Select Manager"
            option-attribute="label"
            value-attribute="value"
          />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Position Form Slideover -->
    <FormSlideover
      v-model="showPositionForm"
      :title="editingPosition ? 'Edit Position' : 'Add New Position'"
      :loading="saving"
      @submit="savePosition"
    >
      <div class="space-y-4">
        <UFormGroup label="Position Name" required :error="posFormSubmitted && !positionForm.name ? 'Required' : ''">
          <UInput v-model="positionForm.name" placeholder="e.g. Senior Developer" />
        </UFormGroup>
        <UFormGroup label="Code" required :error="posFormSubmitted && !positionForm.code ? 'Required' : ''">
          <UInput v-model="positionForm.code" placeholder="e.g. SR-DEV" />
        </UFormGroup>
        <UFormGroup label="Department" required :error="posFormSubmitted && !positionForm.department_id ? 'Required' : ''">
          <USelect 
            v-model="positionForm.department_id" 
            :options="departmentSelectOptions" 
            placeholder="Select Department"
            option-attribute="label"
            value-attribute="value"
          />
        </UFormGroup>
        <UFormGroup label="Level" required :error="posFormSubmitted && !positionForm.level ? 'Required' : ''">
          <UInput v-model.number="positionForm.level" type="number" min="1" max="10" placeholder="1-10" />
        </UFormGroup>
        <UFormGroup label="Base Salary (IDR)" required :error="posFormSubmitted && !positionForm.base_salary ? 'Required' : ''">
          <UInput 
            :model-value="formatSalaryInput(positionForm.base_salary)" 
            @update:model-value="positionForm.base_salary = parseSalaryInput($event)"
            placeholder="e.g. 10,000,000"
          >
            <template #leading>
              <span class="text-gray-500 text-sm">Rp</span>
            </template>
          </UInput>
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="positionForm.description" placeholder="Position description and responsibilities" rows="3" />
        </UFormGroup>
      </div>
    </FormSlideover>

    <!-- Delete Confirmation Modal -->
    <UModal v-model="showDeleteModal">
      <UCard>
        <template #header>
          <h3 class="font-semibold text-red-600">Confirm Delete</h3>
        </template>
        <p>Are you sure you want to delete <strong>{{ deleteTarget?.name }}</strong>?</p>
        <p class="text-sm text-gray-500 mt-2">This action cannot be undone.</p>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDeleteModal = false">Cancel</UButton>
            <UButton color="red" @click="executeDelete" :loading="saving">Delete</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({
  layout: 'default'
})

const activeTab = ref(0)
const loading = ref(false)
const saving = ref(false)

const departments = ref<any[]>([])
const positions = ref<any[]>([])
const managers = ref<any[]>([])

const showDepartmentForm = ref(false)
const showPositionForm = ref(false)
const showDeleteModal = ref(false)

const editingDepartment = ref<any>(null)
const editingPosition = ref<any>(null)
const deleteTarget = ref<any>(null)
const deleteType = ref<'department' | 'position'>('department')
const filterDepartmentId = ref('')

const deptFormSubmitted = ref(false)
const posFormSubmitted = ref(false)

const tabItems = [
  { label: 'Departments', icon: 'i-heroicons-building-office-2' },
  { label: 'Positions', icon: 'i-heroicons-briefcase' }
]

const departmentColumns = [
  { key: 'name', label: 'Name' },
  { key: 'code', label: 'Code' },
  { key: 'manager_name', label: 'Manager' },
  { key: 'employee_count', label: 'Employees' },
  { key: 'actions', label: '' }
]

const positionColumns = [
  { key: 'name', label: 'Name' },
  { key: 'code', label: 'Code' },
  { key: 'department_name', label: 'Department' },
  { key: 'level', label: 'Level' },
  { key: 'base_salary', label: 'Base Salary' },
  { key: 'actions', label: '' }
]

const departmentForm = ref({
  name: '',
  code: '',
  description: '',
  manager_id: '' as string
})

const positionForm = ref({
  name: '',
  code: '',
  department_id: '',
  level: 1,
  base_salary: 0,
  description: ''
})

const filteredPositions = computed(() => {
  if (!filterDepartmentId.value) return positions.value
  return positions.value.filter(p => p.department_id === filterDepartmentId.value)
})

const managerOptions = computed(() => 
  managers.value.map(m => ({ label: `${m.name} (${m.email})`, value: m.id }))
)

const departmentSelectOptions = computed(() => 
  departments.value.map(d => ({ label: d.name, value: d.id }))
)

const departmentFilterOptions = computed(() => [
  { label: 'All Departments', value: '' },
  ...departments.value.map(d => ({ label: d.name, value: d.id }))
])

const getDepartmentName = (deptId: string) => {
  const dept = departments.value.find(d => d.id === deptId)
  return dept?.name || '-'
}

const getManagerName = (managerId: string) => {
  const manager = managers.value.find(m => m.id === managerId)
  return manager?.name || null
}

const getLevelColor = (level: number) => {
  if (level <= 2) return 'green'
  if (level <= 4) return 'blue'
  if (level <= 6) return 'yellow'
  return 'gray'
}

const formatCurrency = (value: number) => {
  if (!value) return '-'
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value)
}

const formatSalaryInput = (value: number) => {
  if (!value) return ''
  return new Intl.NumberFormat('id-ID').format(value)
}

const parseSalaryInput = (value: string) => {
  const num = parseInt(value.replace(/\D/g, ''), 10)
  return isNaN(num) ? 0 : num
}

const fetchData = async () => {
  loading.value = true
  try {
    const [deptRes, posRes, mgrRes] = await Promise.all([
      $api.get('/hr/departments'),
      $api.get('/hr/positions'),
      $api.get('/hr/managers')
    ])
    departments.value = deptRes.data
    positions.value = posRes.data
    managers.value = mgrRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openDepartmentForm = (dept?: any) => {
  deptFormSubmitted.value = false
  if (dept) {
    editingDepartment.value = dept
    departmentForm.value = {
      name: dept.name,
      code: dept.code,
      description: dept.description || '',
      manager_id: dept.manager_id || ''
    }
  } else {
    editingDepartment.value = null
    departmentForm.value = { name: '', code: '', description: '', manager_id: '' }
  }
  showDepartmentForm.value = true
}

const openPositionForm = (pos?: any) => {
  posFormSubmitted.value = false
  if (pos) {
    editingPosition.value = pos
    positionForm.value = {
      name: pos.name,
      code: pos.code,
      department_id: pos.department_id,
      level: pos.level,
      base_salary: pos.base_salary || 0,
      description: pos.description || ''
    }
  } else {
    editingPosition.value = null
    positionForm.value = { name: '', code: '', department_id: '', level: 1, base_salary: 0, description: '' }
  }
  showPositionForm.value = true
}

const saveDepartment = async () => {
  deptFormSubmitted.value = true
  if (!departmentForm.value.name || !departmentForm.value.code || !departmentForm.value.manager_id) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  saving.value = true
  try {
    if (editingDepartment.value) {
      await $api.put(`/hr/departments/${editingDepartment.value.id}`, departmentForm.value)
      toast.add({ title: 'Department updated successfully', color: 'green' })
    } else {
      await $api.post('/hr/departments', departmentForm.value)
      toast.add({ title: 'Department created successfully', color: 'green' })
    }
    showDepartmentForm.value = false
    await fetchData()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Error saving department', color: 'red' })
  } finally {
    saving.value = false
  }
}

const savePosition = async () => {
  posFormSubmitted.value = true
  if (!positionForm.value.name || !positionForm.value.code || !positionForm.value.department_id || !positionForm.value.base_salary) {
    toast.add({ title: 'Please fill all required fields', color: 'red' })
    return
  }
  saving.value = true
  try {
    if (editingPosition.value) {
      await $api.put(`/hr/positions/${editingPosition.value.id}`, positionForm.value)
      toast.add({ title: 'Position updated successfully', color: 'green' })
    } else {
      await $api.post('/hr/positions', positionForm.value)
      toast.add({ title: 'Position created successfully', color: 'green' })
    }
    showPositionForm.value = false
    await fetchData()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Error saving position', color: 'red' })
  } finally {
    saving.value = false
  }
}

const confirmDeleteDepartment = (dept: any) => {
  deleteTarget.value = dept
  deleteType.value = 'department'
  showDeleteModal.value = true
}

const confirmDeletePosition = (pos: any) => {
  deleteTarget.value = pos
  deleteType.value = 'position'
  showDeleteModal.value = true
}

const executeDelete = async () => {
  saving.value = true
  try {
    const endpoint = deleteType.value === 'department' 
      ? `/hr/departments/${deleteTarget.value.id}`
      : `/hr/positions/${deleteTarget.value.id}`
    await $api.delete(endpoint)
    toast.add({ title: `${deleteType.value === 'department' ? 'Department' : 'Position'} deleted successfully`, color: 'green' })
    showDeleteModal.value = false
    await fetchData()
  } catch (e: any) {
    toast.add({ title: e.response?.data?.detail || 'Cannot delete - may have associated employees', color: 'red' })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
