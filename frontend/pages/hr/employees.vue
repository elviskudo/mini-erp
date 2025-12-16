<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Employees</h2>
        <p class="text-gray-500">Manage employee records</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Employee</UButton>
    </div>

    <UCard :ui="{ body: { padding: '' } }">
       <UTable :columns="columns" :rows="employees" :loading="loading">
            <template #status-data="{ row }">
                <UBadge :color="row.status === 'Active' ? 'green' : 'red'" variant="subtle">{{ row.status }}</UBadge>
            </template>
            <template #actions-data="{ row }">
              <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            </template>
       </UTable>
    </UCard>

    <!-- Employee Form Slideover -->
    <FormSlideover 
      v-model="isOpen" 
      :title="editMode ? 'Edit Employee' : 'Add Employee'"
      :loading="saving"
      @submit="onSubmit"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="First Name" required>
            <UInput v-model="form.first_name" />
          </UFormGroup>
          <UFormGroup label="Last Name" required>
            <UInput v-model="form.last_name" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Email" required>
          <UInput v-model="form.email" type="email" />
        </UFormGroup>
        
        <UFormGroup label="Phone">
          <UInput v-model="form.phone" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Department">
            <UInput v-model="form.department" />
          </UFormGroup>
          <UFormGroup label="Job Title">
            <UInput v-model="form.job_title" />
          </UFormGroup>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Base Salary">
            <UInput v-model="form.base_salary" type="number" />
          </UFormGroup>
          <UFormGroup label="Hire Date">
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
