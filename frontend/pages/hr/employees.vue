<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Employees</h2>
        <p class="text-gray-500">Manage employee records</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Employee</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-4' } }">
       <DataTable :columns="columns" :rows="employees" :loading="loading" search-placeholder="Search employees...">
            <template #status-data="{ row }">
                <UBadge :color="row.status === 'Active' ? 'green' : 'red'" variant="subtle">{{ row.status }}</UBadge>
            </template>
            <template #actions-data="{ row }">
              <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            </template>
       </DataTable>
    </UCard>

    <!-- Employee Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Employee' : 'Add Employee'"
      :loading="saving"
      :disabled="!isFormValid"
      @submit="onSubmit"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="First Name" required hint="Legal first name" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.first_name" placeholder="e.g. John" />
          </UFormGroup>
          <UFormGroup label="Last Name" required hint="Legal last name" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.last_name" placeholder="e.g. Smith" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Email" required hint="Work email address" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.email" type="email" placeholder="e.g. john@company.com" />
        </UFormGroup>
        
        <UFormGroup label="Phone" required hint="Contact phone number" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.phone" placeholder="e.g. +62 812 3456 7890" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Department" required hint="Assigned department" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.department" placeholder="e.g. IT" />
          </UFormGroup>
          <UFormGroup label="Job Title" required hint="Official position" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.job_title" placeholder="e.g. Developer" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Base Salary" required hint="Monthly salary (IDR)" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.base_salary" type="number" />
          </UFormGroup>
          <UFormGroup label="Hire Date" required hint="Employment start date" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.hire_date" type="date" />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const toast = useToast()
const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const editMode = ref(false)
const employees = ref<any[]>([])

const form = reactive({
    id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    job_title: '',
    base_salary: 5000000,
    hire_date: new Date().toISOString().split('T')[0]
})

// Form validation - button enabled only when all required fields are filled
const isFormValid = computed(() => {
    return form.first_name.trim() !== '' && 
           form.last_name.trim() !== '' && 
           form.email.trim() !== '' &&
           form.phone.trim() !== '' &&
           form.department.trim() !== '' &&
           form.job_title.trim() !== '' &&
           form.base_salary > 0 &&
           form.hire_date !== ''
})

const columns = [
  { key: 'first_name', label: 'First Name' },
  { key: 'last_name', label: 'Last Name' },
  { key: 'job_title', label: 'Title' },
  { key: 'department', label: 'Dept' },
  { key: 'base_salary', label: 'Salary' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const fetchEmployees = async () => {
    loading.value = true
    try {
        const res: any = await $fetch('/api/hr/employees')
        employees.value = res
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const resetForm = () => {
    Object.assign(form, {
        id: '',
        first_name: '', 
        last_name: '', 
        email: '', 
        phone: '',
        department: '', 
        job_title: '', 
        base_salary: 5000000,
        hire_date: new Date().toISOString().split('T')[0]
    })
}

const openCreate = () => {
    resetForm()
    editMode.value = false
    isOpen.value = true
}

const openEdit = (row: any) => {
    Object.assign(form, row)
    editMode.value = true
    isOpen.value = true
}

const onSubmit = async () => {
    saving.value = true
    try {
        if (editMode.value) {
            await $fetch(`/api/hr/employees/${form.id}`, {
                method: 'PUT',
                body: form
            })
            toast.add({ title: 'Success', description: 'Employee updated.' })
        } else {
            await $fetch('/api/hr/employees', {
                method: 'POST',
                body: form
            })
            toast.add({ title: 'Success', description: 'Employee created.' })
        }
        isOpen.value = false
        fetchEmployees()
        resetForm()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to save employee.', color: 'red' })
    } finally {
        saving.value = false
    }
}

onMounted(() => {
    fetchEmployees()
})
</script>
